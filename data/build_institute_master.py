from __future__ import annotations

from base64 import b64decode
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent
PDF_FILE = BASE_DIR / "ai.pdf"
ADMISSION_FILE = BASE_DIR / "acpc_admission_data.csv"
INSTITUTE_MASTER_FILE = BASE_DIR / "institute_master.csv"
ENRICHED_FILE = BASE_DIR / "acpc_admission_enriched.csv"

IGNORED_LINES = {"institute_name", "51b28e2d-42b5-40e9-b3fe-2d73761a17b5"}
BLOCKED_DOMAINS = (
	"bing.com",
	"google.com",
	"collegedunia.com",
	"shiksha.com",
	"careers360.com",
	"collegedekho.com",
	"youtube.com",
	"facebook.com",
	"instagram.com",
	"linkedin.com",
)

MANUAL_WEBSITE_MAP = {
	"BVM (GIA), VVNagar": "https://bvmengineering.ac.in",
	"BVM (SFI), VVNagar": "https://bvmengineering.ac.in",
	"MSU (GIA), Vadodara": "https://msubaroda.ac.in",
	"DDU (GIA), Nadiad": "https://www.ddu.ac.in",
	"DDU (SFI), Nadiad": "https://www.ddu.ac.in",
	"LDCE, Ahmedabad": "https://ldce.ac.in",
	"VGEC, Ahmedabad": "https://vgecg.ac.in",
	"PDEU, Raisan": "https://www.pdeu.ac.in",
	"Nirma Uni, Ahmedabad": "https://nirmauni.ac.in",
	"LJIET, Ahmedabad": "https://www.ljiet.ac.in",
	"Adani, Ahmedabad": "https://adaniuni.ac.in",
	"Adani Institute Of Infrastructure Engineering, Ahmedabad": "https://adaniuni.ac.in",
	"Aditya, Ahmedabad": "https://silveroakuni.ac.in",
	"Ahmedabad Institute Of Tech, Ahmedabad": "https://aitindia.in",
	"AIT, Ahmedabad": "https://aitindia.in",
	"Atmiya, Rajkot": "https://atmiyauniversity.ac.in",
	"ATMIYA UNIVERSITY, FACULTY OF ENGINEERING AND TECHNOLOGY, RAJKOT": "https://atmiyauniversity.ac.in",
	"Charotar University of Science & Technology (CHARUSAT) - Chandubhai S Patel Institute Of Technology (CSPIT), Changa": "https://www.charusat.ac.in",
	"Charotar University of Science & Technology (CHARUSAT) - Devang Patel Institute of Advance Technology And Research (DEPSTAR), Changa": "https://www.charusat.ac.in",
	"CGPIT, Tarsadi": "https://www.charusat.ac.in",
	"CPIT, Changa": "https://www.charusat.ac.in",
	"DPIATR, Changa": "https://www.charusat.ac.in",
	"GIT, Gandhinagar": "https://git.org.in",
	"Ganpat Uni. UVPCE, Mehsana": "https://ganpatuniversity.ac.in",
	"Ganpat Uni. ICT, Mehsana": "https://ganpatuniversity.ac.in",
	"IAR, Gandhinagar": "https://iar.ac.in",
	"Indus Uni., Ahmedabad": "https://indusuni.ac.in",
	"Institute Of Technology, Nirma University Of Science & Technology, Ahmedabad": "https://nirmauni.ac.in",
	"Institute of Infrastructure,Technology,Research and Management(IITRAM),Ahmedabad": "https://www.iitram.ac.in",
	"Faculty of Engineering & Technology- GLS University, Ahmedabad": "https://www.glsuniversity.ac.in",
	"Faculty of Technology, CEPT University, Ahmedabad": "https://cept.ac.in",
	"Faculty of Engineering & Technology- Sigma University, Bakrol, Vadodara": "https://sigmauniversity.ac.in",
	"Parul Institute of Engineering & Technology, Waghodia, Vadodara": "https://paruluniversity.ac.in",
	"Parul Institute of Technology, Waghodia, Vadodara": "https://paruluniversity.ac.in",
	"P.P. Savani School of Engineering, P.P. Savani University, Kosamba": "https://www.ppsavani.ac.in",
	"School of Engineering, Plastindia International University, Vapi": "https://www.piuvapi.ac.in",
	"Unitedworld, Uvarsad": "https://unitedworld.edu.in",
	"Unitedworld Institute of Technology, UVARSAD, GANDHINAGAR": "https://unitedworld.edu.in",
	"VIE, Kotambi": "https://www.vierct.ac.in",
	"VVP, Rajkot": "https://www.vveec.ac.in",
	"V.V.P. Engineering College, Rajkot": "https://www.vveec.ac.in",
	"Vishwakarma Government Engineering College, Chandkheda,Gandhinagar": "https://vgecg.ac.in",
	"VISHWAKARMA GOVERNMENT ENGINEERING COLLEGE, CHANDKHEDA,GANDHINAGAR": "https://vgecg.ac.in",
	"LDCE, Ahmedabad": "https://ldce.ac.in",
	"L. D. College of Engineering": "https://ldce.ac.in",
	"L.D.College Of Engineering, Ahmedabad": "https://ldce.ac.in",
	"L.D.COLLEGE OF ENGINEERING, AHMEDABAD": "https://ldce.ac.in",
	"B.H.GARDI COLLEGE OF ENGG. & TECHNOLOGY , RAJKOT": "https://www.bhgardi.edu.in",
	"B.H.Gardi College Of Engg. & Technology , Rajkot": "https://www.bhgardi.edu.in",
	"C. K. Pithawala College Of Engg. & Tech., Surat": "https://ckpcet.ac.in",
	"CKPCET, Surat": "https://ckpcet.ac.in",
	"Darshan, Rajkot": "https://darshan.ac.in",
	"Darshan Institute Of Engg. & Tech., Rajkot-Morbi Highway, Hadala": "https://darshan.ac.in",
	"G.H.Patel College Of Engg. & Tech. , V. V. Nagar": "https://gcet.ac.in",
	"G.H.PATEL COLLEGE OF ENGG. & TECH. , V. V. NAGAR": "https://gcet.ac.in",
	"GEC, Surat": "https://gecsurat.gujarat.gov.in",
	"GEC, Bharuch": "https://gecbh.ac.in",
	"GEC, Bhavnagar": "https://gecbhavnagar.ac.in",
	"GEC, Bhuj": "https://gecbhuj.ac.in",
	"GEC, Dahod": "https://gecdahod.ac.in",
	"GEC, Godhra": "https://gecgodhra.ac.in",
	"GEC, Modasa": "https://gecmodasa.ac.in",
	"GEC, Palanpur": "https://gecpalanpur.ac.in",
	"GEC, Patan": "https://gecpatan.ac.in",
	"GEC, Rajkot": "https://gecrajkot.ac.in",
	"GEC, Gandhinagar": "https://gecgandhinagar.ac.in",
	"GEC, Valsad": "https://gecvalsad.ac.in",
	"GEC, Bhuj": "https://gecbhuj.ac.in",
	"GEC, Modasa": "https://gecmodasa.ac.in",
	"GEC, Patan": "https://gecpatan.ac.in",
	"GEC, Rajkot": "https://gecrajkot.ac.in",
	"GEC, Valsad": "https://gecvalsad.ac.in",
}

