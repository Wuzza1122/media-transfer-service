from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
import os
from worker import upload_to_youtube

app = Flask(__name__)

# Setup Redis connection (Render will inject REDIS_URL as env variable)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
conn = Redis.from_url(redis_url)
q = Queue(connection=conn)

@app.route("/upload_to_youtube", methods=["POST"])
def upload():
    data = request.get_json()
    print("🎯 Enqueuing YouTube upload job:", data)

    # Enqueue job to background worker
    job = q.enqueue(upload_to_youtube, data)
    
    # Return immediately to avoid timeout
    return jsonify({
        "status": "🎯 Job enqueued for YouTube upload",
        "job_id": job.get_id(),
        "file_name": data.get("file_name")
    }), 202
