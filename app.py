from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload_route():
    data = request.json
    required = ["download_url", "file_name", "file_size", "frameio_token", "account_id", "folder_id"]

    if not all(field in data for field in required):
        return jsonify({"error": "❌ Missing required fields"}), 400

    try:
        return jsonify(handle_local_upload(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def handle_local_upload(data):
    # Step 1: Download file from Backblaze
    local_path = f"/tmp/{data['file_name']}"
    print(f"⬇️ Downloading file from {data['download_url']}...")
    with requests.get(data["download_url"], stream=True) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # Step 2: Init local upload with Frame.io
    init_url = f"https://api.frame.io/v4/accounts/{data['account_id']}/folders/{data['folder_id']}/files/local_upload"
    headers = {
        "Authorization": f"Bearer {data['frameio_token']}",
        "Content-Type": "application/json"
    }
    payload = {
        "data": {
            "name": data["file_name"],
            "file_size": data["file_size"]
        }
    }

    print("🚀 Requesting upload URLs from Frame.io...")
    init_response = requests.post(init_url, json=payload, headers=headers)
    init_response.raise_for_status()
    upload_info = init_response.json()["data"]
    upload_urls = upload_info["upload_urls"]

    # Step 3: Upload each chunk (EXACT size match)
    print(f"📤 Uploading {len(upload_urls)} part(s)...")
    with open(local_path, 'rb') as f:
        for i, part in enumerate(upload_urls):
            chunk_size = part["size"]
            chunk_data = f.read(chunk_size)

            if len(chunk_data) != chunk_size:
                raise Exception(f"❌ Chunk size mismatch at part {i+1}: expected {chunk_size}, got {len(chunk_data)}")

            res = requests.put(part["url"], data=chunk_data)
            if res.status_code != 200:
                raise Exception(f"❌ Upload failed for part {i+1}: {res.status_code} - {res.text}")

            print(f"✅ Uploaded part {i+1}/{len(upload_urls)}")

    print("🎉 Upload complete!")
    return {
        "status": "✅ Upload complete",
        "asset_id": upload_info["id"],
        "view_url": upload_info.get("view_url")
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
