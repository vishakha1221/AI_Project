from pathlib import Path

import pandas as pd
from sklearn.preprocessing import LabelEncoder


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "acpc_admission_data.csv"


def load_prediction_dataset():
	"""Load the columns needed for prediction and clean them."""
	dataset = pd.read_csv(DATA_FILE, usecols=["rank", "category", "quota", "admission_field"])
	dataset = dataset.dropna().copy()
	dataset["rank"] = pd.to_numeric(dataset["rank"], errors="coerce")
	dataset = dataset.dropna(subset=["rank"])
	dataset["rank"] = dataset["rank"].astype(int)
	return dataset


def encode_training_data(dataset):
	"""Encode the categorical columns for training."""
	category_encoder = LabelEncoder()
	quota_encoder = LabelEncoder()
	target_encoder = LabelEncoder()

	encoded = dataset.copy()
	encoded["category"] = category_encoder.fit_transform(encoded["category"].astype(str))
	encoded["quota"] = quota_encoder.fit_transform(encoded["quota"].astype(str))
	encoded["admission_field"] = target_encoder.fit_transform(encoded["admission_field"].astype(str))

	return encoded, category_encoder, quota_encoder, target_encoder
