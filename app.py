from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timezone
from uuid import uuid4
from functools import wraps
import os
import secrets
import re

app = Flask(__name__)

ALLOWED_ORIGIN = "https://nexus-link-lab.onrender.com"

DASHBOARD_USER = os.environ.get("DASHBOARD_USER", "admin")
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD")

# Store only explicitly consented synthetic test data.
test_results = []


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")

    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
        response.headers["Vary"] = "Origin"

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
                {"WWW-Authenticate": 'Basic realm="Instagram Link Lab Dashboard"'}
            )

        return f(*args, **kwargs)

    return decorated


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "project": "Instagram Link Lab",
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

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid request"
        }), 400

    if data.get("consent") is not True:
        return jsonify({
            "status": "error",
            "message": "Consent required"
        }), 400

    demo_name = data.get("demo_name")
    demo_code = data.get("demo_code")

    if not isinstance(demo_name, str) or not isinstance(demo_code, str):
        return jsonify({
            "status": "error",
            "message": "Invalid test data"
        }), 400

    demo_name = demo_name.strip()
    demo_code = demo_code.strip()

    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,30}", demo_name):
        return jsonify({
            "status": "error",
            "message": "Invalid demo alias"
        }), 400

    if not re.fullmatch(r"[a-zA-Z0-9]{1,20}", demo_code):
        return jsonify({
            "status": "error",
            "message": "Invalid synthetic test ID"
        }), 400

    test_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    result = {
        "test_id": test_id,
        "demo_name": demo_name,
        "demo_code": demo_code,
        "timestamp": timestamp,
        "status": "success"
    }

    test_results.append(result)

    if len(test_results) > 100:
        del test_results[:-100]

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
        <title>Instagram Link Lab Dashboard</title>

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
        <h1>Instagram Link Lab</h1>
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
                    <th>Demo Alias</th>
                    <th>Synthetic Test ID</th>
                    <th>Test ID</th>
                    <th>Timestamp</th>
                    <th>Status</th>
                </tr>
            </thead>

            <tbody>
                {% for result in results %}
                <tr>
                    <td>{{ result.demo_name }}</td>
                    <td>{{ result.demo_code }}</td>
                    <td>{{ result.test_id }}</td>
                    <td>{{ result.timestamp }}</td>
                    <td class="success">{{ result.status }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <br>

        <p>
            Only consented synthetic educational test data is displayed.
            Do not submit passwords or real account information.
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
