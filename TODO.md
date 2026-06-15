# TODO - InsightAI Phase 2

- [x] Implement `DataProfiler` in `utils/analyzer.py`:

  - [ ] Dataset preview (first 10 rows)
  - [ ] Dataset statistics: rows, cols, missing, duplicate rows
  - [ ] Column analysis: missing/unique and numeric stats
  - [ ] Duplicate records count
  - [ ] Data Quality Score out of 100 using required deduction rules
  - [ ] Progress bar color bucket + label formatting
  - [ ] Issues Detected list logic + healthy fallback

- [x] Modify `app.py` to only orchestrate:
  - [ ] Upload file handling
  - [ ] Read CSV/XLSX with pandas
  - [ ] Blank-to-NaN normalization
  - [ ] Call `DataProfiler(df).profile()`
  - [ ] Render `result.html` with report

- [x] Update `templates/result.html` to render the full dashboard:
  - [ ] Data Quality Score text + progress bar
  - [ ] Responsive stat cards
  - [x] Dataset Preview table with alternating row colors
  - [x] Column Analysis section
  - [ ] Duplicate records count
  - [ ] Issues Detected section (⚠ / ✅)
  - [ ] Future Features section

- [x] Update `static/css/style.css`:
  - [x] Progress bar styles
- [x] Table styles for preview (alternating row colors, responsive)
  - [x] Color classes for progress bucket

- [x] Smoke test:
  - [ ] Run Flask and upload a CSV/XLSX to validate UI + calculations

