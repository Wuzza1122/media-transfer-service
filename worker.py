from redis import Redis
from rq import Queue
import os
import requests
import google.auth.transport.requests
from google.oauth2.credentials import Credentials

# ✅ Setup Redis
redis_url = os.getenv("REDIS_URL")
redis_conn = Redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

# ✅ Worker function — no decorator needed
def upload_to_youtube(file_name, download_url, file_size, access_token, refresh_token, client_id, client_secret):
    try:
        print(f"⬇️ Downloading file: {file_name}")
        local_path = f"/tmp/{file_name}"

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print("🔄 Refreshing YouTube access token...")
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )
        creds.refresh(google.auth.transport.requests.Request())

        print("📤 Uploading to YouTube...")
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json"
        }

        metadata = {
            "snippet": {
                "title": file_name,
                "description": "Uploaded via media-transfer-service",
                "tags": ["auto-upload"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "unlisted"
            }
        }

        init_res = requests.post(
            "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
            headers=headers,
            json=metadata
        )
        init_res.raise_for_status()
        upload_url = init_res.headers["Location"]

        with open(local_path, "rb") as f:
            upload_res = requests.put(
                upload_url,
                data=f,
                headers={
                    "Authorization": f"Bearer {creds.token}",
                    "Content-Type": "video/*",
                    "Content-Length": str(file_size)
                }
            )
            upload_res.raise_for_status()

        print("✅ YouTube upload complete!")

    except Exception as e:
        print("❌ YouTube upload failed:", str(e))
