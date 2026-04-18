from pathlib import Path
import re

import pandas as pd
from sklearn.preprocessing import LabelEncoder


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "acpc_admission_data.csv"
CLEANED_DATA_FILE = BASE_DIR / "data" / "acpc_cleaned_data.csv"
ENRICHED_DATA_FILE = BASE_DIR / "data" / "acpc_admission_enriched.csv"
INSTITUTE_MASTER_FILE = BASE_DIR / "data" / "institute_master.csv"


CITY_RULES = [
	("ahmedabad", "Ahmedabad"),
	("surat", "Surat"),
	("vadodara", "Vadodara"),
	("rajkot", "Rajkot"),
	("anand", "Anand"),
	("vvnagar", "Anand"),
	("karamsad", "Anand"),
	("bakrol", "Anand"),
	("changa", "Anand"),
	("vasad", "Anand"),
	("gandhinagar", "Gandhinagar"),
	("raisan", "Gandhinagar"),
	("chandkheda", "Ahmedabad"),
	("moti bhoyan", "Gandhinagar"),
	("kalol", "Gandhinagar"),
	("uvarsad", "Gandhinagar"),
	("nadiad", "Nadiad"),
	("mehsana", "Mehsana"),
	("kherva", "Mehsana"),
	("bhandu", "Mehsana"),
	("linch", "Mehsana"),
	("bhavnagar", "Bhavnagar"),
	("bharuch", "Bharuch"),
	("valsad", "Valsad"),
	("navsari", "Navsari"),
	("junagadh", "Junagadh"),
	("amreli", "Amreli"),
	("palanpur", "Palanpur"),
	("patan", "Patan"),
	("modasa", "Modasa"),
	("godhra", "Godhra"),
	("dahod", "Dahod"),
	("bhuj", "Bhuj"),
	("porbandar", "Porbandar"),
	("morbi", "Morbi"),
	("khedbrahma", "Khedbrahma"),
	("bardoli", "Bardoli"),
	("kosamba", "Kosamba"),
	("kim", "Kim"),
	("waghodia", "Waghodia"),
	("kotambi", "Kotambi"),
	("vapi", "Vapi"),
	("wadhvan", "Wadhvan"),
]


BRANCH_STANDARD_MAP = {
	"computer engg": "Computer Engineering",
	"computer engineering": "Computer Engineering",
	"computer": "Computer Engineering",
	"it": "Information Technology",
	"information technology": "Information Technology",
	"civil engg": "Civil Engineering",
	"civil engineering": "Civil Engineering",
	"mechanical engg": "Mechanical Engineering",
	"mechanical engineering": "Mechanical Engineering",
	"electrical engg": "Electrical Engineering",
	"electrical engineering": "Electrical Engineering",
	"electronics engg": "Electronics Engineering",
	"electronics engineering": "Electronics Engineering",
	"production engg": "Production Engineering",
	"production engineering": "Production Engineering",
}


INSTITUTE_STANDARD_MAP = {
	"gec bhavnagar": "Government Engineering College, Bhavnagar",
	"government engineering college bhavnagar": "Government Engineering College, Bhavnagar",
	"government engineering college, bhavnagar": "Government Engineering College, Bhavnagar",
	"government engg college bhavnagar": "Government Engineering College, Bhavnagar",
	"ssec bhavnagar": "Shantilal Shah Engineering College, Bhavnagar",
	"shantilal shah engineering college bhavnagar": "Shantilal Shah Engineering College, Bhavnagar",
	"shantilal shah engineering college, bhavnagar": "Shantilal Shah Engineering College, Bhavnagar",
	"gyanmanjari bhavnagar": "Gyanmanjari Institute of Technology, Bhavnagar",
	"gyanmanjari institute of technology bhavnagar": "Gyanmanjari Institute of Technology, Bhavnagar",
	"ld college of engineering ahmedabad": "L.D. College of Engineering, Ahmedabad",
	"ldce ahmedabad": "L.D. College of Engineering, Ahmedabad",
	"bvm vvnagar": "Birla Vishvakarma Mahavidyalaya, V.V. Nagar",
	"birla vishvakarma mahavidyalaya": "Birla Vishvakarma Mahavidyalaya, V.V. Nagar",
}


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


def normalize_text(value):
	"""Lowercase and remove punctuation so names can be matched reliably."""
	if pd.isna(value):
		return ""
	text = str(value).lower()
	text = re.sub(r"[.,]", " ", text)
	text = re.sub(r"\s+", " ", text).strip()
	return text


