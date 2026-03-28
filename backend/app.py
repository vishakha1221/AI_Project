from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__)


@app.route("/")
def home():
    """Serve the frontend page."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/predict", methods=["POST"])
def predict():
    """Return a demo prediction response for now."""
    _request_data = request.get_json(silent=True) or {}
    return jsonify({"predicted_field": "Demo Result"})


@app.route("/style.css")
def style():
    """Serve the frontend stylesheet."""
    return send_from_directory(FRONTEND_DIR, "style.css")


@app.route("/script.js")
def script():
    """Serve the frontend JavaScript file."""
    return send_from_directory(FRONTEND_DIR, "script.js")


if __name__ == "__main__":
    app.run(debug=True)