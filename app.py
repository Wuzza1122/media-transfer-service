from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
import os
from worker import upload_to_youtube, upload_to_frameio

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ Setup Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
conn = Redis.from_url(redis_url)
q = Queue(connection=conn)

# ✅ Universal Upload Route
@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_json()
        destination = data.get("destination")

        print(f"🎯 Received upload job for: {destination}")

        if destination == "youtube":
            job = q.enqueue(upload_to_youtube, data)
        elif destination == "frameio":
            job = q.enqueue(upload_to_frameio, data)
        else:
            return jsonify({"error": "❌ Unknown destination. Use 'youtube' or 'frameio'."}), 400

        return jsonify({
            "status": "✅ Job enqueued",
            "job_id": job.get_id(),
            "destination": destination,
            "file_name": data.get("file_name")
        }), 202

    except Exception as e:
        print("❌ Failed to enqueue job:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ Health check
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "✅ Media transfer service is live!"}), 200

if __name__ == "__main__":
    app.run(debug=True)
