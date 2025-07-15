from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
import os
from worker import upload_to_youtube

app = Flask(__name__)

# ✅ Setup Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
conn = Redis.from_url(redis_url)
q = Queue(connection=conn)

# ✅ POST route to enqueue upload job
@app.route("/upload_to_youtube", methods=["POST"])
def upload():
    try:
        data = request.get_json()
        print("🎯 Enqueuing YouTube upload job:", data)

        # ⏳ Enqueue upload job (do NOT block)
        job = q.enqueue(upload_to_youtube, data)

        return jsonify({
            "status": "🎯 Job enqueued for YouTube upload",
            "job_id": job.get_id(),
            "file_name": data.get("file_name")
        }), 202  # HTTP 202 = Accepted

    except Exception as e:
        print("❌ Failed to enqueue job:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ Health check (optional for Render)
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "✅ Media transfer service is live!"}), 200

if __name__ == "__main__":
    app.run(debug=True)
