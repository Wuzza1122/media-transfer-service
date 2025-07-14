import os
import time
import requests
from redis import Redis
from rq import Worker, Queue, Connection

# ✅ YouTube uploader
def upload_to_youtube(data):
    try:
        print("📥 Received job data:", data)
        file_url = data["download_url"]
        file_name = data["file_name"]
        file_size = data["file_size"]

        print("⬇️ Downloading file from Backblaze...")
        response = requests.get(file_url, stream=True)
        response.raise_for_status()

        local_path = f"/tmp/{file_name}"
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Downloaded {file_name} to {local_path}")

        # 🔧 Placeholder logic for YouTube upload (replace with real API upload logic)
        print(f"🚀 Uploading {file_name} to YouTube (simulated)...")

        time.sleep(2)  # simulate upload time
        print(f"✅ Upload complete for YouTube: {file_name}")

    except Exception as e:
        print("❌ Error uploading video:", str(e))


# ✅ Frame.io uploader
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


# ✅ Start RQ worker
if __name__ == "__main__":
    print("🚀 Booting worker...")
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        conn = Redis.from_url(redis_url)
        with Connection(conn):
            worker = Worker(["default"])
            print("✅ Worker is now listening for jobs...")
            worker.work()
    except Exception as e:
        print("❌ Worker failed to start:", str(e))
