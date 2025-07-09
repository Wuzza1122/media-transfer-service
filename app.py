from flask import Flask, request, jsonify
import requests
import os
import uuid
import tempfile
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRAMEIO_API_URL = os.getenv("FRAMEIO_API_URL", "https://api.frame.io/v4")

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
        download_url = data["download_url"]
        file_name = f"{uuid.uuid4()}_{data['file_name']}"  # Sanitize file name
        file_size = int(data["file_size"])
        if file_size <= 0:
            return jsonify({"error": "❌ Invalid file size"}), 400
        token = data["frameio_token"]
        account_id = data["account_id"]
        folder_id = data["folder_id"]

        logger.info(f"Starting upload for {file_name}, size: {file_size}")

        # Step 1: Init upload with Frame.io
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"data": {"file_size": file_size, "name": data["file_name"]}}
        res = requests.post(
            f"{FRAMEIO_API_URL}/accounts/{account_id}/folders/{folder_id}/files/local_upload",
            json=payload, headers=headers
        )
        res.raise_for_status()
        upload_data = res.json().get("data", {})
        if not upload_data:
            return jsonify({"error": "❌ Invalid Frame.io response", "frameio_response": res.json()}), 500

        upload_urls = upload_data.get("upload_urls")
        asset_id = upload_data.get("id")
        view_url = upload_data.get("view_url")
        if not upload_urls:
            return jsonify({"error": "❌ No upload URLs returned", "frameio_response": res.json()}), 500

        # Step 2: Download file to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_name) as temp_file:
            local_path = temp_file.name
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    temp_file.write(chunk)

        try:
            # Step 3: Upload in chunks
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
                    logger.info(f"✅ Uploaded chunk {i + 1}")

            return jsonify({
                "message": "✅ File uploaded successfully",
                "frameio_asset_id": asset_id,
                "view_url": view_url,
                "file_name": data["file_name"],
                "file_size": file_size
            }), 200

        finally:
            if os.path.exists(local_path):
                os.remove(local_path)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"❌ HTTP request failed: {str(e)}"}), 500
    except OSError as e:
        return jsonify({"error": f"❌ File operation failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"❌ Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
