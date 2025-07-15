import requests
import tempfile
import os

def upload_to_frameio(data):
    try:
        print("📥 Received Frame.io job data:", data)

        # Required fields
        download_url = data["download_url"]
        file_name = data["file_name"]
        file_size = data["file_size"]
        frameio_token = data["frameio_token"]
        account_id = data["account_id"]
        folder_id = data["folder_id"]

        # Step 1: Download file
        print("⬇️ Downloading file...")
        tmp_dir = tempfile.mkdtemp()
        local_path = os.path.join(tmp_dir, file_name)

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"✅ File downloaded to {local_path}")

        # Step 2: Initialize upload
        print("🚀 Initializing Frame.io upload...")
        init_res = requests.post(
            f"https://api.frame.io/v4/assets/upload",
            headers={"Authorization": f"Bearer {frameio_token}"},
            json={
                "name": file_name,
                "type": "file",
                "parent_id": folder_id,
                "filesize": file_size
            }
        )
        init_res.raise_for_status()
        upload_info = init_res.json()

        upload_urls = upload_info.get("upload_urls")
        asset_id = upload_info.get("id")

        # Step 3: Upload file in chunks
        print("📤 Uploading to Frame.io...")
        chunk_size = 5 * 1024 * 1024  # 5MB
        with open(local_path, "rb") as f:
            for i, url in enumerate(upload_urls):
                chunk_data = f.read(chunk_size)
                if not chunk_data:
                    break
                res = requests.put(url, data=chunk_data)
                res.raise_for_status()
                print(f"✅ Uploaded chunk {i + 1}/{len(upload_urls)}")

        # Step 4: Finalize upload (optional, Frame.io may auto-complete)
        view_url = f"https://frame.io/player/{asset_id}"
        print(f"✅ Upload complete: {view_url}")

        return {
            "file_name": file_name,
            "frameio_asset_id": asset_id,
            "frameio_view_url": view_url,
            "message": "✅ Uploaded to Frame.io"
        }

    except Exception as e:
        print("❌ Frame.io upload failed:", str(e))
        return {"error": str(e)}
