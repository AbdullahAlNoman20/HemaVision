# processing/pdf_extractor.py
import re
import pdfplumber
import pandas as pd

COLUMNS = ["Name", "Events", "%Parent", "%Grandparent", "%Total", "SSC-A Mean", "FSC-A Mean"]

ROW_PATTERN = re.compile(
    r"(.+?)\s+([\d,]+)\s+([\d.]+)?\s*([\d.]+)?\s*([\d.]+)?\s+([\d,]+)\s+([\d,]+)"
)


class PDFExtractionError(Exception):
    pass


def extract_statistics_table(pdf_path: str) -> pd.DataFrame:
    if not pdf_path.lower().endswith(".pdf"):
        raise PDFExtractionError("Invalid file type.")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) < 2:
                raise PDFExtractionError("Expected report page not found.")
            text = pdf.pages[1].extract_text() or ""
    except Exception as exc:
        raise PDFExtractionError(f"Unable to read PDF: {exc}") from exc

    if "Statistics" not in text:
        raise PDFExtractionError(
            "Statistics section not found in report. "
            "সঠিক ফাইল কিনা চেক করুন — এটা raw flow cytometry ল্যাব রিপোর্ট হতে হবে, "
            "প্রজেক্ট রাইটআপ বা প্রসেসড রিপোর্ট না।"
        )

    stats_section = text.split("Statistics")[-1]
    rows = []

    for raw_line in stats_section.split("\n"):
        line = re.sub(r"\s+", " ", raw_line).strip().replace("***", "")
        if not line:
            continue

        match = ROW_PATTERN.match(line)
        if match:
            rows.append(match.groups())

    if not rows:
        raise PDFExtractionError("No parseable statistics rows found.")

    return pd.DataFrame(rows, columns=COLUMNS)