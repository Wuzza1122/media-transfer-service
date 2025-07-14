import os
import requests
from redis import Redis
from rq import Queue
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import tempfile

redis_url = os.getenv("REDIS_URL")
redis_token = os.getenv("REDIS_PASSWORD")

redis_conn = Redis.from_url(redis_url, password=redis_token)
queue = Queue(connection=redis_conn)

@queue.job
def upload_to_youtube(file_name, download_url, file_size, access_token, refresh_token, client_id, client_secret):
    print(f"📥 Downloading {file_name}...")
    temp_file_path = os.path.join(tempfile.gettempdir(), file_name)
    
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(temp_file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print("🔐 Setting up YouTube credentials...")
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token"
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    print("📡 Connecting to YouTube API...")
    youtube = build("youtube", "v3", credentials=creds)

    print("📤 Uploading to YouTube...")
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": file_name,
                "description": "Uploaded via Render media-transfer-service",
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "unlisted"
            }
        },
        media_body=MediaFileUpload(temp_file_path, chunksize=-1, resumable=True)
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"🚀 Upload progress: {int(status.progress() * 100)}%")

    print(f"✅ Upload complete! Video ID: {response['id']}")
    os.remove(temp_file_path)
