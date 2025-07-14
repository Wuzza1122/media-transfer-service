from flask import Flask, request, jsonify
from worker import upload_to_youtube, queue  # ✅ also import queue

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json()
    download_url = data.get("download_url")
    file_name = data.get("file_name")
    file_size = data.get("file_size")
    destinations = data.get("destinations", [])

    jobs = {}

    if "youtube" in destinations and "youtube" in data:
        youtube_data = data["youtube"]
        job = queue.enqueue(
            upload_to_youtube,
            file_name,
            download_url,
            file_size,
            youtube_data["access_token"],
            youtube_data["refresh_token"],
            youtube_data["client_id"],
            youtube_data["client_secret"]
        )
        jobs["youtube"] = job.id

    return jsonify({
        "file_name": file_name,
        "jobs": jobs,
        "status": "🎯 Jobs enqueued"
    })
