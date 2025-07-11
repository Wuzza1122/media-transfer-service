from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
from worker import upload_to_youtube

import os

app = Flask(__name__)

# Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = Redis.from_url(redis_url)
q = Queue(connection=redis_conn)

@app.route("/upload_to_youtube", methods=["POST"])
def enqueue_youtube_upload():
    data = request.json

    required_keys = [
        "download_url", "file_name", "file_size",
        "access_token", "refresh_token", "client_id", "client_secret"
    ]
    if not all(key in data for key in required_keys):
        return jsonify({"error": "❌ Missing required fields"}), 400

    job = q.enqueue(upload_to_youtube, data)
    return jsonify({
        "message": "⏳ Upload job queued",
        "job_id": job.get_id()
    }), 200

@app.route("/status/<job_id>", methods=["GET"])
def check_status(job_id):
    job = q.fetch_job(job_id)
    if job is None:
        return jsonify({"error": "❌ Job not found"}), 404
    return jsonify({
        "status": job.get_status(),
        "result": job.result
    })

if __name__ == "__main__":
    app.run(debug=True)