QUERY_HINTS = {
	"BVM (GIA), VVNagar": "Birla Vishvakarma Maha Vidhyalaya V V Nagar official website",
	"BVM (SFI), VVNagar": "Birla Vishvakarma Maha Vidhyalaya V V Nagar official website",
	"MSU (GIA), Vadodara": "M S University Vadodara Faculty of Technology official website",
	"DDU (GIA), Nadiad": "Dharamsinh Desai University Nadiad official website",
	"DDU (SFI), Nadiad": "Dharamsinh Desai University Nadiad official website",
	"LDCE, Ahmedabad": "L D College of Engineering Ahmedabad official website",
	"VGEC, Ahmedabad": "Vishwakarma Government Engineering College Ahmedabad official website",
	"PDEU, Raisan": "Pandit Deendayal Energy University Gandhinagar official website",
	"Nirma Uni, Ahmedabad": "Nirma University Ahmedabad Institute of Technology official website",
	"LJIET, Ahmedabad": "L J Institute of Engineering and Technology Ahmedabad official website",
	"Adani, Ahmedabad": "Adani University Faculty of Engineering Sciences and Technology Ahmedabad official website",
	"Aditya, Ahmedabad": "Aditya Silver Oak Institute of Technology Ahmedabad official website",
	"GEC, Surat": "Government Engineering College Surat official website",
	"GEC, Bharuch": "Government Engineering College Bharuch official website",
	"GEC, Bhavnagar": "Government Engineering College Bhavnagar official website",
	"GEC, Bhuj": "Government Engineering College Bhuj official website",
	"GEC, Dahod": "Government Engineering College Dahod official website",
	"GEC, Godhra": "Government Engineering College Godhra official website",
	"GEC, Modasa": "Government Engineering College Modasa official website",
	"GEC, Palanpur": "Government Engineering College Palanpur official website",
	"GEC, Patan": "Government Engineering College Patan official website",
	"GEC, Rajkot": "Government Engineering College Rajkot official website",
	"GEC, Gandhinagar": "Government Engineering College Gandhinagar official website",
	"GEC, Valsad": "Government Engineering College Valsad official website",
}


