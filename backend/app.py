from pathlib import Path
from functools import lru_cache
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import joblib
from flask import Flask, jsonify, request, send_from_directory

from backend.preprocess import encode_training_data, load_institute_search_dataset, load_prediction_dataset


FRONTEND_DIR = BASE_DIR / "frontend"
MODEL_FILE = BASE_DIR / "model" / "model.pkl"
DATA_FILE = BASE_DIR / "data" / "acpc_admission_data.csv"
ENRICHED_DATA_FILE = BASE_DIR / "data" / "acpc_admission_enriched.csv"


PREDICTION_DEFAULTS = {
    "category": "OPEN",
    "quota": "GUJCET",
}

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
    dataset = dataset.dropna(subset=["category", "quota", "admission_field"]).copy()
    default_category = dataset["category"].astype(str).mode().iat[0] if not dataset.empty else PREDICTION_DEFAULTS["category"]
    default_quota = dataset["quota"].astype(str).mode().iat[0] if not dataset.empty else PREDICTION_DEFAULTS["quota"]
    _, category_encoder, quota_encoder, target_encoder = encode_training_data(dataset)

    return {
        "model": model,
        "category_encoder": category_encoder,
        "quota_encoder": quota_encoder,
        "target_encoder": target_encoder,
        "default_category": default_category,
        "default_quota": default_quota,
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
        category = str(payload.get("category", "")).strip() or None
        quota = str(payload.get("quota", "")).strip() or None
    except (TypeError, ValueError):
        return jsonify({"error": "Rank must be a valid number."}), 400

    model_bundle = load_model_bundle()
    if not model_bundle:
        return jsonify({"error": "Trained model file was not found."}), 500

    try:
        if not category:
            category = model_bundle["default_category"]
        if not quota:
            quota = model_bundle["default_quota"]
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


@app.route("/api/options")
def options():
    """Return filter options for the institute search UI."""
    dataset = load_institute_search_dataset()
    branches = sorted(_unique_values(dataset, "course_name"))
    cities = sorted(_unique_values(dataset, "city"))
    institutes = sorted(_unique_values(dataset, "institute_name"))
    return jsonify(
        {
            "branches": branches,
            "cities": cities,
            "institutes": institutes,
            "hostel_available": ["Yes", "No"],
            "categories": ["OPEN", "SC", "ST", "SEBC", "EWS", "TFWS"],
            "quotas": ["D2D", "GUJCET"],
        }
    )


@app.route("/api/filter")
def filter_institutes():
    """Filter the admissions dataset by institute, branch, and hostel availability."""
    dataset = load_institute_search_dataset().copy()
    branch = request.args.get("branch", "").strip()
    city = request.args.get("city", "").strip()
    institute_name = request.args.get("institute_name", "").strip()
    hostel_available = request.args.get("hostel_available", "").strip()
    limit = request.args.get("limit", "20")

    if branch:
        dataset = dataset[dataset["course_name"].astype(str).str.strip().str.casefold() == branch.casefold()]
    if city and "city" in dataset.columns:
        dataset = dataset[dataset["city"].astype(str).str.strip().str.casefold() == city.casefold()]
    if institute_name:
        dataset = dataset[dataset["institute_name"].astype(str).str.strip().str.casefold() == institute_name.casefold()]
    if hostel_available and "hostel_available" in dataset.columns:
        dataset = dataset[dataset["hostel_available"].astype(str).str.strip().str.casefold() == hostel_available.casefold()]

    try:
        limit_value = max(1, int(limit))
    except (TypeError, ValueError):
        limit_value = 20

    columns = [column for column in ["institute_name", "course_name", "city", "hostel_available", "official_website"] if column in dataset.columns]
    filtered = dataset[columns].fillna("").drop_duplicates().head(limit_value)
    return jsonify({"results": filtered.to_dict(orient="records")})


def _unique_values(dataframe, column_name):
    """Collect sorted, non-empty string values from a dataframe column."""
    if column_name not in dataframe.columns:
        return []

    values = set()
    for value in dataframe[column_name].astype(str):
        cleaned_value = value.strip()
        if cleaned_value and cleaned_value.casefold() != "nan":
            values.add(cleaned_value)
    return values


if __name__ == "__main__":
    app.run(debug=True)