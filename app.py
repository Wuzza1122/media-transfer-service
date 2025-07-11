from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/upload_to_frameio", methods=["POST"])
def upload_to_frameio():
    try:
        data = request.json

        required_fields = ["download_url", "file_name", "file_size"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "❌ Missing required fields"}), 400

        # Placeholder logic (replace with actual Frame.io upload later)
        print("Received file:", data["file_name"])
        return jsonify({"message": "✅ Frame.io upload route hit!", "file": data["file_name"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"})
