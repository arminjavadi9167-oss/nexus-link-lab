from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

records = []

@app.route("/")
def home():
    return "Nexus Link Lab API is running!"

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    testcode = data.get("testcode", "").strip()

    if not username or not testcode:
        return jsonify({"error": "Missing test data"}), 400

    records.append({
        "username": username,
        "testcode": testcode,
        "time": datetime.now().isoformat()
    })

    return jsonify({"status": "success"})

@app.route("/dashboard")
def dashboard():
    return jsonify(records)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
