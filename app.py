from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Media Transfer Service is running"

@app.route("/upload", methods=["POST"])
def upload_handler():
    data = request.json

    required_fields = [
        "download_url", "file_name", "file_size",
        "frameio_token", "account_id", "folder_id"
    ]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "❌ Missing required fields"}), 400

    try:
        download_url = data["download_url"]
        file_name = data["file_name"]
        file_size = int(data["file_size"])
        token = data["frameio_token"]
        account_id = data["account_id"]
        folder_id = data["folder_id"]

        # Step 1: Init upload with Frame.io
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "data": {
                "file_size": file_size,
                "name": file_name
            }
        }

        res = requests.post(
            f"https://api.frame.io/v4/accounts/{account_id}/folders/{folder_id}/files/local_upload",
            json=payload, headers=headers
        )
        res.raise_for_status()
        upload_data = res.json().get("data", {})
        upload_urls = upload_data.get("upload_urls")
        asset_id = upload_data.get("id")
        view_url = upload_data.get("view_url")

        if not upload_urls:
            return jsonify({"error": "❌ No upload URLs returned", "frameio_response": res.json()}), 500

        # Step 2: Download file to /tmp first
        local_path = f"/tmp/{file_name}"
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Step 3: Upload in chunks from file
        with open(local_path, 'rb') as f:
            for i, part in enumerate(upload_urls):
                chunk_url = part["url"]
                chunk_size = part["size"]
                chunk_data = f.read(chunk_size)
                if not chunk_data:
                    break

                put_headers = {"Content-Type": "application/octet-stream"}
                put_res = requests.put(chunk_url, data=chunk_data, headers=put_headers)
                put_res.raise_for_status()
                print(f"✅ Uploaded chunk {i + 1}")

        os.remove(local_path)  # Clean up

        return jsonify({
            "message": "✅ File uploaded successfully",
            "frameio_asset_id": asset_id,
            "view_url": view_url
        }), 200

    except Exception as e:
        return jsonify({"error": f"❌ Upload failed: {str(e)}"}), 500
