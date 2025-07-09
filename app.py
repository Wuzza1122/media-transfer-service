from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Media Transfer Service is running"

@app.route("/upload", methods=["POST"])
def upload_handler():
    data = request.json

    required_fields = ["download_url", "file_name", "file_size", "frameio_token", "account_id", "folder_id"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "❌ Missing required fields"}), 400

    try:
        # Extract values
        download_url = data["download_url"]
        file_name = data["file_name"]
        file_size = int(data["file_size"])
        token = data["frameio_token"]
        account_id = data["account_id"]
        folder_id = data["folder_id"]

        # Step 1: Init upload with Frame.io
        init_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        init_payload = {
            "data": {
                "file_size": file_size,
                "name": file_name
            }
        }

        init_url = f"https://api.frame.io/v4/accounts/{account_id}/folders/{folder_id}/files/local_upload"
        init_res = requests.post(init_url, json=init_payload, headers=init_headers)
        init_res.raise_for_status()
        upload_info = init_res.json()

        print("📦 Frame.io response:", upload_info)

        # Extract nested "data" object
        upload_data = upload_info.get("data", {})
        upload_urls = upload_data.get("upload_urls")
        if not upload_urls:
            return jsonify({
                "error": "❌ Frame.io did not return upload URLs",
                "frameio_response": upload_info
            }), 500

        # Step 2: Download & upload in chunks
        chunk_size = 5 * 1024 * 1024  # 5MB
        res = requests.get(download_url, stream=True)
        chunk_index = 0

        for part in upload_urls:
            chunk_url = part["url"]
            chunk_data = res.raw.read(chunk_size)
            if not chunk_data:
                break
            put_res = requests.put(chunk_url, data=chunk_data)
            put_res.raise_for_status()
            print(f"✅ Uploaded chunk {chunk_index + 1}")
            chunk_index += 1

        return jsonify({
            "message": "✅ File uploaded successfully",
            "frameio_asset_id": upload_data.get("id"),
            "view_url": upload_data.get("view_url")
        }), 200

    except Exception as e:
        return jsonify({"error": f"❌ Upload failed: {str(e)}"}), 500
