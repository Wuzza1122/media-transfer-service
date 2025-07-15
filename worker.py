import os
import requests
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from rq import Worker, Queue, Connection
import redis

# ✅ Upload to YouTube
def upload_to_youtube(data):
    try:
        print("📥 YouTube job data:", data)

        download_url = data["download_url"]
        file_name = data["file_name"]
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        client_id = data["client_id"]
        client_secret = data["client_secret"]

        # Download file
        tmp_dir = tempfile.mkdtemp()
        local_path = os.path.join(tmp_dir, file_name)

        print("⬇️ Downloading file from Backblaze...")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"✅ File downloaded to {local_path}")

        # Prepare YouTube API client
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )
        youtube = build("youtube", "v3", credentials=creds)

        # Upload
        media = MediaFileUpload(local_path, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": file_name,
                    "description": "Uploaded via automated job",
                    "tags": ["automated", "upload"],
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": "unlisted",
                },
            },
            media_body=media,
        )

        print("🚀 Starting YouTube upload...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"📤 Upload progress: {int(status.progress() * 100)}%")

        print(f"✅ Upload complete: {response}")
        return {"youtube_video_id": response["id"]}

    except Exception as e:
        print("❌ Error uploading to YouTube:", str(e))
        return {"error": str(e)}

# ✅ Upload to Frame.io
def upload_to_frameio(data):
    try:
        print("📥 Frame.io job data:", data)

        download_url = data["download_url"]
        file_name = data["file_name"]
        access_token = data["access_token"]
        account_id = data["account_id"]
        folder_id = data["folder_id"]

        # Download file
        tmp_dir = tempfile.mkdtemp()
        local_path = os.path.join(tmp_dir, file_name)

        print("⬇️ Downloading file from Backblaze...")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"✅ File downloaded to {local_path}")

        # Init Frame.io upload
        print("🚀 Initiating upload to Frame.io...")
        init_upload = requests.post(
            f"https://api.frame.io/v4/accounts/{account_id}/folders/{folder_id}/files/local_upload",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"file_name": file_name, "file_size": os.path.getsize(local_path)}
        )
        init_upload.raise_for_status()
        upload_info = init_upload.json()
        upload_urls = upload_info["upload_urls"]
        asset_id = upload_info["id"]

        print(f"📤 Uploading {len(upload_urls)} parts to Frame.io...")

        with open(local_path, "rb") as f:
            for idx, url in enumerate(upload_urls):
                chunk = f.read(5 * 1024 * 1024)
                res = requests.put(url, data=chunk)
                res.raise_for_status()
                print(f"✅ Uploaded chunk {idx + 1}/{len(upload_urls)}")

        view_url = f"https://app.frame.io/review/{asset_id}"
        print(f"✅ Upload complete. View: {view_url}")

        return {
            "file_name": file_name,
            "frameio_asset_id": asset_id,
            "frameio_view_url": view_url,
            "message": "✅ Video uploaded to Frame.io"
        }

    except Exception as e:
        print("❌ Error uploading to Frame.io:", str(e))
        return {"error": str(e)}

# ✅ Redis worker setup
if __name__ == "__main__":
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    conn = redis.from_url(redis_url)

    with Connection(conn):
        worker = Worker(["default"])
        worker.work(with_scheduler=True)
