@app.route("/upload_to_youtube", methods=["POST"])
def upload_to_youtube():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    data = request.json

    required_fields = ["download_url", "file_name", "file_size", "access_token", "refresh_token", "client_id", "client_secret"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "❌ Missing required fields"}), 400

    download_url = data["download_url"]
    file_name = data["file_name"]
    file_path = f"/tmp/{file_name}"

    # Download from Backblaze
    try:
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except Exception as e:
        return jsonify({"error": f"❌ Download failed: {str(e)}"}), 500

    # Upload to YouTube
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
            print(f"Uploaded {int(status.progress() * 100)}%") if status else None

        return jsonify({"message": "✅ Upload to YouTube successful", "videoId": response["id"]})

    except Exception as e:
        return jsonify({"error": f"❌ YouTube upload failed: {str(e)}"}), 500
