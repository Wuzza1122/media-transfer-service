from flask import Flask, request, jsonify
from worker import queue
from youtube_upload import upload_to_youtube

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    print("📥 Incoming upload request")

    data = request.get_json()
    print("📦 Payload received:", data)

    download_url = data.get("download_url")
    file_name = data.get("file_name")
    file_size = data.get("file_size")
    destinations = data.get("destinations", [])

    jobs = {}

    if "youtube" in destinations and "youtube" in data:
        print("🎯 YouTube upload requested")
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
        print("✅ Job enqueued with ID:", job.id)
        jobs["youtube"] = job.id
    else:
        print("⚠️ No valid destinations or missing YouTube data")

    return jsonify({
        "file_name": file_name,
        "jobs": jobs,
        "status": "🎯 Jobs enqueued"
    })
