import os
import requests
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from rq import Worker, Queue, Connection
import redis

# ✅ Upload function
def upload_to_youtube(data):
    try:
        print("📥 Received job data:", data)

        download_url = data["download_url"]
        file_name = data["file_name"]
        file_size = data["file_size"]

        print("⬇️ Downloading file from Backblaze...")
        tmp_dir = tempfile.mkdtemp()
        local_path = os.path.join(tmp_dir, file_name)

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"✅ File downloaded to {local_path}")

        creds = Credentials(
            token=data["access_token"],
            refresh_token=data["refresh_token"],
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            token_uri="https://oauth2.googleapis.com/token"
        )

        youtube = build("youtube", "v3", credentials=creds)

        media = MediaFileUpload(local_path, mimetype="video/mp4", resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": file_name,
                    "description": "Uploaded via automated job",
                    "tags": ["automated", "upload"],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "unlisted"
                }
            },
            media_body=media
        )

        print("🚀 Initiating YouTube upload...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"📤 Upload progress: {int(status.progress() * 100)}%")

        print("✅ Upload complete:", response)

        youtube_url = f"https://www.youtube.com/watch?v={response['id']}"
        return {
            "file_name": file_name,
            "youtube_video_id": response["id"],
            "youtube_url": youtube_url,
            "message": "✅ Video uploaded to YouTube"
        }

    except Exception as e:
        print("❌ Error uploading video:", str(e))
        return {"error": str(e)}

# ✅ Redis setup and worker start
if __name__ == "__main__":
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    conn = redis.from_url(redis_url)

    print("👷 Worker is starting and connected to Redis...")
    with Connection(conn):
        worker = Worker(["default"])
        worker.work(with_scheduler=True)
