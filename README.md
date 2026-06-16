# 📊 InsightAI

> **AI-Powered Data Analyst Assistant**

InsightAI is an AI-powered web application that helps users analyze datasets, evaluate data quality, and prepare data for visualization and business intelligence. Simply upload a CSV or Excel file to receive an interactive profiling report with quality metrics, column analysis, and actionable insights.

---

# 🚀 Features

## ✅ Current Features

### 📖 AI Business Storytelling (Phase 5)

* Executive Summary Generation
* KPI Interpretation and Context
* Visualization Storytelling & Narrative
* Automated Business Insights Generation
* Key Findings Extraction
* Data Risks & Recommendations
* Exportable Business Reports

### 📊 AI Dashboard Recommendations (Phase 4)

* Automatic column type analysis (Date, Numeric, Categorical, Boolean, Identifier)
* Context-aware KPI suggestions with business logic reasoning
* Chart recommendations matched to column mappings (Line, Bar, Pie, Scatter, Maps, etc.)
* Complete grid dashboard layout wireframe recommendations
* 5+ auto-generated business questions tailored to the dataset
* Structural metadata visualization insights

### 📂 Dataset Upload

* Upload CSV (`.csv`) files
* Upload Excel (`.xlsx`) files
* Automatic file validation & secure UUID naming

### 🧹 AI Data Cleaning (Phase 3)

* One-Click Data Cleaning
* Detailed dynamic explanation logs for each step taken
* Before vs After Data Quality Score Comparison
* Safe handling of missing values (median/mode/forward fill)
* Duplicates & empty rows elimination
* Standardize column names to lowercase `snake_case`
* Numeric column detection and text trimming (removing multi-space characters)
* Download Cleaned Dataset in original format (.csv or .xlsx)

### 📊 Advanced Dataset Profiling

* Total Rows
* Total Columns
* Dataset Preview (First 10 Rows)
* Missing Values Count
* Duplicate Rows Count

### ⭐ Data Quality Analysis

* Data Quality Score (0–100)
* Visual Progress Indicator
* Dataset Health Assessment

### 📋 Column Analysis

For each column:

* Data Type
* Missing Values
* Unique Values

For numeric columns:

* Minimum Value
* Maximum Value
* Mean Value

### ⚠️ Automatic Issue Detection

* Missing values detection
* Duplicate record detection
* High-cardinality column detection
* Data quality warnings

### 🎨 Modern Responsive Dashboard

* Professional analytics dashboard
* Responsive design
* Statistics cards
* Dataset preview table
* Column analysis cards

---

# 🛣️ Roadmap

## ✅ Phase 1 — Completed

* CSV & Excel Upload
* Basic Dataset Profiling
* Modern Landing Page

## ✅ Phase 2 — Completed

* Dataset Preview
* Data Quality Score
* Column Analysis
* Issue Detection Dashboard
* Responsive Analytics UI

## ✅ Phase 3 — Completed

* One-Click Data Cleaning
* Explain Every Cleaning Step
* Download Cleaned Dataset

## ✅ Phase 4 — Completed

* AI Dashboard Recommendations
* Power BI Dashboard Suggestions
* Tableau Visualization Templates

## ✅ Phase 5 — Completed

* AI Business Storytelling
* Executive Summary Generation
* Automated Business Insights

## 🔜 Phase 6

* Chat with Your Data
* Natural Language Querying
* AI Data Assistant

---

# 🛠️ Tech Stack

| Technology | Purpose                     |
| ---------- | --------------------------- |
| Python     | Backend Development         |
| Flask      | Web Framework               |
| Pandas     | Data Processing & Analysis  |
| HTML5      | Frontend Structure          |
| CSS3       | Styling & Responsive Design |
| JavaScript | Interactive UI              |

---

# 📂 Project Structure

```text
InsightAI/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── uploads/
├── cleaned_files/
├── reports/
│
├── routes/
│   ├── __init__.py
│   ├── main.py
│   └── upload.py
│
├── services/
│   ├── dataset_service.py
│   └── file_service.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│
├── templates/
│   ├── index.html
│   ├── result.html
│   ├── cleaned_result.html
│   ├── recommendations.html
│   ├── storytelling.html
│   └── errors/
│       ├── 400.html
│       ├── 404.html
│       ├── 413.html
│       └── 500.html
│
└── utils/
    ├── analyzer.py
    ├── cleaner.py
    ├── dashboard_recommender.py
    └── storytelling.py
```

---

# ⚙️ Installation

## Clone the repository

```bash
git clone https://github.com/YashPrajapati989/InsightAI.git
cd InsightAI
```

## Create a virtual environment (Optional)

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run the application

```bash
python app.py
```

Visit:

```
http://127.0.0.1:5000
```

---

# 📈 Current Workflow

```text
Upload CSV / Excel
        │
        ▼
Read Dataset Safely
        │
        ▼
Generate Dataset Profile
        │
        ▼
Calculate Data Quality Score
        │
        ▼
Preview First 10 Rows
        │
        ▼
Analyze Columns & Detect Issues
        │
        ▼
Display Analytics Dashboard with AI Recommendations
        │
        ▼
Apply AI Data Cleaning (One-Click)
        │
        ▼
Generate Cleaning Log & Before/After Score Comparison
        │
        ▼
Export Cleaned Dataset (CSV / Excel)
```

---

# 🎯 Future Workflow

```text
Upload Dataset
        │
        ▼
📊 Dataset Profiling
        │
        ▼
⭐ Data Quality Analysis
        │
        ▼
🧹 AI Data Cleaning
        │
        ▼
📊 Dashboard Recommendations
        │
        ▼
📖 Business Storytelling
        │
        ▼
💬 Chat with Your Data
        │
        ▼
📥 Export Reports & Cleaned Dataset
```

---

# 🎯 Vision

InsightAI aims to become a complete **AI Data Analyst Assistant** capable of:

* Profiling datasets
* Cleaning messy data automatically
* Explaining every transformation
* Recommending dashboards
* Generating business insights
* Creating executive reports
* Answering natural language questions about uploaded data

---

# 🤝 Contributing

Contributions, feature requests, and suggestions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push the branch
5. Open a Pull Request

---

# 📄 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Author

**Yash Prajapati**

⭐ If you like this project, consider giving it a star on GitHub!
