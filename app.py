from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timezone
from uuid import uuid4
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
import json
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


@app.route("/", methods=["GET"])
def home():
    return send_from_directory(app.root_path, "index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/submit", methods=["POST"])
def submit():

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or data.get("consent") is not True:
        return jsonify({
            "status": "error",
            "message": "Consent required"
        }), 400

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        app.logger.error("Telegram environment variables are missing")

        return jsonify({
            "status": "error",
            "message": "Server configuration error"
        }), 500

    test_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    message = (
        "Nexus Link Lab\n"
        "Educational demo completed!\n"
        f"Test ID: {test_id}\n"
        f"Time: {timestamp}"
    )

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = urlencode({
        "chat_id": chat_id,
        "text": message
    }).encode("utf-8")

    try:
        req = Request(
            api_url,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            method="POST"
        )

        with urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))

        if not result.get("ok"):
            app.logger.error(
                "Telegram API returned an unsuccessful response"
            )

            return jsonify({
                "status": "error",
                "message": "Telegram rejected the notification"
            }), 502

        app.logger.info(
            "Educational test %s completed and notification sent",
            test_id
        )

        return jsonify({
            "status": "success",
            "notification_sent": True
        }), 200

    except HTTPError as error:
        try:
            error_data = json.loads(
                error.read().decode("utf-8")
            )
            description = error_data.get(
                "description",
                "Unknown Telegram API error"
            )
        except Exception:
            description = "Could not read Telegram error response"

        app.logger.error(
            "Telegram HTTP error %s: %s",
            error.code,
            description
        )

        return jsonify({
            "status": "error",
            "message": "Telegram notification failed"
        }), 502

    except URLError as error:
        app.logger.error(
            "Telegram connection error: %s",
            error.reason
        )

        return jsonify({
            "status": "error",
            "message": "Could not connect to Telegram"
        }), 502

    except Exception:
        app.logger.exception("Unexpected notification error")

        return jsonify({
            "status": "error",
            "message": "Unexpected server error"
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
