import requests
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ========================
# 🎥 YouTube Upload
# ========================
def upload_to_youtube(data):
    try:
        file_url = data["download_url"]
        file_name = data["file_name"]
        access_token = data["youtube"]["access_token"]

        print(f"⬇️ Downloading file from: {file_url}")
        response = requests.get(file_url, stream=True)
        response.raise_for_status()

        temp_path = f"/tmp/{file_name}"
        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("📤 Uploading to YouTube...")

        creds = Credentials(token=access_token)
        youtube = build("youtube", "v3", credentials=creds)

        request_body = {
            "snippet": {
                "title": file_name,
                "description": "Uploaded via media-transfer-service",
                "tags": ["upload", "automated"],
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "unlisted"
            }
        }

        media = MediaFileUpload(temp_path, mimetype="video/mp4", resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"📶 Upload progress: {int(status.progress() * 100)}%")

        print(f"✅ YouTube upload complete: {response['id']}")

        # Optional: clean up
        os.remove(temp_path)

    except Exception as e:
        print("❌ YouTube upload failed:", str(e))


# ========================
# 🎞️ Frame.io Upload
# ========================
def upload_to_frameio(data):
    try:
        file_url = data["download_url"]
        file_name = data["file_name"]
        token = data["frameio"]["access_token"]
        account_id = data["frameio"]["account_id"]
        folder_id = data["frameio"]["folder_id"]

        print(f"⬆️ Uploading to Frame.io: {file_name}")

        # Step 1: Init upload session
        init_res = requests.post(
            f"https://api.frame.io/v4/accounts/{account_id}/assets",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "file", "name": file_name, "parent_id": folder_id}
        )
        init_res.raise_for_status()
        upload_info = init_res.json()
        upload_urls = upload_info["upload_urls"]
        asset_id = upload_info["id"]

        # Step 2: Download from source
        download = requests.get(file_url, stream=True)
        download.raise_for_status()

        # Step 3: Upload in chunks
        chunk_size = 5 * 1024 * 1024
        chunk_index = 0
        for url in upload_urls:
            chunk_data = download.raw.read(chunk_size)
            if not chunk_data:
                break
            res = requests.put(url, data=chunk_data)
            res.raise_for_status()
            print(f"✅ Uploaded chunk {chunk_index + 1}")
            chunk_index += 1

        print(f"✅ Frame.io upload complete: {file_name} (Asset ID: {asset_id})")

    except Exception as e:
        print("❌ Frame.io upload failed:", str(e))
