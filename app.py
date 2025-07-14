from flask import Flask, request, jsonify
from rq import Queue
from redis import Redis
import os
from youtube_upload import upload_to_youtube

app = Flask(__name__)

# 🔧 Redis Setup
redis_url = os.getenv("REDIS_URL")
redis_conn = Redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

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
            file_name=file_name,
            download_url=download_url,
            file_size=file_size,
            access_token=youtube_data["access_token"],
            refresh_token=youtube_data["refresh_token"],
            client_id=youtube_data["client_id"],
            client_secret=youtube_data["client_secret"]
        )
        jobs["youtube"] = job.id

    return jsonify({
        "file_name": file_name,
        "jobs": jobs,
        "status": "🎯 Jobs enqueued"
    })
