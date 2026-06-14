from flask import Flask, render_template, request
from utils.analyzer import DataProfiler
import pandas as pd
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    if "file" not in request.files:
        return "No file uploaded"

    file = request.files["file"]

    if file.filename == "":
        return "No file selected"

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    # Read dataset
    if file.filename.endswith(".csv"):
        df = pd.read_csv(filepath, sep=None, engine="python")

    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(filepath)

    else:
        return "Unsupported file format"

    # Convert blank cells to NaN
    df = df.replace(r'^\s*$', pd.NA, regex=True)

    # Profile dataset
    profiler = DataProfiler(df)

    report = profiler.profile()

    # Render result page
    return render_template(
        "result.html",
        report=report
    )


if __name__ == "__main__":
    app.run(debug=True)

