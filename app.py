from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
import requests
import os
from worker import upload_to_youtube

app = Flask(__name__)

# ✅ Redis setup
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_conn = Redis.from_url(redis_url)
q = Queue(connection=redis_conn)

@app.route("/")
def home():
    return "✅ Media Transfer Service is Live!"

@app.route("/upload", methods=["POST"])
def upload():
    data = request.json
    destination = data.get("destination")

    if destination == "youtube":
        job = q.enqueue(upload_to_youtube, data)
        return jsonify({"message": "🎬 YouTube upload queued", "job_id": job.id}), 202

    elif destination == "frameio":
        # 🔁 Instant remote upload to Frame.io
        try:
            access_token = data["access_token"]
            account_id = data["account_id"]
            folder_id = data["folder_id"]
            download_url = data["download_url"]
            file_name = data["file_name"]

            frameio_url = f"https://api.frame.io/v4/accounts/{account_id}/folders/{folder_id}/files/remote_upload"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "data": {
                    "name": file_name,
                    "source_url": download_url
                }
            }

            res = requests.post(frameio_url, headers=headers, json=payload)
            res.raise_for_status()

            return jsonify({
                "message": "✅ File sent to Frame.io remote_upload",
                "status_code": res.status_code,
                "frameio_response": res.json()
            }), 200

        except Exception as e:
            return jsonify({"error": f"❌ Error uploading to Frame.io: {str(e)}"}), 500

    else:
        return jsonify({"error": "❌ Invalid destination"}), 400
