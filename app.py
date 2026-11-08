from flask import Flask, request, jsonify
from datetime import datetime, timezone
from uuid import uuid4
import urllib.request
import urllib.parse
import json
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Instagram Link Lab API is running!"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}

    if data.get("consent") is not True:
        return jsonify({"error": "Consent required"}), 400

    record_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return jsonify({"error": "Telegram not configured"}), 500

    message = (
        "Instagram Link Lab\n"
        "New educational test completed!\n"
        f"Test ID: {record_id}\n"
        f"Time: {timestamp}"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message
    }).encode()

    try:
        req = urllib.request.Request(url, data=payload)

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read())

        if not result.get("ok"):
            raise RuntimeError("Telegram notification failed")

        return jsonify({
            "status": "success",
            "notification_sent": True
        })

    except Exception:
        app.logger.exception("Telegram notification failed")
        return jsonify({
            "status": "error",
            "notification_sent": False
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
