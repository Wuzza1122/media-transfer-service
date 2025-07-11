from flask import Flask, request, jsonify
import os
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ YouTube Upload Service is Running!"

@app.route("/upload_to_youtube", methods=["POST"])
def upload_to_youtube():
    try:
        data = request.json
        required_fields = [
            "download_url", "file_name", "file_size",
            "access_token", "refresh_token", "client_id", "client_secret"
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "❌ Missing required fields"}), 400

        # Step 1: Download file
        local_path = f"/tmp/{data['file_name']}"
        with requests.get(data["download_url"], stream=True) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Step 2: Setup credentials
        creds = Credentials(
            token=data["access_token"],
            refresh_token=data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )

        # Step 3: Upload to YouTube
        youtube = build("youtube", "v3", credentials=creds)
        media = MediaFileUpload(local_path, mimetype="video/mp4", resumable=True)

        request_upload = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": data["file_name"],
                    "description": "Uploaded via API",
                    "tags": ["API Upload"],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "unlisted"
                }
            },
            media_body=media
        )

        response = None
        while response is None:
            status, response = request_upload.next_chunk()
            if status:
                print(f"📤 Upload progress: {int(status.progress() * 100)}%")

        return jsonify({
            "message": "✅ Upload complete",
            "video_id": response["id"],
            "video_url": f"https://www.youtube.com/watch?v={response['id']}"
        })

    except Exception as e:
        return jsonify({"error": f"❌ {str(e)}"}), 500
