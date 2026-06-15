import os
import re
import math
import pandas as pd
from typing import Dict, Any, List
from utils.analyzer import DataProfiler

class DataCleaner:
    """
    Handles automatic cleaning of pandas DataFrames for InsightAI.
    Cleans duplicates, missing values, normalizes text, parses dates, and renames columns.
    Generates dynamic cleaning recommendations and natural language logs.
    """

    def __init__(self, df: pd.DataFrame, original_score: int):
        self.df = df.copy()
        self.original_df = df.copy()
        self.original_score = original_score
        
        # Tracking metrics
        self.rows_before = len(df)
        self.rows_after = len(df)
        self.duplicates_removed = 0
        self.missing_removed = 0  # Total filled missing values
        self.columns_renamed = 0
        self.datatypes_fixed = 0
        self.cleaning_log: List[str] = []

    def analyze(self) -> List[str]:
        """
        Scan the dataset and return a list of recommendations
        before the cleaning is actually performed.
        """
        recommendations = []
        df = self.df
        
        # 1. Duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            recommendations.append(f"Remove {dup_count} duplicate rows to ensure data integrity.")

        # 2. Empty Rows
        empty_rows = df.isna().all(axis=1).sum()
        if empty_rows > 0:
            recommendations.append(f"Remove {empty_rows} completely empty rows.")

        # 3. Column Names
        cols_to_rename = []
        for col in df.columns:
            cleaned_col = self._normalize_column_name(col)
            if cleaned_col != col:
                cols_to_rename.append(col)
        if cols_to_rename:
            recommendations.append(f"Standardize column names to snake_case ({len(cols_to_rename)} columns).")

        # 4. Column specific issues (Missing, Dates, Numeric, Text)
        for col in df.columns:
            series = df[col]
            missing_count = series.isna().sum()
            
            # Missing values recommendations
            if missing_count > 0:
                if pd.api.types.is_numeric_dtype(series):
                    recommendations.append(f"Fill {missing_count} missing values in '{col}' using Median.")
                elif 'date' in str(col).lower() or 'time' in str(col).lower():
                    recommendations.append(f"Fill {missing_count} missing values in date column '{col}' using forward fill.")
                else:
                    recommendations.append(f"Fill {missing_count} missing values in categorical column '{col}' using Mode.")

            # Date parsing recommendations
            if not pd.api.types.is_datetime64_any_dtype(series) and not pd.api.types.is_numeric_dtype(series):
                if 'date' in str(col).lower() or 'time' in str(col).lower():
                    recommendations.append(f"Convert column '{col}' to datetime format and parse dates safely.")

            # Text cleaning recommendations (object types)
            if pd.api.types.is_object_dtype(series) and not ('date' in str(col).lower() or 'time' in str(col).lower()):
                # Check if there is trailing space or double spaces
                string_vals = series.dropna().astype(str)
                has_extra_spaces = string_vals.apply(lambda x: x != x.strip() or '  ' in x).any()
                if has_extra_spaces:
                    recommendations.append(f"Trim spaces and clean extra whitespaces in text column '{col}'.")
                
                # Check if it looks numeric but is object type
                # Try to parse numeric
                numeric_parsed = pd.to_numeric(series, errors='coerce')
                # If at least 90% of non-null values can be numeric and it's not completely NaN
                if numeric_parsed.notna().sum() > 0.9 * series.notna().sum() and series.notna().sum() > 0:
                    recommendations.append(f"Convert numeric-looking column '{col}' to proper numeric type.")

        if not recommendations:
            recommendations.append("No cleaning recommended! Your dataset looks clean.")

        return recommendations

    def clean(self) -> Dict[str, Any]:
        """
        Execute all cleaning operations on the dataset.
        Updates internal metrics and log.
        """
        # 1. Clean completely empty rows
        self._clean_empty_rows()

        # 2. Clean duplicates
        self._clean_duplicates()

        # 3. Standardize Column Names
        self._clean_column_names()

        # 4. Clean and convert specific columns
        # We must iterate over columns. Since column names might change after step 3, 
        # we will use the current columns.
        current_cols = list(self.df.columns)
        for col in current_cols:
            self._clean_single_column(col)

        # Update rows after
        self.rows_after = len(self.df)

        # Profile the cleaned DataFrame to get new quality score and report details
        profiler = DataProfiler(self.df)
        cleaned_report = profiler.profile()
        quality_after = cleaned_report["quality_score"]

        return {
            "rows_before": self.rows_before,
            "rows_after": self.rows_after,
            "missing_removed": self.missing_removed,
            "duplicates_removed": self.duplicates_removed,
            "columns_renamed": self.columns_renamed,
            "datatypes_fixed": self.datatypes_fixed,
            "quality_before": self.original_score,
            "quality_after": quality_after,
            "cleaning_log": self.cleaning_log,
            "report": cleaned_report
        }

    def _normalize_column_name(self, name: str) -> str:
        """Helper to convert column name into snake_case."""
        s = str(name).strip()
        # Replace non-alphanumeric chars with underscore
        s = re.sub(r'[^a-zA-Z0-9]', '_', s)
        # Convert camelCase to snake_case
        s = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', s)
        s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
        # Replace multiple underscores with one
        s = re.sub(r'_+', '_', s)
        return s.lower().strip('_')

    def _clean_empty_rows(self):
        """Remove rows where all elements are NaN."""
        empty_mask = self.df.isna().all(axis=1)
        empty_count = empty_mask.sum()
        if empty_count > 0:
            self.df = self.df[~empty_mask].reset_index(drop=True)
            self.cleaning_log.append(f"Removed {empty_count} completely empty rows.")

    def _clean_duplicates(self):
        """Remove duplicate records."""
        dup_mask = self.df.duplicated()
        self.duplicates_removed = int(dup_mask.sum())
        if self.duplicates_removed > 0:
            self.df = self.df.drop_duplicates().reset_index(drop=True)
            self.cleaning_log.append(f"Removed {self.duplicates_removed} duplicate rows because duplicate data skews metrics.")

    def _clean_column_names(self):
        """Rename all columns to snake_case."""
        new_cols = []
        renamed_count = 0
        for col in self.df.columns:
            cleaned = self._normalize_column_name(col)
            if cleaned != col:
                renamed_count += 1
            new_cols.append(cleaned)
            
        self.df.columns = new_cols
        self.columns_renamed = renamed_count
        if renamed_count > 0:
            self.cleaning_log.append(f"Standardized {renamed_count} column names into lowercase snake_case format for better coding compliance.")

    def _clean_single_column(self, col: str):
        """Perform missing value imputation, type casting, and text trimming on a single column."""
        series = self.df[col]
        missing_count = int(series.isna().sum())
        is_date_col = 'date' in col.lower() or 'time' in col.lower()
        
        # 1. Text Trim / Whitespace normalization for text columns
        if pd.api.types.is_object_dtype(series) and not is_date_col:
            # Safe string cleanup
            self.df[col] = series.apply(
                lambda x: re.sub(r'\s+', ' ', str(x).strip()) if pd.notna(x) else x
            )
            # Re-read series after string cleaning
            series = self.df[col]

        # 2. Date conversion
        if is_date_col and not pd.api.types.is_datetime64_any_dtype(series):
            try:
                # Attempt to parse date safely
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    self.df[col] = pd.to_datetime(series, errors='coerce')
                self.datatypes_fixed += 1
                self.cleaning_log.append(f"Converted column '{col}' to datetime format and handled invalid dates.")
                series = self.df[col]
            except Exception:
                pass

        # 3. Numeric Conversion for object columns that look numeric
        if pd.api.types.is_object_dtype(series) and not is_date_col:
            numeric_parsed = pd.to_numeric(series, errors='coerce')
            if numeric_parsed.notna().sum() > 0.9 * series.notna().sum() and series.notna().sum() > 0:
                self.df[col] = numeric_parsed
                self.datatypes_fixed += 1
                self.cleaning_log.append(f"Converted text column '{col}' to numeric data type because its values were purely numerical.")
                series = self.df[col]

        # 4. Fill missing values
        if missing_count > 0:
            self.missing_removed += missing_count
            if pd.api.types.is_numeric_dtype(series):
                median_val = series.median()
                if not pd.isna(median_val):
                    self.df[col] = series.fillna(median_val)
                    self.cleaning_log.append(f"Filled {missing_count} missing values in numeric column '{col}' with median value ({median_val}).")
            elif pd.api.types.is_datetime64_any_dtype(series):
                self.df[col] = series.ffill().bfill() # Forward fill then backfill if first is NaN
                self.cleaning_log.append(f"Filled {missing_count} missing values in datetime column '{col}' using forward fill.")
            else:
                # Categorical column
                mode_series = series.mode()
                if not mode_series.empty:
                    mode_val = mode_series[0]
                    self.df[col] = series.fillna(mode_val)
                    self.cleaning_log.append(f"Filled {missing_count} missing values in categorical column '{col}' with mode value ('{mode_val}').")
                else:
                    # Fallback to empty string if no mode
                    self.df[col] = series.fillna("")

    def save_cleaned_file(self, directory: str, filename: str) -> str:
        """
        Save the cleaned DataFrame to the cleaned directory, matching the original format (CSV or Excel).
        Checks for Excel formula injection patterns before writing.
        """
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        
        # Prevent formula injection: escape values starting with '=', '+', '-', '@'
        cleaned_df = self.df.copy()
        for col in cleaned_df.columns:
            if pd.api.types.is_object_dtype(cleaned_df[col]):
                # If it's a string column, escape dangerous starting characters
                cleaned_df[col] = cleaned_df[col].apply(
                    lambda x: f"'{x}" if isinstance(x, str) and x.startswith(('=', '+', '-', '@')) else x
                )
        
        # Save file based on original extension
        if filepath.lower().endswith('.xlsx'):
            cleaned_df.to_excel(filepath, index=False, engine='openpyxl')
        else:
            cleaned_df.to_csv(filepath, index=False)
        return filepath
