from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload_route():
    data = request.json
    required_fields = ["download_url", "file_name", "file_size", "frameio_token", "account_id", "folder_id"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "❌ Missing required fields"}), 400

    try:
        result = handle_upload(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def handle_upload(data):
    download_url = data["download_url"]
    file_name = data["file_name"]
    file_size = data["file_size"]
    token = data["frameio_token"]
    account_id = data["account_id"]
    folder_id = data["folder_id"]

    # Step 1: Download the file
    local_path = f"/tmp/{file_name}"
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # Step 2: Initialize upload with Frame.io
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "file_name": file_name,
        "file_size": file_size
    }
    init_url = f"https://api.frame.io/v4/accounts/{account_id}/folders/{folder_id}/files/local_upload"
    init_response = requests.post(init_url, json=payload, headers=headers)
    init_response.raise_for_status()
    upload_info = init_response.json()
    upload_urls = upload_info["upload_urls"]
    asset_id = upload_info["asset_id"]

    # Step 3: Upload in chunks
    with open(local_path, 'rb') as f:
        for i, url in enumerate(upload_urls):
            chunk_data = f.read(5 * 1024 * 1024)
            if not chunk_data:
                break
            res = requests.put(url, data=chunk_data)
            res.raise_for_status()
            print(f"✅ Uploaded chunk {i+1}/{len(upload_urls)}")

    return {
        "status": "✅ Upload complete",
        "asset_id": asset_id,
        "view_url": upload_info.get("view_url", None)
    }

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
