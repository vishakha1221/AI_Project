from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "acpc_admission_data.csv"
OUTPUT_FILE = BASE_DIR / "acpc_final_cleaned.csv"


STANDARD_NAME_MAP = {
    "gec dahod": "Government Engineering College, Dahod",
    "government engineering college dahod": "Government Engineering College, Dahod",
    "gec ahmedabad": "Government Engineering College, Ahmedabad",
    "ld college of engineering ahmedabad": "L.D. College of Engineering, Ahmedabad",
    "ldce ahmedabad": "L.D. College of Engineering, Ahmedabad",
    "bvm vvnagar": "Birla Vishvakarma Mahavidyalaya, V.V. Nagar",
    "birla vishvakarma mahavidyalaya": "Birla Vishvakarma Mahavidyalaya, V.V. Nagar",
}


def clean_text(value):
    """Convert text to a simple normalized form for matching."""
    if pd.isna(value):
        return ""
    text = str(value).lower()
    text = text.replace(",", " ")
    text = text.replace(".", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def to_title_case(value):
    """Fallback formatting when a name is not found in the map."""
    text = re.sub(r"\s+", " ", value).strip()
    return text.title()


def standardize_institute_name(value):
    """Map different versions of the same college to one standard name."""
    normalized = clean_text(value)
    if not normalized:
        return ""

    if normalized in STANDARD_NAME_MAP:
        return STANDARD_NAME_MAP[normalized]

    # Try a second match without commas or dots for slightly different spellings.
    compact = normalized.replace(" ", "")
    for key, standard_name in STANDARD_NAME_MAP.items():
        if compact == key.replace(" ", ""):
            return standard_name

    return to_title_case(normalized)


def clean_dataset():
    """Load the CSV, clean institute names, remove duplicates, and save one final file."""
    data = pd.read_csv(INPUT_FILE)

    if "institute_name" not in data.columns:
        raise ValueError("The CSV does not contain an institute_name column.")

    # Keep missing values safe before cleaning.
    data["institute_name"] = data["institute_name"].fillna("")

    # Standardize institute names.
    data["institute_name"] = data["institute_name"].apply(standardize_institute_name)

    # Remove duplicate rows after name cleanup.
    data = data.drop_duplicates()

    # Save only the final cleaned CSV.
    data.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved cleaned data to {OUTPUT_FILE}")
    print(f"Rows after cleaning: {len(data)}")


if __name__ == "__main__":
    clean_dataset()