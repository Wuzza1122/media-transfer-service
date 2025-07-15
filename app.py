@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_json()
        destination = data.get("destination")

        print(f"🎯 Enqueuing upload job for: {destination}")

        if destination == "youtube":
            job = q.enqueue(upload_to_youtube, data)
        elif destination == "frameio":
            job = q.enqueue(upload_to_frameio, data)
        else:
            return jsonify({"error": "❌ Unknown destination"}), 400

        return jsonify({
            "status": f"🎯 Job enqueued for {destination}",
            "job_id": job.get_id(),
            "file_name": data.get("file_name")
        }), 202

    except Exception as e:
        print("❌ Failed to enqueue job:", str(e))
        return jsonify({"error": str(e)}), 500
