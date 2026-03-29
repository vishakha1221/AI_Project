from pathlib import Path
from functools import lru_cache
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import joblib
from flask import Flask, jsonify, request, send_from_directory

from backend.preprocess import encode_training_data, load_prediction_dataset


FRONTEND_DIR = BASE_DIR / "frontend"
MODEL_FILE = BASE_DIR / "model" / "model.pkl"
DATA_FILE = BASE_DIR / "data" / "acpc_admission_data.csv"

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    """Allow the frontend to call the API from the browser."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@lru_cache(maxsize=1)
def load_model_bundle():
    """Load the trained model and recreate the label encoders from the CSV."""
    if not MODEL_FILE.exists() or not DATA_FILE.exists():
        return None

    model_artifact = joblib.load(MODEL_FILE)
    if isinstance(model_artifact, dict) and "model" in model_artifact:
        model = model_artifact["model"]
    else:
        model = model_artifact

    dataset = load_prediction_dataset()
    _, category_encoder, quota_encoder, target_encoder = encode_training_data(dataset)

    return {
        "model": model,
        "category_encoder": category_encoder,
        "quota_encoder": quota_encoder,
        "target_encoder": target_encoder,
    }


@app.route("/")
def home():
    """Serve the frontend page."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/predict", methods=["POST"])
def predict():
    """Predict the admission field using the trained model."""
    payload = request.get_json(silent=True) or {}

    try:
        rank = int(payload.get("rank"))
        category = str(payload.get("category", "")).strip()
        quota = str(payload.get("quota", "")).strip()
    except (TypeError, ValueError):
        return jsonify({"error": "Rank must be a valid number."}), 400

    model_bundle = load_model_bundle()
    if not model_bundle:
        return jsonify({"error": "Trained model file was not found."}), 500

    try:
        category_encoded = model_bundle["category_encoder"].transform([category])[0]
        quota_encoded = model_bundle["quota_encoder"].transform([quota])[0]
        prediction_encoded = model_bundle["model"].predict([[rank, category_encoded, quota_encoded]])[0]
        predicted_field = model_bundle["target_encoder"].inverse_transform([prediction_encoded])[0]
    except ValueError:
        return jsonify({"error": "Category or quota is not recognized by the trained model."}), 400

    return jsonify({"predicted_field": predicted_field})


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