from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload_route():
    data = request.json
    required = ["download_url", "file_name", "frameio_token", "account_id", "folder_id"]

    if not all(field in data for field in required):
        return jsonify({"error": "❌ Missing required fields"}), 400

    try:
        return jsonify(handle_remote_upload(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def handle_remote_upload(data):
    # Step 1: Remote upload to Frame.io
    url = f"https://api.frame.io/v4/accounts/{data['account_id']}/folders/{data['folder_id']}/files/remote_upload"
    headers = {
        "Authorization": f"Bearer {data['frameio_token']}",
        "Content-Type": "application/json"
    }
    payload = {
        "data": {
            "name": data["file_name"],
            "source_url": data["download_url"]
        }
    }

    print(f"🚀 Initiating remote upload for {data['file_name']}...")
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()["data"]

    print("✅ Remote upload request accepted by Frame.io")
    return {
        "status": "✅ Remote upload initiated",
        "asset_id": result["id"],
        "view_url": result.get("view_url")
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
