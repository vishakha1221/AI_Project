from pathlib import Path
from functools import lru_cache
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from backend.preprocess import (
    encode_training_data,
    load_institute_search_dataset,
    load_prediction_dataset,
    standardize_category,
    standardize_quota,
)


FRONTEND_DIR = BASE_DIR / "frontend"
MODEL_FILE = BASE_DIR / "model" / "model.pkl"
DATA_FILE = BASE_DIR / "data" / "acpc_admission_data.csv"
ENRICHED_DATA_FILE = BASE_DIR / "data" / "acpc_admission_enriched.csv"


PREDICTION_DEFAULTS = {
    "category": "GENERAL",
    "quota": "GUJCET",
}

app = Flask(__name__)


def _resolve_model_file():
    """Find the trained model in common project locations."""
    candidate_files = [
        BASE_DIR / "model" / "model.pkl",
        BASE_DIR / "model" / "trained_model.pkl",
        BASE_DIR / "models" / "model.pkl",
        BASE_DIR / "models" / "trained_model.pkl",
        BASE_DIR / "idel" / "model.pkl",
        BASE_DIR / "idel" / "trained_model.pkl",
    ]

    for candidate in candidate_files:
        if candidate.exists():
            return candidate

    return None


def _match_encoder_label(raw_value, encoder):
    """Map a normalized input value to the exact encoder class label."""
    if raw_value is None:
        return None

    value = str(raw_value).strip()
    if not value:
        return value

    classes = [str(item) for item in getattr(encoder, "classes_", [])]
    if value in classes:
        return value

    normalized_value = value.casefold().replace("_", " ").replace("-", " ").strip()
    for label in classes:
        normalized_label = label.casefold().replace("_", " ").replace("-", " ").strip()
        if normalized_label == normalized_value:
            return label

    return value


def _predict_field(model_bundle, rank, category, quota):
    """Run model inference for one input and return the predicted field."""
    if not category:
        category = model_bundle["default_category"]
    if not quota:
        quota = model_bundle["default_quota"]

    category = standardize_category(category)
    quota = standardize_quota(quota)
    category = _match_encoder_label(category, model_bundle["category_encoder"])
    quota = _match_encoder_label(quota, model_bundle["quota_encoder"])

    category_encoded = model_bundle["category_encoder"].transform([category])[0]
    quota_encoded = model_bundle["quota_encoder"].transform([quota])[0]
    prediction_features = pd.DataFrame(
        [[rank, category_encoded, quota_encoded]],
        columns=["rank", "category", "quota"],
    )
    prediction_encoded = model_bundle["model"].predict(prediction_features)[0]
    return model_bundle["target_encoder"].inverse_transform([prediction_encoded])[0]


def _estimate_segment_accuracy(model_bundle, rank, category, quota):
    """Estimate expected accuracy for selected inputs using historical rows."""
    dataset = load_prediction_dataset().copy()
    if dataset.empty:
        return {"estimated_accuracy": None, "matched_rows": 0, "window": 0}

    selected_category = standardize_category(category or model_bundle["default_category"])
    selected_quota = standardize_quota(quota or model_bundle["default_quota"])
    filtered = dataset[
        (dataset["category"].astype(str).str.casefold() == str(selected_category).casefold())
        & (dataset["quota"].astype(str).str.casefold() == str(selected_quota).casefold())
    ].copy()

    if filtered.empty:
        return {"estimated_accuracy": None, "matched_rows": 0, "window": 0}

    windows = [500, 2000, 5000]
    for window in windows:
        local = filtered[(filtered["rank"] >= (rank - window)) & (filtered["rank"] <= (rank + window))].copy()
        if len(local) >= 25:
            break
    else:
        local = filtered
        window = 0

    predicted_values = []
    actual_values = local["admission_field"].astype(str).tolist()
    for _, row in local.iterrows():
        try:
            predicted_values.append(_predict_field(model_bundle, int(row["rank"]), row["category"], row["quota"]))
        except Exception:
            predicted_values.append(None)

    comparable_pairs = [
        (predicted, actual)
        for predicted, actual in zip(predicted_values, actual_values)
        if predicted is not None
    ]
    if not comparable_pairs:
        return {"estimated_accuracy": None, "matched_rows": 0, "window": window}

    matches = sum(
        1
        for predicted, actual in comparable_pairs
        if str(predicted).strip().casefold() == str(actual).strip().casefold()
    )
    estimated_accuracy = round(matches / len(comparable_pairs), 4)
    return {
        "estimated_accuracy": estimated_accuracy,
        "matched_rows": len(comparable_pairs),
        "window": window,
    }


