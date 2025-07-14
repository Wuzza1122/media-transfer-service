import os
import requests
import google.auth.transport.requests
from google.oauth2.credentials import Credentials

def upload_to_youtube(file_name, download_url, file_size, access_token, refresh_token, client_id, client_secret):
    print("🚀 [youtube_upload.py] Starting upload job")
    print(f"🧾 File Name: {file_name}")
    print(f"📦 File Size: {file_size}")
    print(f"🌐 Download URL: {download_url}")

    try:
        # Step 1: Download the video
        print("⬇️ Downloading video file...")
        local_path = f"/tmp/{file_name}"
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("✅ Download complete")

        # Step 2: Refresh access token
        print("🔄 Refreshing token...")
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )
        creds.refresh(google.auth.transport.requests.Request())
        print("✅ Token refreshed")

        # Step 3: Start YouTube upload
        print("📤 Initializing YouTube upload session...")
        metadata = {
            "snippet": {
                "title": file_name,
                "description": "Auto uploaded via media-transfer-service",
                "tags": ["media", "auto-upload"],
                "categoryId": "22",
            },
            "status": {"privacyStatus": "unlisted"},
        }

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json"
        }

        init_res = requests.post(
            "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
            headers=headers,
            json=metadata
        )
        init_res.raise_for_status()
        upload_url = init_res.headers["Location"]
        print(f"✅ Upload session started: {upload_url}")

        # Step 4: Upload video
        print("⬆️ Uploading video file to YouTube...")
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
        print("✅ Upload to YouTube complete!")

    except Exception as e:
        print("❌ Upload to YouTube failed:", str(e))
