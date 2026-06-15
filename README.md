# 📊 InsightAI

> **AI-Powered Data Analyst Assistant**

InsightAI is an AI-powered web application that helps users analyze datasets, evaluate data quality, and prepare data for visualization and business intelligence. Simply upload a CSV or Excel file to receive an interactive profiling report with quality metrics, column analysis, and actionable insights.

---

# 🚀 Features

## ✅ Current Features

### 📂 Dataset Upload

* Upload CSV (`.csv`) files
* Upload Excel (`.xlsx`) files
* Automatic file validation

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

## 🔜 Phase 3 — In Progress

* One-Click Data Cleaning
* Explain Every Cleaning Step
* Download Cleaned Dataset

## 🔜 Phase 4

* AI Dashboard Recommendations
* Power BI Dashboard Suggestions
* Tableau Visualization Templates

## 🔜 Phase 5

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
├── requirements.txt
├── README.md
│
├── uploads/
├── cleaned_files/
├── reports/
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│
├── templates/
│   ├── index.html
│   └── result.html
│
└── utils/
    └── analyzer.py
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
Read Dataset
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
Analyze Columns
        │
        ▼
Detect Data Issues
        │
        ▼
Display Analytics Dashboard
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
