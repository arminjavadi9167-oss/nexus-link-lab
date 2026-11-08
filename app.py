from flask import Flask, request, jsonify
from datetime import datetime, timezone

app = Flask(__name__)

records = []

@app.route("/", methods=["GET"])
def home():
    return "Nexus Link Lab API is running!"

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "")
    testcode = data.get("testcode", "")

    if not isinstance(username, str) or not isinstance(testcode, str):
        return jsonify({"error": "Invalid test data"}), 400

    username = username.strip()
    testcode = testcode.strip()

    if not username or not testcode:
        return jsonify({"error": "Missing test data"}), 400

    if len(username) > 40 or len(testcode) > 40:
        return jsonify({"error": "Test data is too long"}), 400

    records.append({
        "username": username,
        "testcode": testcode,
        "time": datetime.now(timezone.utc).isoformat()
    })

    return jsonify({"status": "success"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
