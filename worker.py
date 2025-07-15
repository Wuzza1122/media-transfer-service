def upload_to_youtube(data):
    try:
        print("📥 Received job data:", data)

        download_url = data["download_url"]
        file_name = data["file_name"]
        file_size = data["file_size"]

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        client_id = data["client_id"]
        client_secret = data["client_secret"]

        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )

        youtube = build("youtube", "v3", credentials=creds)

        # Step 1: Download the file
        print("⬇️ Downloading file...")
        tmp_dir = tempfile.mkdtemp()
        local_path = os.path.join(tmp_dir, file_name)

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"✅ File downloaded to {local_path}")

        # Step 2: Upload to YouTube
        print("🚀 Uploading to YouTube...")
        media = MediaFileUpload(local_path, chunksize=-1, resumable=True, mimetype="video/*")
        request_upload = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": file_name,
                    "description": "Uploaded via API",
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
                print(f"🔁 Upload progress: {int(status.progress() * 100)}%")

        print(f"✅ Upload complete! Video ID: {response['id']}")
        return {"video_id": response["id"], "message": "✅ Uploaded to YouTube"}

    except Exception as e:
        print("❌ Error during YouTube upload:", str(e))
        return {"error": str(e)}