def infer_city(institute_name):
	"""Guess the city from the institute name using simple keyword rules."""
	name = normalize_text(institute_name)
	for keyword, city in CITY_RULES:
		if keyword in name:
			return city
	return "Other"


def standardize_branch(value):
	"""Convert branch aliases into one standard label."""
	name = normalize_text(value)
	if not name:
		return ""

	for token in [" d2d", " gujcet", " tfws", " gia", " sfi"]:
		name = name.replace(token, "")
	name = re.sub(r"\s+", " ", name).strip()
	if name in BRANCH_STANDARD_MAP:
		return BRANCH_STANDARD_MAP[name]
	if "computer science" in name:
		return "Computer Science & Engineering"
	if "aero space" in name:
		return "Aerospace Engineering"
	if "electronics and communication" in name or "electronics & communication" in name:
		return "Electronics & Communication Engineering"
	if "electronics and telecommunication" in name:
		return "Electronics & Telecommunication Engineering"
	if "electronic" in name and "communication" not in name:
		return "Electronics Engineering"
	if "computer" in name:
		return "Computer Engineering"
	if "civil" in name:
		return "Civil Engineering"
	if "mechanical" in name:
		return "Mechanical Engineering"
	if "electrical" in name:
		return "Electrical Engineering"
	if "information technology" in name or name == "it":
		return "Information Technology"
	if "production" in name:
		return "Production Engineering"
	return re.sub(r"\s+", " ", name).title()


def standardize_institute_name(value):
	"""Merge institute name variations into one standard college name."""
	name = normalize_text(value)
	if not name:
		return ""
	if name in INSTITUTE_STANDARD_MAP:
		return INSTITUTE_STANDARD_MAP[name]
	compact = name.replace(" ", "")
	for key, standard_name in INSTITUTE_STANDARD_MAP.items():
		if compact == key.replace(" ", ""):
			return standard_name
	if name.startswith("gec "):
		return f"Government Engineering College, {name.split(' ', 1)[1].title()}"
	if name.startswith("government engineering college"):
		suffix = name.replace("government engineering college", "").strip(" ,")
		return f"Government Engineering College, {suffix.title()}" if suffix else "Government Engineering College"
	return re.sub(r"\s+", " ", name).title()


def load_institute_search_dataset():
	"""Build a search-friendly dataset from the admissions CSV and institute master CSV."""
	admissions = pd.read_csv(DATA_FILE)
	for column in ["course_name", "admission_field", "institute_name"]:
		if column in admissions.columns:
			admissions[column] = admissions[column].fillna("")
	admissions["course_name"] = admissions["course_name"].apply(standardize_branch)
	admissions["admission_field"] = admissions["admission_field"].apply(standardize_branch)
	admissions["institute_name"] = admissions["institute_name"].apply(standardize_institute_name)
	if not INSTITUTE_MASTER_FILE.exists():
		search_data = admissions.copy()
		search_data["hostel_available"] = ""
		search_data["official_website"] = ""
		search_data["city"] = search_data.get("institute_name", "").apply(infer_city)
		return search_data

	institute_master = pd.read_csv(INSTITUTE_MASTER_FILE)
	institute_master["institute_name"] = institute_master["institute_name"].fillna("").apply(standardize_institute_name)
	admissions["join_key"] = admissions["institute_name"].astype(str).map(normalize_text)
	institute_master["join_key"] = institute_master["institute_name"].astype(str).map(normalize_text)
	merged = admissions.merge(
		institute_master[["join_key", "hostel_available", "official_website"]],
		on="join_key",
		how="left",
	)
	merged["hostel_available"] = merged["hostel_available"].fillna("")
	merged["official_website"] = merged["official_website"].fillna("")
	merged["city"] = merged["institute_name"].apply(infer_city)
	merged = merged.drop_duplicates()
	merged = merged.drop(columns=["join_key"])
	return merged


def load_enriched_dataset():
	"""Load the merged admissions dataset if it exists, otherwise fall back to the base CSV."""
	if CLEANED_DATA_FILE.exists():
		return pd.read_csv(CLEANED_DATA_FILE)
	if ENRICHED_DATA_FILE.exists():
		return pd.read_csv(ENRICHED_DATA_FILE)
	return pd.read_csv(DATA_FILE)
