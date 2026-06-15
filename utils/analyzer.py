import math
from typing import Any, Dict, List, Optional

import pandas as pd


class DataProfiler:
    """Profiles a pandas DataFrame for InsightAI dashboard.

    All business logic for scoring, issues, and computed statistics lives here
    (utils/analyzer.py). The Flask app should only orchestrate file loading
    and render the template using the returned report.
    """

    def __init__(self, df: pd.DataFrame):
        """Initialize the profiler with the dataset."""
        self.df = df

    def profile(self) -> Dict[str, Any]:
        """Build a complete report dictionary consumable by result.html."""
        rows, cols = self._shape()
        missing_total = self._missing_total()
        duplicate_rows = self._duplicate_rows()

        preview = self._preview_rows(limit=10)

        column_analysis = self._column_analysis()
        issues = self._issues_detected(column_analysis=column_analysis, duplicate_rows=duplicate_rows)

        missing_percent = self._missing_percentage(missing_total=missing_total, rows=rows, cols=cols)

        score = self._compute_quality_score(
            rows=rows,
            cols=cols,
            missing_total=missing_total,
            missing_percent=missing_percent,
            duplicate_rows=duplicate_rows,
            column_analysis=column_analysis,
        )
        score_label, score_color_class = self._score_bucket(score)

        # Progress bar width is the score out of 100
        progress_width = f"{score}%"

        return {
            "rows": rows,
            "columns": cols,
            "missing_values": int(missing_total),
            "duplicate_rows": int(duplicate_rows),
            "missing_percent": missing_percent,
            "duplicate_records_count": int(duplicate_rows),
            "preview": preview,
            "column_analysis": column_analysis,
            "issues": issues,
            "quality_score": score,
            "quality_score_label": score_label,
            "quality_score_color_class": score_color_class,
            "quality_score_progress_width": progress_width,
        }

    def _shape(self) -> tuple[int, int]:
        """Return the dataset shape as (rows, columns)."""
        return int(self.df.shape[0]), int(self.df.shape[1])

    def _missing_total(self) -> int:
        """Return total number of missing cells in the DataFrame."""
        # sum() over rows gives series of missing counts; sum() again over columns totals.
        return int(self.df.isna().sum().sum())

    def _duplicate_rows(self) -> int:
        """Return count of duplicate records (rows duplicated)."""
        # duplicated() marks True for duplicates excluding first occurrence.
        return int(self.df.duplicated().sum())

    def _preview_rows(self, limit: int = 10) -> Dict[str, Any]:
        """Return a HTML-friendly preview structure.

        Returns:
            {
              "columns": [..],
              "rows": [ [..], [..] ]
            }
        """
        preview_df = self.df.head(limit)
        cols: List[str] = [str(c) for c in preview_df.columns]
        rows: List[List[Optional[str]]] = []

        for _, r in preview_df.iterrows():
            row_values: List[Optional[str]] = []
            for v in r.tolist():
                if pd.isna(v):
                    row_values.append(None)
                else:
                    row_values.append(str(v))
            rows.append(row_values)

        return {"columns": cols, "rows": rows}

    def _column_analysis(self) -> List[Dict[str, Any]]:
        """Compute per-column stats for the dashboard.

        For every column we return:
        - name
        - type
        - missing_count
        - unique_count
        - numeric stats if applicable: min/max/mean
        - unique_ratio (unique/non-null) used for high-cardinality issues
        """
        analysis: List[Dict[str, Any]] = []

        for col in self.df.columns:
            series = self.df[col]

            missing_count = int(series.isna().sum())

            # Unique count based on non-null values (so missing doesn't inflate cardinality)
            non_null = series.dropna()
            unique_count = int(non_null.nunique(dropna=True))

            dtype_str = str(series.dtype)

            # Determine numeric: use pandas type checks
            is_numeric = pd.api.types.is_numeric_dtype(series)

            col_dict: Dict[str, Any] = {
                "name": str(col),
                "dtype": dtype_str,
                "missing_count": missing_count,
                "unique_count": unique_count,
                "unique_ratio": self._safe_div(unique_count, len(non_null)),
                "is_numeric": bool(is_numeric),
            }

            if is_numeric:
                # Use numeric conversion to avoid issues with mixed types.
                numeric = pd.to_numeric(series, errors="coerce")
                numeric_non_null = numeric.dropna()

                col_dict.update(
                    {
                        "min": self._safe_stat(numeric_non_null.min()),
                        "max": self._safe_stat(numeric_non_null.max()),
                        "mean": self._safe_stat(numeric_non_null.mean()),
                    }
                )

            analysis.append(col_dict)

        return analysis

    def _safe_div(self, a: float, b: float) -> float:
        """Safely compute a/b returning 0.0 when b is 0."""
        if b == 0:
            return 0.0
        return float(a) / float(b)

    def _safe_stat(self, v: Any) -> Optional[float]:
        """Convert statistics to JSON/HTML-friendly types."""
        if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
            return None
        try:
            return float(v)
        except Exception:
            return None

    def _missing_percentage(self, missing_total: int, rows: int, cols: int) -> float:
        """Compute missing value percentage across all cells."""
        total_cells = rows * cols
        if total_cells <= 0:
            return 0.0
        return (missing_total / total_cells) * 100.0

    def _compute_quality_score(
        self,
        rows: int,
        cols: int,
        missing_total: int,
        missing_percent: float,
        duplicate_rows: int,
        column_analysis: List[Dict[str, Any]],
    ) -> int:
        """Compute Data Quality Score out of 100 using the provided deduction logic."""
        # Start from 100
        score = 100.0

        # 2 points for every missing value percentage
        # Interpreted as: subtract (2 * missing_percent)
        score -= 2.0 * missing_percent

        # 5 points if duplicate rows exist
        if duplicate_rows > 0:
            score -= 5.0

        # 3 points for object columns with too many unique values (>90%)
        # Use unique_ratio computed as unique_count / non_null_count.
        for col in column_analysis:
            is_object_like = not col.get("is_numeric", False)
            unique_ratio = float(col.get("unique_ratio", 0.0))
            if is_object_like and unique_ratio > 0.9:
                score -= 3.0

        score = max(0.0, score)
        return int(round(score))

    def _score_bucket(self, score: int) -> tuple[str, str]:
        """Return (label, css class) based on score thresholds."""
        if 90 <= score <= 100:
            return "Green", "progress-green"
        if 70 <= score <= 89:
            return "Blue", "progress-blue"
        if 50 <= score <= 69:
            return "Orange", "progress-orange"
        return "Red", "progress-red"

    def _issues_detected(
        self,
        column_analysis: List[Dict[str, Any]],
        duplicate_rows: int,
    ) -> List[str]:
        """Generate a list of human-readable issues for the dashboard."""
        issues: List[str] = []

        # Missing values by column
        for col in column_analysis:
            missing_count = int(col.get("missing_count", 0))
            if missing_count > 0:
                issues.append(f"⚠ Missing values detected in {col.get('name')}")

        # Duplicate records
        if duplicate_rows > 0:
            issues.append("⚠ Duplicate records found")

        # High cardinality object columns
        for col in column_analysis:
            is_object_like = not col.get("is_numeric", False)
            unique_ratio = float(col.get("unique_ratio", 0.0))
            if is_object_like and unique_ratio > 0.9:
                issues.append(f"⚠ High cardinality column: {col.get('name')}")

        if not issues:
            issues.append("✅ Dataset looks healthy")

        return issues

