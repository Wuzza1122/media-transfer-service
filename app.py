from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
from worker import upload_to_youtube

app = Flask(__name__)
redis_conn = Redis(host='redis', port=6379)  # render will link this
q = Queue(connection=redis_conn)

@app.route("/upload_to_youtube", methods=["POST"])
def enqueue_upload():
    data = request.get_json()
    job = q.enqueue(upload_to_youtube, data)
    return jsonify({
        "message": "✅ Upload job queued",
        "job_id": job.get_id()
    }), 202
