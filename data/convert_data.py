from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "acpc_admission_data.csv"


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").strip()


def to_int(value):
    if pd.isna(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number.is_integer():
        return int(number)
    return int(number)


def normalize_category(value):
    category = normalize_text(value).upper().replace(" ", "")
    mapping = {
        "OP": "OPEN",
        "OPEN": "OPEN",
        "GEN": "OPEN",
        "GENERAL": "OPEN",
        "EW": "EWS",
        "EWS": "EWS",
        "SE": "SEBC",
        "SEBC": "SEBC",
        "SC": "SC",
        "ST": "ST",
        "TF": "TFWS",
        "TFW": "TFWS",
        "TFWS": "TFWS",
        "NRI": "NRI",
    }
    return mapping.get(category, category)


def academic_year_from_filename(file_name):
    if file_name.startswith("22_23"):
        return "2022-2023"
    if file_name.startswith("23_24"):
        return "2023-2024"
    if file_name.startswith("24_25"):
        return "2024-2025"
    return ""


def flatten_columns(columns):
    flattened = []
    for column in columns:
        if isinstance(column, tuple):
            parts = [normalize_text(part) for part in column if normalize_text(part)]
            flattened.append("_".join(parts) if parts else "")
        else:
            flattened.append(normalize_text(column))
    return flattened


def add_record(records, **kwargs):
    records.append(
        {
            "source_file": kwargs.get("source_file", ""),
            "source_sheet": kwargs.get("source_sheet", ""),
            "academic_year": kwargs.get("academic_year", ""),
            "program_type": kwargs.get("program_type", ""),
            "institute_name": kwargs.get("institute_name", ""),
            "course_name": kwargs.get("course_name", ""),
            "category": kwargs.get("category", ""),
            "quota": kwargs.get("quota", ""),
            "first_rank": kwargs.get("first_rank", ""),
            "last_rank": kwargs.get("last_rank", ""),
            "rank": kwargs.get("rank", ""),
            "admission_field": kwargs.get("admission_field", ""),
        }
    )


def parse_22_23_rank_sheet(file_name, sheet_name, records):
    df = pd.read_excel(BASE_DIR / file_name, sheet_name=sheet_name, header=[4, 5])
    category_columns = ["OP", "SC", "ST", "SE", "EWS"]

    institute_column = next(
        (column for column in df.columns if normalize_text(column[0]) == "Institute Name"),
        None,
    )
    course_column = next(
        (column for column in df.columns if normalize_text(column[0]) == "Degree Eligible Branch"),
        None,
    )

    for _, row in df.iterrows():
        institute_name = normalize_text(row[institute_column]) if institute_column else ""
        course_name = normalize_text(row[course_column]) if course_column else ""
        if not institute_name or not course_name:
            continue

        for category in category_columns:
            rank_column = next(
                (
                    column
                    for column in df.columns
                    if normalize_text(column[0]) == category and "Merit No" in normalize_text(column[1])
                ),
                None,
            )
            rank = to_int(row[rank_column]) if rank_column else None
            if rank is None:
                continue
            add_record(
                records,
                source_file=file_name,
                source_sheet=sheet_name,
                academic_year=academic_year_from_filename(file_name),
                program_type="D2D",
                institute_name=institute_name,
                course_name=course_name,
                category=normalize_category(category),
                quota="D2D",
                first_rank=rank,
                last_rank=rank,
                rank=rank,
                admission_field=course_name,
            )


def parse_23_24_d2d_sheet(file_name, sheet_name, records):
    df = pd.read_excel(BASE_DIR / file_name, sheet_name=sheet_name, header=0)

    current_institute = ""
    category_columns = {
        2: "OPEN",
        5: "SC",
        7: "ST",
        9: "SEBC",
        12: "EWS",
        15: "TFWS",
    }

    for _, row in df.iterrows():
        first_cell = normalize_text(row.iloc[0])
        other_values = row.iloc[1:]

        if first_cell and other_values.isna().all():
            current_institute = first_cell
            continue

        course_name = first_cell
        if not current_institute or not course_name:
            continue

        for column_index, category in category_columns.items():
            first_rank = to_int(row.iloc[column_index]) if column_index < len(row) else None
            last_rank = to_int(row.iloc[column_index + 1]) if column_index + 1 < len(row) else None
            if first_rank is None and last_rank is None:
                continue

            add_record(
                records,
                source_file=file_name,
                source_sheet=sheet_name,
                academic_year=academic_year_from_filename(file_name),
                program_type="D2D",
                institute_name=current_institute,
                course_name=course_name,
                category=normalize_category(category),
                quota="D2D",
                first_rank=first_rank if first_rank is not None else "",
                last_rank=last_rank if last_rank is not None else "",
                rank=last_rank if last_rank is not None else first_rank,
                admission_field=course_name,
            )


def parse_24_25_d2d_sheet(file_name, sheet_name, records):
    df = pd.read_excel(BASE_DIR / file_name, sheet_name=sheet_name, header=4)
    for _, row in df.iterrows():
        institute_name = normalize_text(row.iloc[1])
        course_name = normalize_text(row.iloc[3])
        quota = normalize_text(row.iloc[4])
        category = normalize_category(row.iloc[5])
        first_rank = to_int(row.iloc[7]) if len(row) > 7 else None
        last_rank = to_int(row.iloc[9]) if len(row) > 9 else None

        if not institute_name or not course_name or not category:
            continue

        if first_rank is None and last_rank is None:
            continue

        add_record(
            records,
            source_file=file_name,
            source_sheet=sheet_name,
            academic_year=academic_year_from_filename(file_name),
            program_type="D2D",
            institute_name=institute_name,
            course_name=course_name,
            category=category,
            quota=quota,
            first_rank=first_rank if first_rank is not None else "",
            last_rank=last_rank if last_rank is not None else "",
            rank=last_rank if last_rank is not None else first_rank,
            admission_field=course_name,
        )


def parse_23_24_deg_sheet(file_name, sheet_name, records):
    df = pd.read_excel(BASE_DIR / file_name, sheet_name=sheet_name, header=4)
    for _, row in df.iterrows():
        institute_name = normalize_text(row.iloc[0])
        course_name = normalize_text(row.iloc[1])
        category = normalize_category(row.iloc[3])
        quota = normalize_text(row.iloc[4])
        last_rank = to_int(row.iloc[5]) if len(row) > 5 else None

        if not institute_name or not course_name or not category or last_rank is None:
            continue

        add_record(
            records,
            source_file=file_name,
            source_sheet=sheet_name,
            academic_year=academic_year_from_filename(file_name),
            program_type="DEG",
            institute_name=institute_name,
            course_name=course_name,
            category=category,
            quota=quota,
            first_rank="",
            last_rank=last_rank,
            rank=last_rank,
            admission_field=course_name,
        )


def parse_24_25_deg_sheet(file_name, sheet_name, records):
    df = pd.read_excel(BASE_DIR / file_name, sheet_name=sheet_name, header=2)
    for _, row in df.iterrows():
        institute_name = normalize_text(row.iloc[0])
        course_name = normalize_text(row.iloc[1])
        category = normalize_category(row.iloc[2])
        quota = normalize_text(row.iloc[3])
        first_rank = to_int(row.iloc[5]) if len(row) > 5 else None
        last_rank = to_int(row.iloc[6]) if len(row) > 6 else None

        if not institute_name or not course_name or not category:
            continue

        if first_rank is None and last_rank is None:
            continue

        add_record(
            records,
            source_file=file_name,
            source_sheet=sheet_name,
            academic_year=academic_year_from_filename(file_name),
            program_type="DEG",
            institute_name=institute_name,
            course_name=course_name,
            category=category,
            quota=quota,
            first_rank=first_rank if first_rank is not None else "",
            last_rank=last_rank if last_rank is not None else "",
            rank=last_rank if last_rank is not None else first_rank,
            admission_field=course_name,
        )


def build_common_csv():
    records = []

    for file_path in sorted(BASE_DIR.glob("*.xlsx")):
        file_name = file_path.name
        print(f"Processing {file_name}...")

        if file_name in {"22_23_D2D.xlsx", "22_23_DEG.xlsx"}:
            for sheet_name in pd.ExcelFile(file_path).sheet_names:
                parse_22_23_rank_sheet(file_name, sheet_name, records)
        elif file_name == "23_24_D2D.xlsx":
            for sheet_name in pd.ExcelFile(file_path).sheet_names:
                parse_23_24_d2d_sheet(file_name, sheet_name, records)
        elif file_name == "24_25_D2D.xlsx":
            for sheet_name in pd.ExcelFile(file_path).sheet_names:
                parse_24_25_d2d_sheet(file_name, sheet_name, records)
        elif file_name == "23_24_DEG.xlsx":
            for sheet_name in pd.ExcelFile(file_path).sheet_names:
                parse_23_24_deg_sheet(file_name, sheet_name, records)
        elif file_name == "24_25_DEG.xlsx":
            for sheet_name in pd.ExcelFile(file_path).sheet_names:
                parse_24_25_deg_sheet(file_name, sheet_name, records)

    final_df = pd.DataFrame(records)
    if final_df.empty:
        final_df = pd.DataFrame(
            columns=[
                "source_file",
                "source_sheet",
                "academic_year",
                "program_type",
                "institute_name",
                "course_name",
                "category",
                "quota",
                "first_rank",
                "last_rank",
                "rank",
                "admission_field",
            ]
        )

    final_df = final_df.dropna(how="all").drop_duplicates()
    final_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved {len(final_df)} rows to {OUTPUT_FILE.name}")


if __name__ == "__main__":
    build_common_csv()