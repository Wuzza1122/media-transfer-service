from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "✅ YouTube Upload Service is running!"

@app.route("/upload_to_youtube", methods=["POST"])
def upload_to_youtube():
    try:
        data = request.get_json()

        # ✅ Required fields
        required_fields = [
            "download_url",
            "file_name",
            "file_size",
            "access_token",
            "refresh_token",
            "client_id",
            "client_secret"
        ]

        # ❌ Check for missing fields
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({"error": f"❌ Missing fields: {', '.join(missing)}"}), 400

        # ✅ Confirm input accepted (YouTube upload logic will go here)
        return jsonify({
            "message": "✅ Ready to upload to YouTube",
            "file_name": data["file_name"],
            "file_size": data["file_size"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
