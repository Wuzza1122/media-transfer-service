import requests
import os

# 🔧 Replace these with your actual values
FRAMEIO_TOKEN = "your_frameio_token_here"
ACCOUNT_ID = "your_account_id_here"
FOLDER_ID = "your_folder_id_here"
FILE_NAME = "Test.jpeg"
DOWNLOAD_URL = "https://f004.backblazeb2.com/file/video-uploads/Test.jpeg"
FILE_SIZE = 2097152  # Approx 2MB

# Step 1: Download file locally
local_path = f"/tmp/{FILE_NAME}"
print("⬇️ Downloading file...")
with requests.get(DOWNLOAD_URL, stream=True) as r:
    r.raise_for_status()
    with open(local_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

# Step 2: Init Frame.io Upload
print("🚀 Initializing upload with Frame.io...")
headers = {
    "Authorization": f"Bearer {FRAMEIO_TOKEN}",
    "Content-Type": "application/json"
}
payload = {
    "data": {
        "file_size": FILE_SIZE,
        "name": FILE_NAME
    }
}
init_url = f"https://api.frame.io/v4/accounts/{ACCOUNT_ID}/folders/{FOLDER_ID}/files/local_upload"
res = requests.post(init_url, json=payload, headers=headers)
res.raise_for_status()

upload_data = res.json()["data"]
upload_url = upload_data["upload_urls"][0]["url"]
asset_id = upload_data["id"]
view_url = upload_data["view_url"]

# Step 3: Upload file (no extra headers!)
print("⬆️ Uploading file to Frame.io...")
with open(local_path, 'rb') as f:
    chunk = f.read()
    put_res = requests.put(upload_url, data=chunk)
    put_res.raise_for_status()

# Done
print("✅ Upload complete!")
print(f"Frame.io Asset ID: {asset_id}")
print(f"View URL: {view_url}")
