from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timezone
from uuid import uuid4
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ALLOWED_ORIGIN = "https://nexus-link-lab.onrender.com"


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/", methods=["GET"])
def home():
    return send_from_directory(app.root_path, "index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/submit", methods=["POST", "OPTIONS"])
def submit():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or data.get("consent") is not True:
        return jsonify({
            "status": "error",
            "message": "Consent required"
        }), 400

    test_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    app.logger.info(
        "Educational demo completed: test_id=%s timestamp=%s",
        test_id,
        timestamp
    )

    return jsonify({
        "status": "success",
        "notification_sent": False,
        "message": "Educational test completed",
        "test_id": test_id
    }), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
