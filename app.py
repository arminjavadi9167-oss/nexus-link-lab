from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timezone
from uuid import uuid4
from functools import wraps
import os
import logging
import secrets

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ALLOWED_ORIGIN = "https://nexus-link-lab.onrender.com"

# Set these in Render Environment Variables
DASHBOARD_USER = os.environ.get("DASHBOARD_USER", "admin")
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD")

# Store only harmless educational test metadata
test_results = []


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def dashboard_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not DASHBOARD_PASSWORD:
            return "Dashboard password is not configured.", 503

        auth = request.authorization

        if (
            not auth
            or auth.username != DASHBOARD_USER
            or not secrets.compare_digest(
                auth.password or "",
                DASHBOARD_PASSWORD
            )
        ):
            return (
                "Authentication required",
                401,
                {"WWW-Authenticate": 'Basic realm="Nexus Dashboard"'}
            )

        return f(*args, **kwargs)

    return decorated


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "project": "Nexus Link Lab",
        "status": "online",
        "message": "Educational testing API"
    })


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

    result = {
        "test_id": test_id,
        "timestamp": timestamp,
        "status": "success"
    }

    test_results.append(result)

    # Keep only the latest 100 test results
    if len(test_results) > 100:
        del test_results[:-100]

    app.logger.info(
        "Educational test completed: test_id=%s timestamp=%s",
        test_id,
        timestamp
    )

    return jsonify({
        "status": "success",
        "message": "Educational test completed",
        "test_id": test_id
    }), 200


@app.route("/dashboard", methods=["GET"])
@dashboard_auth_required
def dashboard():

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Nexus Link Lab Dashboard</title>

        <style>
            body {
                font-family: Arial, sans-serif;
                background: #101827;
                color: white;
                padding: 20px;
            }

            h1 {
                color: #38bdf8;
            }

            .card {
                background: #1e293b;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 15px;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                background: #1e293b;
            }

            th, td {
                padding: 12px;
                border-bottom: 1px solid #334155;
                text-align: left;
                overflow-wrap: anywhere;
            }

            th {
                color: #38bdf8;
            }

            .success {
                color: #4ade80;
            }

            button {
                padding: 10px 15px;
                border: none;
                border-radius: 8px;
                background: #0284c7;
                color: white;
                cursor: pointer;
            }
        </style>
    </head>

    <body>
        <h1>Nexus Link Lab</h1>
        <p>Educational Test Dashboard</p>

        <div class="card">
            <h2>Total Tests</h2>
            <h3>{{ results|length }}</h3>
        </div>

        <button onclick="location.reload()">Refresh</button>

        <br><br>

        <table>
            <thead>
                <tr>
                    <th>Test ID</th>
                    <th>Timestamp</th>
                    <th>Status</th>
                </tr>
            </thead>

            <tbody>
                {% for result in results %}
                <tr>
                    <td>{{ result.test_id }}</td>
                    <td>{{ result.timestamp }}</td>
                    <td class="success">{{ result.status }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <br>

        <p>
            Only educational test metadata is displayed.
            No credentials or personal information are collected.
        </p>
    </body>
    </html>
    """

    return render_template_string(
        html,
        results=list(reversed(test_results))
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
