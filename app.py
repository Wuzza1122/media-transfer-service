from flask import Flask, request, jsonify
from worker import upload_to_youtube  # Import your background job

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json()

    download_url = data.get("download_url")
    file_name = data.get("file_name")
    file_size = data.get("file_size")
    destinations = data.get("destinations", [])

    jobs = {}

    # Enqueue YouTube upload if requested
    if "youtube" in destinations and "youtube" in data:
        youtube_data = data["youtube"]
        job = upload_to_youtube.queue(
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