def normalize_key(value: str) -> str:
	return "".join(character for character in value.casefold() if character.isalnum())


def extract_institute_names(pdf_path: Path) -> list[str]:
	reader = PdfReader(str(pdf_path))
	names = []
	for page in reader.pages:
		text = page.extract_text() or ""
		for line in text.splitlines():
			line = line.strip()
			if not line or line.startswith("Page ") or line in IGNORED_LINES:
				continue
			if any(character.isdigit() for character in line):
				continue
			if len(line) < 3:
				continue
			names.append(line)
	return list(dict.fromkeys(names))
def normalize_official_url(url: str) -> str:
	parsed = urlparse(url)
	if not parsed.scheme or not parsed.netloc:
		return ""
	return f"{parsed.scheme}://{parsed.netloc}"


def is_blocked_url(url: str) -> bool:
	parsed = urlparse(url)
	domain = parsed.netloc.casefold()
	return any(blocked in domain for blocked in BLOCKED_DOMAINS)


def allowed_official_domain(url: str) -> bool:
	domain = urlparse(url).netloc.casefold()
	return any(domain.endswith(suffix) for suffix in (".ac.in", ".edu", ".edu.in")) or domain in {
		"adaniuni.ac.in",
		"pdeu.ac.in",
		"bvmengineering.ac.in",
		"vgecg.ac.in",
		"ldce.ac.in",
		"msubaroda.ac.in",
		"ddu.ac.in",
		"nirmauni.ac.in",
		"ljiet.ac.in",
		"charusat.ac.in",
		"ganpatuniversity.ac.in",
		"iitram.ac.in",
		"atmiyauniversity.ac.in",
		"paruluniversity.ac.in",
		"sigmauniversity.ac.in",
		"glsuniversity.ac.in",
		"ckpcet.ac.in",
		"darshan.ac.in",
	}


def lookup_official_website(name: str) -> str:
	return MANUAL_WEBSITE_MAP.get(name, "")


def infer_hostel_availability(name: str) -> str:
	text = name.casefold()
	positive_keywords = (
		"university",
		"college",
		"institute",
		"engineering",
		"technology",
		"school of engineering",
		"polytechnic",
	)
	return "Yes" if any(keyword in text for keyword in positive_keywords) else "No"


def build_institute_master() -> pd.DataFrame:
	names = extract_institute_names(PDF_FILE)
	print(f"Found {len(names)} unique institute names in PDF")

	rows = [
		{
			"institute_name": name,
			"hostel_available": infer_hostel_availability(name),
			"official_website": lookup_official_website(name),
		}
		for name in names
	]

	master = pd.DataFrame(rows).sort_values("institute_name").drop_duplicates(subset=["institute_name"])
	master.to_csv(INSTITUTE_MASTER_FILE, index=False)
	print(f"Saved institute master to {INSTITUTE_MASTER_FILE}")
	return master


def build_enriched_dataset(master: pd.DataFrame) -> pd.DataFrame:
	admissions = pd.read_csv(ADMISSION_FILE)
	master = master.copy()
	master["join_key"] = master["institute_name"].map(normalize_key)
	admissions["join_key"] = admissions["institute_name"].astype(str).map(normalize_key)

	merged = admissions.merge(master[["join_key", "hostel_available", "official_website"]], on="join_key", how="left")
	merged["hostel_available"] = merged["hostel_available"].fillna("Yes")
	merged["official_website"] = merged["official_website"].fillna("")
	merged = merged.drop(columns=["join_key"])
	merged.to_csv(ENRICHED_FILE, index=False)
	print(f"Saved enriched admissions data to {ENRICHED_FILE}")
	return merged


def main():
	master = build_institute_master()
	build_enriched_dataset(master)


if __name__ == "__main__":
	main()