import os
import requests
from rq import Worker, Queue, Connection
from redis import Redis
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Redis connection
redis_conn = Redis()
queue = Queue(connection=redis_conn)

# ✅ Real YouTube upload function
def upload_to_youtube(job_data):
    file_name = job_data["file_name"]
    download_url = job_data["download_url"]
    file_path = f"/tmp/{file_name}"

    print(f"📥 Received job data: {job_data}")

    # Step 1: Download the file from Backblaze
    print("⬇️ Downloading file from Backblaze...")
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"✅ Downloaded {file_name} to {file_path}")

    # Step 2: Upload to YouTube
    youtube_creds = job_data.get("youtube")
    if youtube_creds:
        creds = Credentials(
            token=youtube_creds["access_token"],
            refresh_token=youtube_creds["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=youtube_creds["client_id"],
            client_secret=youtube_creds["client_secret"],
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )

        youtube = build("youtube", "v3", credentials=creds)

        media = MediaFileUpload(file_path, mimetype="video/*", resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": file_name,
                    "description": "Uploaded via media-transfer-service",
                    "categoryId": "22"  # People & Blogs
                },
                "status": {
                    "privacyStatus": "unlisted"
                }
            },
            media_body=media
        )

        print(f"🚀 Uploading {file_name} to YouTube...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"⬆️ Upload progress: {int(status.progress() * 100)}%")
        print(f"✅ YouTube upload complete. Video ID: {response.get('id')}")
    else:
        print("⚠️ No YouTube credentials found in job data.")

    # Cleanup
    os.remove(file_path)
    print(f"🧹 Cleaned up: {file_path}")


# Start listening for jobs
if __name__ == "__main__":
    print("*** Listening on default queue...")
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()
