# 🧠 InsightAI — AI-Powered Data Analyst Assistant

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Claude AI](https://img.shields.io/badge/Claude%20AI-412991?style=for-the-badge&logo=anthropic&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=for-the-badge)

> Upload a CSV or Excel file. Get instant profiling, AI-powered data cleaning, dashboard recommendations, executive-level business storytelling, and a natural language chat interface — all in one web app.

---

## 📌 Table of Contents

- [What Is InsightAI?](#-what-is-insightai)
- [Live Workflow](#-live-workflow)
- [Features by Phase](#-features-by-phase)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Roadmap](#️-roadmap)
- [Vision](#-vision)
- [Contributing](#-contributing)
- [Author](#-author)

---

## 🔍 What Is InsightAI?

**InsightAI** is a full-stack, AI-powered web application designed to act as an intelligent data analyst for anyone who uploads a dataset. Instead of spending hours in Excel or writing Pandas scripts, a user can upload a `.csv` or `.xlsx` file and immediately receive:

- Automated data profiling and quality scoring
- One-click AI cleaning with step-by-step explanations
- AI-generated dashboard and chart recommendations
- Executive-level business storytelling and insights
- A natural language chat interface to query the data directly

The project was built in **6 iterative phases**, each adding a meaningful layer of intelligence on top of the previous one.

---

## 🔄 Live Workflow

```
Upload CSV / Excel
        │
        ▼
  Read & Validate Dataset (UUID naming, type detection)
        │
        ▼
  Dataset Profiling
  ├── Row / Column count
  ├── Missing values & duplicates
  └── First 10-row preview
        │
        ▼
  Data Quality Score (0–100)
  └── Visual health indicator with assessment label
        │
        ▼
  Column Analysis
  ├── Data types, unique values, missing counts
  └── Min / Max / Mean for numeric columns
        │
        ▼
  Issue Detection Dashboard
  ├── Missing value warnings
  ├── Duplicate record alerts
  └── High-cardinality column flags
        │
        ▼
  AI Data Cleaning (One-Click)
  ├── Median/mode/forward-fill for nulls
  ├── Duplicate & empty row removal
  ├── Column name standardization (snake_case)
  ├── Numeric type coercion & text trimming
  └── Before vs After quality score comparison
        │
        ▼
  Download Cleaned Dataset (.csv or .xlsx)
        │
        ▼
  AI Dashboard Recommendations
  ├── Column type classification (Date, Numeric, Categorical…)
  ├── KPI suggestions with business reasoning
  ├── Chart type recommendations with column mappings
  └── Grid dashboard layout wireframe
        │
        ▼
  AI Business Storytelling
  ├── Executive summary
  ├── KPI interpretation & context
  ├── Key findings extraction
  ├── Risk & recommendation report
  └── Exportable business report
        │
        ▼
  Chat with Your Data
  ├── Natural language → Pandas/SQL query generation
  ├── Dynamic chart generation (Bar, Line, Pie)
  ├── Paginated data table output
  ├── Persistent conversational memory
  └── "Show your work" query explanation mode
```

---

## ✨ Features by Phase

### ✅ Phase 1 & 2 — Upload, Profile & Analyse

The foundation. Upload a `.csv` or `.xlsx`, and InsightAI immediately generates a full profiling report.

- Secure file upload with UUID naming and format validation
- Total rows, columns, missing values, and duplicate counts
- First 10-row dataset preview table
- **Data Quality Score** (0–100) with a visual progress indicator and health label
- Per-column analysis: data type, missing count, unique values, and min/max/mean for numeric fields
- Automatic issue detection: missing values, duplicates, high-cardinality columns

---

### ✅ Phase 3 — AI Data Cleaning

One click. Clean data. Full transparency.

- Safe handling of missing values using median (numeric), mode (categorical), and forward-fill (time series)
- Duplicate and completely empty row removal
- Column name standardisation to `snake_case`
- Numeric coercion for columns stored as text
- Whitespace and multi-space trimming across string fields
- **Detailed cleaning log** — every action explained in plain English
- Before vs After Data Quality Score comparison
- Download the cleaned file in the original format (`.csv` or `.xlsx`)

> **Why this matters:** Automated cleaning with transparent explanations bridges the gap between raw data and analysis-ready data, making this tool genuinely useful for non-technical users and analysts alike.

---

### ✅ Phase 4 — AI Dashboard Recommendations

InsightAI analyses your dataset's structure and recommends a complete BI dashboard layout — before you even open Power BI or Tableau.

- Column type classification: Date, Numeric, Categorical, Boolean, Identifier
- Context-aware KPI suggestions with business logic reasoning
- Chart type recommendations (Line, Bar, Pie, Scatter, Map) matched to specific column pairings
- Full grid dashboard wireframe layout
- 5+ auto-generated business questions tailored to the dataset

---

### ✅ Phase 5 — AI Business Storytelling

Converts raw numbers into a narrative a stakeholder can actually read.

- Executive summary generation
- KPI interpretation with contextual business meaning
- Visualization storytelling — what each chart is actually saying
- Automated insights: trends, anomalies, and highlights
- Key findings extraction
- Data risks and actionable recommendations
- Exportable business report

---

### ✅ Phase 6 — Chat with Your Data

Ask questions about your dataset in plain English and get instant answers — with charts.

- Natural language → Pandas/SQL query generation and execution
- Dynamic chart generation: Bar, Line, and Pie charts from a text prompt
- Formatted data tables with pagination for large result sets
- Persistent conversational AI memory across a session
- "Show your work" mode — see the generated query before results are shown

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3 | Core application logic |
| Web Framework | Flask | Routing, API endpoints, file handling |
| Data Processing | Pandas | Dataset profiling, cleaning, analysis |
| AI Layer | Claude API (Anthropic) | NL querying, storytelling, recommendations |
| Frontend | HTML5 + CSS3 + JavaScript | Responsive dashboard UI |
| File Handling | UUID, Werkzeug | Secure upload and naming |

---

## 📁 Project Structure

```
InsightAI/
│
├── app.py                          # App entry point
├── config.py                       # Configuration & environment variables
├── requirements.txt                # Python dependencies
│
├── 📂 uploads/                     # Raw uploaded files
├── 📂 cleaned_files/               # Cleaned output files
├── 📂 reports/                     # Exported business reports
│
├── 📂 routes/
│   ├── __init__.py
│   ├── main.py                     # Landing page & routing
│   └── upload.py                   # File upload endpoints
│
├── 📂 services/
│   ├── dataset_service.py          # Dataset read/parse logic
│   └── file_service.py             # File I/O, UUID naming, format detection
│
├── 📂 utils/
│   ├── analyzer.py                 # Profiling & quality scoring
│   ├── cleaner.py                  # Data cleaning pipeline
│   ├── dashboard_recommender.py    # AI dashboard & chart suggestions
│   ├── storytelling.py             # AI business narrative generation
│   └── chat_engine.py             # NL query engine + chart generation
│
├── 📂 static/
│   ├── css/style.css               # Responsive dashboard styles
│   └── js/                         # Frontend interactivity
│
└── 📂 templates/
    ├── index.html                  # Landing page
    ├── result.html                 # Profiling dashboard
    ├── cleaned_result.html         # Post-cleaning report
    ├── recommendations.html        # AI dashboard suggestions
    ├── storytelling.html           # Business narrative view
    ├── chat.html                   # Chat with data interface
    └── errors/
        ├── 400.html
        ├── 404.html
        ├── 413.html
        └── 500.html
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip
- An Anthropic API key (for AI features)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YashPrajapati989/InsightAI.git
cd InsightAI

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
export ANTHROPIC_API_KEY=your_api_key_here   # Linux/macOS
set ANTHROPIC_API_KEY=your_api_key_here      # Windows

# 5. Run the application
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## 🗺️ Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| Phase 1 | CSV & Excel Upload + Basic Profiling | ✅ Complete |
| Phase 2 | Data Quality Score + Column Analysis + Issue Detection | ✅ Complete |
| Phase 3 | AI Data Cleaning + Cleaning Log + Download | ✅ Complete |
| Phase 4 | AI Dashboard Recommendations | ✅ Complete |
| Phase 5 | AI Business Storytelling + Executive Reports | ✅ Complete |
| Phase 6 | Chat with Your Data + Dynamic Charts | ✅ Complete |
| Phase 7 | Multi-dataset joins and comparison mode | 🔜 Planned |
| Phase 8 | User authentication + saved sessions | 🔜 Planned |
| Phase 9 | Direct Power BI / Tableau export | 🔜 Planned |

---

## 🎯 Vision

InsightAI is built toward becoming a **complete AI Data Analyst Assistant** — one that removes every friction point between raw data and business decisions.

The target state: a non-technical user uploads a dataset, and within minutes has a cleaned file, a dashboard layout, an executive-readable report, and the ability to ask questions about their data in plain English — without writing a single line of code or touching a BI tool.

---

## 🤝 Contributing

Contributions, feature requests, and bug reports are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add: your feature description"`
4. Push the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Yash Prajapati**

[![GitHub](https://img.shields.io/badge/GitHub-YashPrajapati989-181717?style=for-the-badge&logo=github)](https://github.com/YashPrajapati989)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Yash%20Prajapati-0077B5?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/yash-prajapati-2b99392b8)

---

> ⭐ If InsightAI saved you time or impressed you, give it a star — it helps others find the project!
