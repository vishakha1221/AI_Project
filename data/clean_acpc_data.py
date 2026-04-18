from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "acpc_admission_data.csv"
INSTITUTE_MASTER_FILE = BASE_DIR / "institute_master.csv"
OUTPUT_FILE = BASE_DIR / "acpc_cleaned_data.csv"


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
}


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


def clean_text(value):
    """Normalize text for matching."""
    if pd.isna(value):
        return ""
    text = str(value).lower().replace(".", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def title_case_keep_ampersand(text):
    """Convert a cleaned branch name back to a readable standard format."""
    return re.sub(r"\s+", " ", text).strip().title().replace(" & ", " & ")


def standardize_branch(value):
    """Convert branch aliases into one standard label."""
    normalized = clean_text(value)
    if not normalized:
        return ""

    compact = normalized.replace(" ", "")
    if normalized in BRANCH_STANDARD_MAP:
        return BRANCH_STANDARD_MAP[normalized]

    if normalized == "it" or "information technology" in normalized:
        return "Information Technology"

    if "computer science" in normalized:
        if "artificial intelligence" in normalized and "machine learning" in normalized:
            return "Computer Science & Engineering (Artificial Intelligence and Machine Learning)"
        if "data science" in normalized:
            return "Computer Science & Engineering (Data Science)"
        if "cyber security" in normalized or "cybersecurity" in normalized:
            return "Computer Science & Engineering (Cyber Security)"
        if "cloud computing" in normalized:
            return "Computer Science & Engineering (Cloud Computing)"
        if "design" in normalized:
            return "Computer Science & Design"
        if "engineering" in normalized:
            return "Computer Science & Engineering"

    if "computer" in normalized and ("engg" in normalized or "engineering" in normalized or compact == "computer"):
        return "Computer Engineering"

    if "civil" in normalized:
        if "infrastructure" in normalized:
            return "Civil & Infrastructure Engineering"
        return "Civil Engineering"

    if "mechanical" in normalized:
        return "Mechanical Engineering"

    if "electrical" in normalized:
        return "Electrical Engineering"

    if "electronics and communication" in normalized or "electronics & communication" in normalized:
        return "Electronics & Communication Engineering"

    if "electronics" in normalized:
        return "Electronics Engineering"

    if "production" in normalized:
        return "Production Engineering"

    if "automobile" in normalized:
        return "Automobile Engineering"

    if "aeronautical" in normalized:
        return "Aeronautical Engineering"

    if "aerospace" in normalized:
        return "Aerospace Engineering"

    if "agricultural" in normalized:
        return "Agricultural Engineering"

    if "biotechnology" in normalized:
        return "Biotechnology Engineering"

    if "chemical" in normalized:
        return "Chemical Engineering"

    if "textile" in normalized:
        return "Textile Engineering"

    if "food processing" in normalized or "food technology" in normalized:
        return "Food Processing Technology"

    if "environment" in normalized:
        return "Environmental Engineering"

    if "mechatronics" in normalized:
        return "Mechatronics Engineering"

    if "power electronics" in normalized:
        return "Power Electronics"

    return title_case_keep_ampersand(normalized)


def extract_city(institute_name):
    """Extract city from institute name using simple keyword rules."""
    normalized = clean_text(institute_name)
    for keyword, city in CITY_RULES:
        if keyword in normalized:
            return city
    return "Other"


def clean_institute_name(value):
    """Keep the institute name readable while removing extra spaces and dots."""
    if pd.isna(value):
        return ""
    text = str(value).replace(".", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def merge_institute_details(dataframe):
    """Add hostel and website details from the institute master."""
    if not INSTITUTE_MASTER_FILE.exists():
        dataframe["hostel_available"] = ""
        dataframe["official_website"] = ""
        return dataframe

    institute_master = pd.read_csv(INSTITUTE_MASTER_FILE)
    institute_master["lookup_key"] = institute_master["institute_name"].astype(str).map(clean_text)
    institute_master = institute_master.drop_duplicates(subset=["lookup_key"])

    dataframe["lookup_key"] = dataframe["institute_name"].astype(str).map(clean_text)
    merged = dataframe.merge(
        institute_master[["lookup_key", "hostel_available", "official_website"]],
        on="lookup_key",
        how="left",
    )
    merged["hostel_available"] = merged["hostel_available"].fillna("")
    merged["official_website"] = merged["official_website"].fillna("")
    merged = merged.drop(columns=["lookup_key"])
    return merged


def clean_dataset():
    """Load, standardize, deduplicate, and save the cleaned admission dataset."""
    data = pd.read_csv(INPUT_FILE)

    for column in ["course_name", "admission_field", "institute_name"]:
        if column in data.columns:
            data[column] = data[column].astype(str).map(lambda value: value if value.lower() != "nan" else "")

    # Clean the text columns safely.
    data["course_name"] = data["course_name"].apply(standardize_branch)
    data["admission_field"] = data["admission_field"].apply(standardize_branch)
    data["institute_name"] = data["institute_name"].apply(clean_institute_name)

    # Add city for easy filtering in the UI.
    data["city"] = data["institute_name"].apply(extract_city)

    # Merge hostel and official website details.
    data = merge_institute_details(data)

    # Handle missing values safely.
    data["city"] = data["city"].fillna("Other")
    data["course_name"] = data["course_name"].fillna("")
    data["admission_field"] = data["admission_field"].fillna("")
    data["institute_name"] = data["institute_name"].fillna("")

    # Keep ML columns consistent after cleaning.
    data = data[data["course_name"].astype(str).str.strip() != ""]
    data = data[data["admission_field"].astype(str).str.strip() != ""]

    # Remove duplicate rows after cleaning.
    data = data.drop_duplicates()

    # Save the cleaned dataset.
    data.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved cleaned file to {OUTPUT_FILE}")
    print(f"Rows after cleaning: {len(data)}")


if __name__ == "__main__":
    clean_dataset()