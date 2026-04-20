from pathlib import Path
import sys

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "acpc_admission_data.csv"
MODEL_FILE = BASE_DIR / "model" / "model.pkl"

if str(BASE_DIR) not in sys.path:
	sys.path.insert(0, str(BASE_DIR))

from backend.preprocess import load_prediction_dataset


def load_data():
	"""Load and prepare the admission dataset."""
	return load_prediction_dataset()


def encode_features(data):
	"""Encode categorical columns into numeric values."""
	category_encoder = LabelEncoder()
	quota_encoder = LabelEncoder()
	target_encoder = LabelEncoder()

	encoded = data.copy()
	encoded["category"] = category_encoder.fit_transform(encoded["category"])
	encoded["quota"] = quota_encoder.fit_transform(encoded["quota"])
	encoded["admission_field"] = target_encoder.fit_transform(encoded["admission_field"])

	encoders = {
		"category_encoder": category_encoder,
		"quota_encoder": quota_encoder,
		"target_encoder": target_encoder,
	}

	return encoded, encoders


def train_models(features, target):
	"""Split the data and train the required models."""
	class_counts = target.value_counts()
	stratify_target = target if class_counts.min() >= 2 else None

	x_train, x_test, y_train, y_test = train_test_split(
		features,
		target,
		test_size=0.2,
		random_state=42,
		stratify=stratify_target,
	)

	random_forest = RandomForestClassifier(
		random_state=42,
		n_estimators=25,
		max_depth=15,
		n_jobs=1,
	)
	random_forest.fit(x_train, y_train)
	rf_predictions = random_forest.predict(x_test)

	decision_tree = DecisionTreeClassifier(random_state=42, max_depth=15)
	decision_tree.fit(x_train, y_train)
	dt_predictions = decision_tree.predict(x_test)

	rf_accuracy = accuracy_score(y_test, rf_predictions)
	dt_accuracy = accuracy_score(y_test, dt_predictions)
	rf_confusion = confusion_matrix(y_test, rf_predictions)

	print(f"Random Forest Accuracy: {rf_accuracy:.4f}")
	print(f"Decision Tree Accuracy: {dt_accuracy:.4f}")
	print("Random Forest Confusion Matrix:")
	print(rf_confusion)

	return random_forest, x_test, y_test, rf_predictions


def show_sample_predictions(x_test, y_test, y_pred, target_encoder):
	"""Print a few sample predictions for inspection."""
	sample_frame = pd.DataFrame(x_test, columns=["rank", "category", "quota"]).head(5).copy()
	sample_frame["actual_admission_field"] = target_encoder.inverse_transform(y_test[:5])
	sample_frame["predicted_admission_field"] = target_encoder.inverse_transform(y_pred[:5])
	print("Sample Predictions:")
	print(sample_frame.to_string(index=False))


def main():
	"""Run the full training workflow and save the model."""
	data = load_data()
	encoded_data, encoders = encode_features(data)

	features = encoded_data[["rank", "category", "quota"]]
	target = encoded_data["admission_field"]

	model, x_test, y_test, y_pred = train_models(features, target)
	show_sample_predictions(x_test, y_test, y_pred, encoders["target_encoder"])

	# Save the model together with the encoders so future prediction code can reuse them.
	MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
	joblib.dump(
		{
			"model": model,
			"category_encoder": encoders["category_encoder"],
			"quota_encoder": encoders["quota_encoder"],
			"target_encoder": encoders["target_encoder"],
		},
		MODEL_FILE,
	)
	print(f"Saved trained model to: {MODEL_FILE}")


if __name__ == "__main__":
	main()