@app.after_request
def add_cors_headers(response):
    """Allow the frontend to call the API from the browser."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@lru_cache(maxsize=1)
def load_model_bundle():
    """Load the trained model and encoders with fallback to dataset-based encoders."""
    model_file = _resolve_model_file()
    if not model_file or not DATA_FILE.exists():
        return None

    model_artifact = joblib.load(model_file)
    if isinstance(model_artifact, dict) and "model" in model_artifact:
        model = model_artifact["model"]
        category_encoder = model_artifact.get("category_encoder")
        quota_encoder = model_artifact.get("quota_encoder")
        target_encoder = model_artifact.get("target_encoder")
    else:
        model = model_artifact
        category_encoder = None
        quota_encoder = None
        target_encoder = None

    dataset = load_prediction_dataset()
    dataset = dataset.dropna(subset=["category", "quota", "admission_field"]).copy()
    default_category = dataset["category"].astype(str).mode().iat[0] if not dataset.empty else PREDICTION_DEFAULTS["category"]
    default_quota = dataset["quota"].astype(str).mode().iat[0] if not dataset.empty else PREDICTION_DEFAULTS["quota"]
    if category_encoder is None or quota_encoder is None or target_encoder is None:
        _, category_encoder, quota_encoder, target_encoder = encode_training_data(dataset)

    training_accuracy = None
    total_samples = 0
    try:
        category_values = [_match_encoder_label(value, category_encoder) for value in dataset["category"].astype(str)]
        quota_values = [_match_encoder_label(value, quota_encoder) for value in dataset["quota"].astype(str)]
        actual_values = [_match_encoder_label(value, target_encoder) for value in dataset["admission_field"].astype(str)]

        encoded_features = pd.DataFrame(
            {
                "rank": dataset["rank"].astype(int).tolist(),
                "category": category_encoder.transform(category_values),
                "quota": quota_encoder.transform(quota_values),
            }
        )
        predicted_encoded = model.predict(encoded_features)
        predicted_values = target_encoder.inverse_transform(predicted_encoded)
        total_samples = len(predicted_values)
        if total_samples > 0:
            matches = sum(
                1
                for predicted, actual in zip(predicted_values, actual_values)
                if str(predicted).strip().casefold() == str(actual).strip().casefold()
            )
            training_accuracy = round(matches / total_samples, 4)
    except Exception:
        training_accuracy = None
        total_samples = 0

    return {
        "model": model,
        "category_encoder": category_encoder,
        "quota_encoder": quota_encoder,
        "target_encoder": target_encoder,
        "default_category": default_category,
        "default_quota": default_quota,
        "model_file": str(model_file),
        "training_accuracy": training_accuracy,
        "total_samples": total_samples,
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
        return jsonify(
            {
                "error": "Trained model file was not found. Expected one of: model/model.pkl, model/trained_model.pkl, models/model.pkl, idel/model.pkl"
            }
        ), 500

    try:
        predicted_field = _predict_field(model_bundle, rank, category, quota)
    except ValueError:
        return jsonify({"error": "Category or quota is not recognized by the trained model."}), 400

    return jsonify({"predicted_field": predicted_field})


@app.route("/predict/check", methods=["POST"])
def check_prediction_accuracy():
    """Return prediction plus estimated accuracy for selected input values."""
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
        predicted_field = _predict_field(model_bundle, rank, category, quota)
    except ValueError:
        return jsonify({"error": "Category or quota is not recognized by the trained model."}), 400

    segment = _estimate_segment_accuracy(model_bundle, rank, category, quota)

    response = {
        "predicted_field": predicted_field,
        "selected_rank": rank,
        "selected_category": standardize_category(category or model_bundle["default_category"]),
        "selected_quota": standardize_quota(quota or model_bundle["default_quota"]),
        "estimated_input_accuracy": segment.get("estimated_accuracy"),
        "similar_rows_used": segment.get("matched_rows", 0),
        "rank_window": segment.get("window", 0),
        "model_training_accuracy": model_bundle.get("training_accuracy"),
        "evaluated_samples": model_bundle.get("total_samples", 0),
    }
    return jsonify(response)


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
    prediction_dataset = load_prediction_dataset()
    branches = sorted(_unique_values(dataset, "course_name"))
    cities = sorted(_unique_values(dataset, "city"))
    institutes = sorted(_unique_values(dataset, "institute_name"))
    boys_hostel_options = sorted(_unique_values(dataset, "boys_hostel"))
    girls_hostel_options = sorted(_unique_values(dataset, "girls_hostel"))
    categories = sorted(_unique_values(prediction_dataset, "category"))
    quotas = sorted(_unique_values(prediction_dataset, "quota"))
    return jsonify(
        {
            "branches": branches,
            "cities": cities,
            "institutes": institutes,
            "hostel_available": ["Yes", "No"],
            "boys_hostel": boys_hostel_options,
            "girls_hostel": girls_hostel_options,
            "categories": categories,
            "quotas": quotas,
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
    boys_hostel = request.args.get("boys_hostel", "").strip()
    girls_hostel = request.args.get("girls_hostel", "").strip()
    limit = request.args.get("limit", "20")

    if branch:
        dataset = dataset[dataset["course_name"].astype(str).str.strip().str.casefold() == branch.casefold()]
    if city and "city" in dataset.columns:
        dataset = dataset[dataset["city"].astype(str).str.strip().str.casefold() == city.casefold()]
    if institute_name:
        dataset = dataset[dataset["institute_name"].astype(str).str.strip().str.casefold() == institute_name.casefold()]
    if hostel_available and "hostel_available" in dataset.columns:
        dataset = dataset[dataset["hostel_available"].astype(str).str.strip().str.casefold() == hostel_available.casefold()]
    if boys_hostel and "boys_hostel" in dataset.columns:
        dataset = dataset[dataset["boys_hostel"].astype(str).str.strip().str.casefold() == boys_hostel.casefold()]
    if girls_hostel and "girls_hostel" in dataset.columns:
        dataset = dataset[dataset["girls_hostel"].astype(str).str.strip().str.casefold() == girls_hostel.casefold()]

    try:
        limit_value = max(1, int(limit))
    except (TypeError, ValueError):
        limit_value = 20

    columns = [
        column
        for column in [
            "institute_name",
            "course_name",
            "city",
            "hostel_available",
            "boys_hostel",
            "girls_hostel",
            "official_website",
        ]
        if column in dataset.columns
    ]
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