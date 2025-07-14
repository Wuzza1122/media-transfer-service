from flask import Flask, request, jsonify
import os
from redis import Redis
from rq import Queue
from worker import upload_to_youtube  # Add more destinations here if needed

app = Flask(__name__)

# ✅ Setup Redis connection from environment (Upstash-compatible)
redis_url = os.getenv("REDIS_URL")  # Must be set in Render ENV vars
conn = Redis.from_url(redis_url)
q = Queue(connection=conn)

# ✅ Health check route
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "✅ Media transfer service is live!"})

# ✅ Main upload route
@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_json()
        download_url = data.get("download_url")
        file_name = data.get("file_name")
        file_size = data.get("file_size")
        destinations = data.get("destinations", [])

        jobs = {}

        # ✅ Handle YouTube upload
        if "youtube" in destinations and "youtube" in data:
            youtube_data = data["youtube"]
            job = q.enqueue(
                upload_to_youtube,
                file_name=file_name,
                download_url=download_url,
                file_size=file_size,
                access_token=youtube_data["access_token"],
                refresh_token=youtube_data["refresh_token"],
                client_id=youtube_data["client_id"],
                client_secret=youtube_data["client_secret"]
            )
            jobs["youtube"] = job.get_id()

        return jsonify({
            "file_name": file_name,
            "jobs": jobs,
            "status": "🎯 Jobs enqueued"
        }), 202

    except Exception as e:
        print("❌ Upload job failed:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ Start the app (only used for local testing)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
