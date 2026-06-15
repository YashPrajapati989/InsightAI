import os

import pandas as pd
from flask import Flask, render_template, request

from utils.analyzer import DataProfiler

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    """Render the dataset upload page."""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Handle dataset upload and render the generated dashboard report."""
    if "file" not in request.files:
        return "No file uploaded"

    file = request.files["file"]
    if file.filename == "":
        return "No file selected"

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Read dataset (business logic intentionally kept minimal here)
    if file.filename.lower().endswith(".csv"):
        df = pd.read_csv(filepath, sep=None, engine="python")
    elif file.filename.lower().endswith(".xlsx"):
        df = pd.read_excel(filepath)
    else:
        return "Unsupported file format"

    # Convert blank cells to NaN so the analyzer can detect missing values consistently.
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    # Profile dataset using the DataProfiler utility.
    report = DataProfiler(df).profile()

    # Render result page (result.html renders only using Jinja2 data).
    return render_template("result.html", report=report)


if __name__ == "__main__":
    app.run(debug=True)


