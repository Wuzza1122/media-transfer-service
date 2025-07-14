from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
import os
from worker import upload_to_youtube, upload_to_frameio  # 👈 Add other destinations here

app = Flask(__name__)

# ✅ Setup Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
conn = Redis.from_url(redis_url)
q = Queue(connection=conn)

# ✅ Generic POST route to handle multiple destinations
@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_json()
        print("📦 Incoming upload request:", data)

        # Check destinations array
        destinations = data.get("destinations", [])
        if not destinations:
            return jsonify({"error": "❌ No destinations specified"}), 400

        # Enqueue separate jobs for each destination
        jobs = {}
        if "youtube" in destinations:
            jobs["youtube"] = q.enqueue(upload_to_youtube, data)

        if "frameio" in destinations:
            jobs["frameio"] = q.enqueue(upload_to_frameio, data)

        return jsonify({
            "status": "🎯 Jobs enqueued",
            "jobs": {dest: job.get_id() for dest, job in jobs.items()},
            "file_name": data.get("file_name")
        }), 202  # HTTP 202 = Accepted

    except Exception as e:
        print("❌ Failed to enqueue job:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ Health check
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "✅ Media transfer service is live!"}), 200

# ✅ Needed to run locally
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
