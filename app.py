from flask import Flask, request, jsonify
import requests
import os
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

app = Flask(__name__)

@app.route("/upload_to_youtube", methods=["POST"])
def upload_to_youtube():
    try:
        data = request.json
        print("📥 Received data:", data)

        # Extract POSTed values
        download_url = data["download_url"]
        file_name = data["file_name"]
        file_size = data["file_size"]
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        client_id = data["client_id"]
        client_secret = data["client_secret"]

        # Step 1: Download the video file to a temp file
        print("⬇️ Downloading file from Backblaze...")
        temp_dir = tempfile.mkdtemp()
        local_path = os.path.join(temp_dir, file_name)

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"✅ File downloaded to {local_path}")

        # Step 2: Prepare YouTube credentials
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )

        # Step 3: Build YouTube client
        youtube = build("youtube", "v3", credentials=creds)

        # Step 4: Upload video
        body = {
            "snippet": {
                "title": file_name,
                "description": "Uploaded via API",
                "tags": ["automated", "upload"],
                "categoryId": "22"  # People & Blogs
            },
            "status": {
                "privacyStatus": "unlisted"
            }
        }

        media = MediaFileUpload(local_path, resumable=True, mimetype="video/mp4")

        print("🚀 Initiating YouTube upload...")
        request_upload = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request_upload.next_chunk()
            if status:
                print(f"📦 Upload progress: {int(status.progress() * 100)}%")

        print("🎉 Upload complete:", response["id"])

        return jsonify({
            "file_name": file_name,
            "youtube_video_id": response["id"],
            "youtube_url": f"https://www.youtube.com/watch?v={response['id']}",
            "message": "✅ Video uploaded to YouTube"
        })

    except Exception as e:
        print("❌ Error uploading video:", str(e))
        return jsonify({"error": str(e)}), 500
