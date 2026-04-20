from pathlib import Path
import re

import pandas as pd
from sklearn.preprocessing import LabelEncoder


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "acpc_admission_data.csv"
CLEANED_DATA_FILE = BASE_DIR / "data" / "acpc_cleaned_data.csv"
CONFLICT_FREE_DATA_FILE = BASE_DIR / "data" / "acpc_admission_conflict_resolved.csv"
ENRICHED_DATA_FILE = BASE_DIR / "data" / "acpc_admission_enriched.csv"
INSTITUTE_MASTER_FILE = BASE_DIR / "data" / "institute_master.csv"
INSTITUTE_MASTER_FILE_V2 = BASE_DIR / "data" / "institue_master1.csv"


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


CATEGORY_STANDARD_MAP = {
	"OPEN": "GENERAL",
	"GENERAL": "GENERAL",
	"GEN": "GENERAL",
	"OPEN-PH": "GENERAL",
	"GEN-PH": "GENERAL",
	"OPPH": "GENERAL",
	"OPEN-EWS": "EWS",
	"EWS": "EWS",
	"OPEN-EWS-PH": "EWS",
	"EWPH": "EWS",
	"EWS-PH": "EWS",
	"SC": "SC",
	"SC-PH": "SC",
	"SEBC": "SEBC",
	"SEBC-PH": "SEBC",
	"SEPH": "SEBC",
	"ST": "ST",
	"ST-PH": "ST",
	"TFWS": "TFWS",
	"EX": "",
	"ESM": "",
}


QUOTA_STANDARD_MAP = {
	"GUJCET": "GUJCET",
	"GUJCET_RANK": "GUJCET",
	"D2D": "D2D",
	"ALL INDIA": "",
	"ALL INDIA_RANK": "",
	"HOME STATE": "",
	"JEE": "",
}


ALLOWED_CATEGORIES = {"GENERAL", "SC", "ST", "SEBC", "EWS", "TFWS"}
ALLOWED_QUOTAS = {"D2D", "GUJCET"}


def _normalize_code(value):
	"""Uppercase and normalize separators for category and quota codes."""
	if pd.isna(value):
		return ""
	code = str(value).strip().upper()
	code = code.replace("/", "-")
	code = re.sub(r"\s+", " ", code)
	return code


def standardize_category(value):
	"""Resolve category aliases to one standard value."""
	code = _normalize_code(value)
	if not code:
		return ""
	resolved = CATEGORY_STANDARD_MAP.get(code, code)
	if resolved in ALLOWED_CATEGORIES:
		return resolved
	return ""


def standardize_quota(value):
	"""Resolve quota aliases to one standard value."""
	code = _normalize_code(value).replace("-", "_")
	if not code:
		return ""
	resolved = QUOTA_STANDARD_MAP.get(code, code.replace("_", " "))
	if resolved in ALLOWED_QUOTAS:
		return resolved
	return ""


def load_prediction_dataset():
	"""Load the columns needed for prediction and clean them."""
	dataset = pd.read_csv(DATA_FILE, usecols=["rank", "category", "quota", "admission_field"])
	dataset = dataset.dropna().copy()
	dataset["category"] = dataset["category"].apply(standardize_category)
	dataset["quota"] = dataset["quota"].apply(standardize_quota)
	dataset["rank"] = pd.to_numeric(dataset["rank"], errors="coerce")
	dataset = dataset.dropna(subset=["rank"])
	dataset["rank"] = dataset["rank"].astype(int)
	dataset = dataset[
		(dataset["category"].astype(str).str.strip() != "")
		& (dataset["quota"].astype(str).str.strip() != "")
		& (dataset["admission_field"].astype(str).str.strip() != "")
	].copy()
	return dataset


def export_conflict_resolved_dataset(output_file=CONFLICT_FREE_DATA_FILE):
	"""Save a CSV with standardized category and quota values for all records."""
	dataset = pd.read_csv(DATA_FILE)
	if "category" in dataset.columns:
		dataset["category"] = dataset["category"].apply(standardize_category)
	if "quota" in dataset.columns:
		dataset["quota"] = dataset["quota"].apply(standardize_quota)
	dataset = dataset[
		(dataset["category"].astype(str).str.strip() != "")
		& (dataset["quota"].astype(str).str.strip() != "")
	].copy()
	dataset.to_csv(output_file, index=False)
	return output_file


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
	text = re.sub(r"[^a-z0-9]+", " ", text)
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

	# Fix common typos before matching branch rules.
	name = name.replace("engireeng", "engineering")
	name = name.replace("enginerring", "engineering")
	name = name.replace("enginering", "engineering")
	name = name.replace("infomation", "information")
	name = name.replace("technolgy", "technology")
	name = name.replace("chemengg", "chemical engineering")
	name = re.sub(r"\bengg\b", "engineering", name)
	name = re.sub(r"\btech\b", "technology", name)

	for token in [" d2d", " gujcet", " tfws", " gia", " sfi"]:
		name = name.replace(token, "")
	name = re.sub(r"\s+", " ", name).strip()
	if name in BRANCH_STANDARD_MAP:
		return BRANCH_STANDARD_MAP[name]
	if "information tech" in name or "information technology" in name or name == "it":
		return "Information Technology"
	if "information communication technology" in name or "information communication tech" in name:
		return "Information Communication Technology"
	if "computer science" in name:
		return "Computer Science Engineering"
	if "aero space" in name:
		return "Aerospace Engineering"
	if "electronics communication" in name:
		return "Electronics & Communication Engineering"
	if "electronics and communication" in name or "electronics & communication" in name:
		return "Electronics & Communication Engineering"
	if "electronics and telecommunication" in name:
		return "Electronics & Telecommunication Engineering"
	if "electronic" in name and "communication" not in name:
		return "Electronics Engineering"
	if "computer" in name and "science" not in name and "information" not in name:
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
	if "chemical" in name:
		return "Chemical Engineering"
	if "automobile" in name:
		return "Automobile Engineering"
	return re.sub(r"\s+", " ", name).title()


