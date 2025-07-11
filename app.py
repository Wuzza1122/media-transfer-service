from flask import Flask, request, jsonify
import requests
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

# 🔁 FRAME.IO UPLOAD (placeholder)
@app.route("/upload_to_frameio", methods=["POST"])
def upload_to_frameio():
    data = request.json
    return jsonify({
        "message": "✅ Frame.io upload endpoint is active",
        "file_name": data.get("file_name", "Unknown")
    })

# 📤 YOUTUBE UPLOAD
@app.route("/upload_to_youtube", methods=["POST"])
def upload_to_youtube():
    import traceback

    data = request.get_json(force=True)

    required_fields = [
        "download_url", "file_name", "file_size",
        "access_token", "refresh_token", "client_id", "client_secret"
    ]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "❌ Missing required fields"}), 400

    download_url = data["download_url"]
    file_name = data["file_name"]
    file_path = f"/tmp/{file_name}"

    # ⬇️ Step 1: Download from Backblaze
    try:
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"✅ Downloaded {file_name} to {file_path}")
    except Exception as e:
        print("❌ Download error:", traceback.format_exc())
        return jsonify({"error": f"❌ Download failed: {str(e)}"}), 500

    # 🚀 Step 2: Upload to YouTube
    try:
        creds = Credentials(
            token=data["access_token"],
            refresh_token=data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=data["client_id"],
            client_secret=data["client_secret"]
        )

        youtube = build("youtube", "v3", credentials=creds)

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")
        request_body = {
            "snippet": {
                "title": file_name,
                "description": "Uploaded via Render",
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "unlisted"
            }
        }

        request_upload = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request_upload.next_chunk()
            if status:
                print(f"📤 Uploaded {int(status.progress() * 100)}%")

        # 🧹 Clean up local file
        os.remove(file_path)

        # ✅ Build response
        video_id = response.get("id")
        return jsonify({
            "message": "✅ Upload to YouTube successful",
            "videoId": video_id,
            "file_name": file_name,
            "youtube_url": f"https://youtube.com/watch?v={video_id}" if video_id else None
        }), 200

    except Exception as e:
        print("❌ YouTube upload error:", traceback.format_exc())
        return jsonify({"error": f"❌ YouTube upload failed: {str(e)}"}), 500

# 🏁 Health check
@app.route("/", methods=["GET"])
def index():
    return "✅ Media Transfer Service is running!"
