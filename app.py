from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
import os
from worker import upload_to_youtube, upload_to_frameio

app = Flask(__name__)

# ✅ Use REDIS_URL from Render environment
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
        job = q.enqueue(upload_to_frameio, data)
        return jsonify({"message": "📤 Frame.io upload queued", "job_id": job.id}), 202

    else:
        return jsonify({"error": "❌ Invalid destination"}), 400
