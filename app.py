from flask import Flask, render_template, request
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

    if file.filename.endswith(".csv"):
        df = pd.read_csv(filepath, sep=None, engine="python")

    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(filepath)

    else:
        return "Unsupported file format"

    rows = df.shape[0]
    cols = df.shape[1]

    missing_values = df.isnull().sum().sum()

    duplicate_rows = df.duplicated().sum()

    return render_template(
        "result.html",
        rows=rows,
        cols=cols,
        missing_values=missing_values,
        duplicate_rows=duplicate_rows
    )


if __name__ == "__main__":
    app.run(debug=True)