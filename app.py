from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload_route():
    data = request.json
    required = ["file_name", "frameio_token", "account_id", "folder_id"]

    # Shared required fields
    if not all(field in data for field in required):
        return jsonify({"error": "❌ Missing required fields"}), 400

    try:
        upload_type = data.get("upload_type", "local")  # default to local
        if upload_type == "remote":
            return jsonify(handle_remote_upload(data))
        else:
            if not all(x in data for x in ["download_url", "file_size"]):
                return jsonify({"error": "❌ Missing download_url or file_size for local upload"}), 400
            return jsonify(handle_local_upload(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def handle_local_upload(data):
    # Step 1: Download file
    local_path = f"/tmp/{data['file_name']}"
    with requests.get(data["download_url"], stream=True) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # Step 2: Init local upload
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

    init_response = requests.post(init_url, json=payload, headers=headers)
    init_response.raise_for_status()
    upload_info = init_response.json()["data"]
    upload_urls = upload_info["upload_urls"]

    # Step 3: Upload chunks
    with open(local_path, 'rb') as f:
        for i, part in enumerate(upload_urls):
            res = requests.put(part["url"], data=f.read(part["size"]))
            res.raise_for_status()
            print(f"✅ Uploaded chunk {i+1}/{len(upload_urls)}")

    return {
        "status": "✅ Local upload complete",
        "asset_id": upload_info["id"],
        "view_url": upload_info["view_url"]
    }


def handle_remote_upload(data):
    url = f"https://api.frame.io/v4/accounts/{data['account_id']}/folders/{data['folder_id']}/files/remote_upload"
    headers = {
        "Authorization": f"Bearer {data['frameio_token']}",
        "Content-Type": "application/json"
    }
    payload = {
        "data": {
            "name": data["file_name"],
            "source_url": data["download_url"]  # reuse same key
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()["data"]

    return {
        "status": "✅ Remote upload initiated",
        "asset_id": result["id"],
        "view_url": result.get("view_url")
    }

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
