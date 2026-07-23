# app.py
import os
import uuid
import json
import logging
from datetime import datetime
from flask import Flask, render_template, flash, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from config import Config
from processing.pdf_extractor import extract_statistics_table, PDFExtractionError
from processing.marker_aggregator import aggregate_tube
from processing.interpreter import interpret_results
from processing.chart_builder import build_vega_lite_spec

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UploadForm(FlaskForm):
    report = FileField(
        "Blood Test Report (PDF)",
        validators=[
            FileRequired(message="ফাইল সিলেক্ট করুন।"),
            FileAllowed(["pdf"], message="শুধুমাত্র PDF ফাইল আপলোড করা যাবে।"),
        ],
    )


DOCTOR_PROFILE = {
    "name": "Assoc. Prof. Dr. Momena Begum",
    "designation": "Associate Professor, Pediatric Hematology & Oncology",
    "institute": "Bangladesh Medical University",
    "location": "Shahbagh, Dhaka-1000, Bangladesh",
    "photo": "img/dr-momena-begum.jpg",
    "expertise": [
        "Pediatric Leukaemia Diagnosis",
        "Flow Cytometry Immunophenotyping",
        "Bone Marrow Failure Syndromes",
        "Pediatric Hemato-Oncology Consultation",
    ],
}

COMING_SOON_SERVICES = [
    {"title": "AI Radiology Assistant", "desc": "X-ray ও CT স্ক্যান বিশ্লেষণ", "icon": "scan"},
    {"title": "Cardiology AI Screening", "desc": "ECG প্যাটার্ন রিস্ক ডিটেকশন", "icon": "heart"},
    {"title": "Pathology Report AI", "desc": "হিস্টোপ্যাথলজি রিপোর্ট সহায়তা", "icon": "flask"},
    {"title": "Genomics Insight Engine", "desc": "জেনেটিক মার্কার বিশ্লেষণ", "icon": "dna"},
]


@app.route("/", methods=["GET"])
def home():
    return render_template(
        "home.html",
        doctor=DOCTOR_PROFILE,
        services=COMING_SOON_SERVICES,
    )


@app.route("/analyze", methods=["GET"])
def analyze():
    form = UploadForm()
    return render_template("index.html", form=form, doctor=DOCTOR_PROFILE)


@app.route("/process", methods=["POST"])
def process():
    form = UploadForm()

    if not form.validate_on_submit():
        flash("ফাইল ভ্যালিডেশন ব্যর্থ হয়েছে। আবার চেষ্টা করুন।")
        return redirect(url_for("analyze"))

    file = form.report.data
    filename = secure_filename(file.filename)

    if not filename:
        flash("অবৈধ ফাইলনেম।")
        return redirect(url_for("analyze"))

    safe_name = f"{uuid.uuid4().hex}_{filename}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)

    try:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(save_path)

        raw_df = extract_statistics_table(save_path)

        tube1 = aggregate_tube(
            raw_df,
            tube_prefix="Tube_001",
            marker_groups=[
                ("CD79a PE-A", "CD19 PE-Cy7-A"),
                ("CD7 APC-A", "cyCD3 V450-A"),
                ("Anti-MPO FITC-A", "CD34 PerCP-Cy5.5-A"),
            ],
            tube_label="Tube 001",
        )

        tube2 = aggregate_tube(
            raw_df,
            tube_prefix="Tube_002",
            marker_groups=[
                ("CD13 PE-A", "CD33 APC-R700-A"),
                ("CD10 APC-A", "CD5 PerCP-Cy5.5-A"),
                ("CD117 PE-Cy7-A", "Anti-HLA-DR V450-A"),
            ],
            tube_label="Tube 002",
        )

        combined_df = tube1._append(tube2, ignore_index=True) if hasattr(tube1, "_append") else tube1.append(tube2, ignore_index=True)
        interpretation = interpret_results(combined_df)
        chart_spec = build_vega_lite_spec(combined_df)

        marker_summary = (
            combined_df.groupby("Marker", sort=False)["Sum Percent"]
            .first()
            .reset_index()
            .to_dict(orient="records")
        )

        return render_template(
            "report.html",
            doctor=DOCTOR_PROFILE,
            markers=marker_summary,
            interpretation=interpretation,
            report_id=f"BMU-HEM-{datetime.now().strftime('%Y%m%d')}",
            report_date=datetime.now().strftime("%d %B %Y"),
            chart_spec=json.dumps(chart_spec),
        )

    except PDFExtractionError as e:
        logger.warning("PDF extraction failed: %s", e)
        flash("PDF থেকে ডেটা এক্সট্রাক্ট করা যায়নি। ফাইল ফরম্যাট চেক করুন।")
        return redirect(url_for("analyze"))

    except Exception:
        logger.exception("Unexpected error while processing report")
        flash("প্রসেসিং এর সময় একটি সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        return redirect(url_for("analyze"))

    finally:
        if os.path.exists(save_path):
            os.remove(save_path)


@app.errorhandler(413)
def file_too_large(e):
    flash("ফাইল সাইজ সীমার বাইরে (ম্যাক্স ৫ এমবি)।")
    return redirect(url_for("analyze"))


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)