from pathlib import Path

import joblib
import pandas as pd

from backend.preprocess import encode_training_data, load_prediction_dataset


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "acpc_admission_data.csv"
MODEL_FILE = BASE_DIR / "model" / "model.pkl"


def load_model_bundle():
    """Load the model and rebuild encoders from the CSV."""
    model_artifact = joblib.load(MODEL_FILE)
    model = model_artifact["model"] if isinstance(model_artifact, dict) and "model" in model_artifact else model_artifact

    dataset = load_prediction_dataset()
    encoded_data, category_encoder, quota_encoder, target_encoder = encode_training_data(dataset)

    return model, category_encoder, quota_encoder, target_encoder, encoded_data


def check_prediction(rank, category, quota, actual_admission_field):
    """Print the prediction result and whether it matches the actual field."""
    model, category_encoder, quota_encoder, target_encoder, _ = load_model_bundle()

    category_encoded = category_encoder.transform([category])[0]
    quota_encoded = quota_encoder.transform([quota])[0]

    predicted_encoded = model.predict([[rank, category_encoded, quota_encoded]])[0]
    predicted_field = target_encoder.inverse_transform([predicted_encoded])[0]

    is_correct = str(predicted_field).strip().lower() == str(actual_admission_field).strip().lower()

    print("Input values:")
    print(f"  rank: {rank}")
    print(f"  category: {category}")
    print(f"  quota: {quota}")
    print(f"  actual admission field: {actual_admission_field}")
    print()
    print(f"Predicted field: {predicted_field}")
    print(f"Matched: {'Yes' if is_correct else 'No'}")


def run_sample_from_csv(row_index=0):
    """Check one known row from the CSV against the trained model."""
    data = pd.read_csv(DATA_FILE)
    sample = data.iloc[row_index]

    check_prediction(
        rank=int(sample["rank"]),
        category=str(sample["category"]),
        quota=str(sample["quota"]),
        actual_admission_field=str(sample["admission_field"]),
    )


if __name__ == "__main__":
    # Change the row index if you want to test another known record from the CSV.
    run_sample_from_csv(row_index=12)