def standardize_institute_name(value):
	"""Merge institute name variations into one standard college name."""
	name = normalize_text(value)
	if not name:
		return ""

	# Normalize common spelling and abbreviation conflicts.
	name = name.replace("enginerring", "engineering")
	name = name.replace("enginering", "engineering")
	name = name.replace("engireeng", "engineering")
	name = re.sub(r"\bengg\b", "engineering", name)
	name = re.sub(r"\bbharuc\b", "bharuch", name)
	name = re.sub(r"\bbharuch+h*\b", "bharuch", name)
	name = name.replace("gandhinager", "gandhinagar")
	name = re.sub(r"\s+", " ", name).strip()

	if name in INSTITUTE_STANDARD_MAP:
		return INSTITUTE_STANDARD_MAP[name]
	compact = name.replace(" ", "")
	for key, standard_name in INSTITUTE_STANDARD_MAP.items():
		if compact == key.replace(" ", ""):
			return standard_name
	if name.startswith("gec "):
		return f"Government Engineering College, {name.split(' ', 1)[1].title()}"
	if name.startswith("gec") and len(name.split()) > 1:
		return f"Government Engineering College, {name.split(' ', 1)[1].title()}"
	if name.startswith("government engineering college"):
		suffix = name.replace("government engineering college", "").strip(" ,")
		return f"Government Engineering College, {suffix.title()}" if suffix else "Government Engineering College"
	return re.sub(r"\s+", " ", name).title()


def clean_main_admission_data_in_place():
	"""Clean and standardize the main admission CSV directly in place."""
	dataset = pd.read_csv(DATA_FILE)

	for column in ["category", "quota", "admission_field", "course_name", "institute_name"]:
		if column in dataset.columns:
			dataset[column] = dataset[column].fillna("")

	if "category" in dataset.columns:
		dataset["category"] = dataset["category"].apply(standardize_category)
	if "quota" in dataset.columns:
		dataset["quota"] = dataset["quota"].apply(standardize_quota)
	if "admission_field" in dataset.columns:
		dataset["admission_field"] = dataset["admission_field"].apply(standardize_branch)
	if "course_name" in dataset.columns:
		dataset["course_name"] = dataset["course_name"].apply(standardize_branch)
	if "institute_name" in dataset.columns:
		dataset["institute_name"] = dataset["institute_name"].apply(standardize_institute_name)

	dataset = dataset[
		(dataset["category"].astype(str).str.strip() != "")
		& (dataset["quota"].astype(str).str.strip() != "")
	].copy()

	dataset.to_csv(DATA_FILE, index=False)
	return len(dataset)


def load_institute_search_dataset():
	"""Build a search-friendly dataset from the admissions CSV and institute master CSV."""
	admissions = pd.read_csv(DATA_FILE)
	for column in ["course_name", "admission_field", "institute_name"]:
		if column in admissions.columns:
			admissions[column] = admissions[column].fillna("")
	admissions["course_name"] = admissions["course_name"].apply(standardize_branch)
	admissions["admission_field"] = admissions["admission_field"].apply(standardize_branch)
	admissions["institute_name"] = admissions["institute_name"].apply(standardize_institute_name)
	master_file = INSTITUTE_MASTER_FILE_V2 if INSTITUTE_MASTER_FILE_V2.exists() else INSTITUTE_MASTER_FILE
	if not master_file.exists():
		search_data = admissions.copy()
		search_data["hostel_available"] = ""
		search_data["boys_hostel"] = ""
		search_data["girls_hostel"] = ""
		search_data["official_website"] = ""
		search_data["city"] = search_data.get("institute_name", "").apply(infer_city)
		return search_data

	institute_master = pd.read_csv(master_file)
	institute_master["institute_name"] = institute_master["institute_name"].fillna("").apply(standardize_institute_name)
	admissions["join_key"] = admissions["institute_name"].astype(str).map(normalize_text)
	institute_master["join_key"] = institute_master["institute_name"].astype(str).map(normalize_text)
	merge_columns = ["join_key", "hostel_available", "boys_hostel", "girls_hostel", "official_website"]
	merge_columns = [column for column in merge_columns if column in institute_master.columns]
	merged = admissions.merge(
		institute_master[merge_columns],
		on="join_key",
		how="left",
	)
	for column in ["hostel_available", "boys_hostel", "girls_hostel", "official_website"]:
		if column not in merged.columns:
			merged[column] = ""
		merged[column] = merged[column].fillna("")
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
