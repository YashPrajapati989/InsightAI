import os
import re
import math
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
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


class DataCleaningAgent:
    """
    Advanced interactive data cleaning analyst agent.
    Analyzes missing values and outliers from statistical, business,
    and operational perspectives (Causes A-I) without making automatic modifications.
    Executes changes only upon explicit user approval.
    """

    def __init__(self, df: pd.DataFrame, original_score: int):
        self.df = df.copy()
        self.original_df = df.copy()
        self.original_score = original_score
        self.audit_log: List[str] = []

    def analyze(self) -> Dict[str, Any]:
        """Perform deep missing values and outliers analysis."""
        missing_analysis = self._analyze_missing_values()
        outlier_analysis = self._analyze_outliers()
        
        return {
            "quality_score": self.original_score,
            "missing_analysis": missing_analysis,
            "outlier_analysis": outlier_analysis,
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns)
        }

    def _analyze_missing_values(self) -> Dict[str, Any]:
        analysis = {}
        df = self.df
        total_rows = len(df)
        if total_rows == 0:
            return analysis

        # Identify categorical columns to cross-reference missingness pattern
        cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_datetime64_any_dtype(df[c]) and df[c].nunique() < 15]

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            if missing_count == 0:
                continue

            missing_percent = (missing_count / total_rows) * 100.0
            col_lower = str(col).lower()

            # 1. Consecutive missing rows (run-length encoding helper)
            is_na = series.isna().astype(int)
            consecutive = (is_na.groupby((is_na != is_na.shift()).cumsum()).transform('sum') * is_na).max()
            consecutive_missing = int(consecutive) if pd.notna(consecutive) else 0

            # 2. Start/End of time series check
            is_temporal = pd.api.types.is_datetime64_any_dtype(series) or 'date' in col_lower or 'time' in col_lower
            missing_at_start = False
            missing_at_end = False
            if is_temporal and total_rows > 0:
                missing_at_start = pd.isna(series.iloc[0])
                missing_at_end = pd.isna(series.iloc[-1])

            # 3. Missing pattern by category
            category_patterns = []
            for cat_col in cat_cols:
                if cat_col != col:
                    grouped = df.groupby(cat_col)[col].apply(lambda x: x.isna().sum()).reset_index()
                    grouped_total = df.groupby(cat_col).size().reset_index(name='total')
                    merged = pd.merge(grouped, grouped_total, on=cat_col)
                    merged['pct'] = (merged[col] / merged['total']) * 100.0
                    merged_sorted = merged.sort_values(by='pct', ascending=False)
                    # Find categories with highly concentrated missingness (>50%)
                    for _, row in merged_sorted.iterrows():
                        if row['pct'] > 50.0 and row['total'] > 3:
                            category_patterns.append(f"Highly missing in segment '{row[cat_col]}' of '{cat_col}' ({row['pct']:.1f}% missing)")

            # 4. Evaluate Causes A to I
            causes = []
            rec_action = "Keep NULL"
            confidence = "High"
            risk_level = "Low"

            # Cause I: Excessive missingness
            if missing_percent >= 50.0:
                causes.append({
                    "cause": "Cause I: Excessive Missingness",
                    "explanation": f"Column has critical missingness ({missing_percent:.1f}%). Imputation risks introducing massive bias.",
                    "confidence": "High"
                })
                rec_action = "Request User Review / Drop Column"
                confidence = "High"
                risk_level = "High"
            elif missing_percent >= 20.0:
                causes.append({
                    "cause": "Cause I: Excessive Missingness",
                    "explanation": f"Column has high missingness ({missing_percent:.1f}%). Proceed with extreme caution.",
                    "confidence": "Medium"
                })
                rec_action = "Request User Review"
                confidence = "Medium"
                risk_level = "Medium"

            # Cause C: Intentionally Left Blank
            optional_keywords = ['middle', 'suffix', 'phone', 'fax', 'website', 'optional', 'comment', 'notes', 'address2', 'secondary']
            if any(k in col_lower for k in optional_keywords):
                causes.append({
                    "cause": "Cause C: Intentionally Left Blank",
                    "explanation": "Field appears to collect optional or auxiliary information (e.g. secondary contact details).",
                    "confidence": "High"
                })
                if rec_action == "Keep NULL":
                    rec_action = "Keep NULL"
                    confidence = "High"
                    risk_level = "Low"

            # Cause D: Not Applicable
            na_keywords = ['spouse', 'dependents', 'bonus', 'commission', 'marriage', 'partner', 'children']
            if any(k in col_lower for k in na_keywords):
                causes.append({
                    "cause": "Cause D: Not Applicable",
                    "explanation": "Field may not apply to all entities (e.g., bonus for non-sales employees, spouse name for unmarried clients).",
                    "confidence": "High"
                })
                if rec_action == "Keep NULL":
                    rec_action = "Convert to 'N/A' or Keep NULL"
                    confidence = "High"
                    risk_level = "Low"

            # Cause E: Future Placeholder Data
            if is_temporal and missing_at_end:
                causes.append({
                    "cause": "Cause E: Future Placeholder Data",
                    "explanation": "Missing entries are at the end of the chronological sequence, indicating forecast periods or placeholders.",
                    "confidence": "Medium"
                })
                if rec_action == "Keep NULL":
                    rec_action = "Keep Empty / Do Not Impute"
                    confidence = "High"
                    risk_level = "Low"

            # Cause B: System Failure
            if consecutive_missing >= 10:
                causes.append({
                    "cause": "Cause B: System Failure",
                    "explanation": f"Detected a block of {consecutive_missing} consecutive missing values, indicating sensor downtime, API failure, or ingestion halt.",
                    "confidence": "Medium"
                })
                rec_action = "Interpolate or Forward Fill"
                confidence = "Medium"
                risk_level = "Medium"

            # Cause F: Data Still Being Collected
            if not is_temporal and consecutive_missing > 0 and (is_na.tail(missing_count).sum() == missing_count):
                # Missing values are concentrated at the very end
                causes.append({
                    "cause": "Cause F: Data Still Being Collected",
                    "explanation": "Missing values are concentrated heavily at the end of the dataset, typical of ongoing processes or pending records.",
                    "confidence": "Medium"
                })
                rec_action = "Mark as Pending / Keep NULL"
                confidence = "Medium"
                risk_level = "Medium"

            # Cause G: Privacy or Compliance Removal
            sensitive_keywords = ['password', 'ssn', 'tax', 'income', 'salary', 'salary_amount', 'national_id', 'passport']
            if any(k in col_lower for k in sensitive_keywords):
                causes.append({
                    "cause": "Cause G: Privacy or Compliance Removal",
                    "explanation": "Field contains sensitive or regulatory personal data that may have been intentionally redacted or omitted for compliance.",
                    "confidence": "Medium"
                })
                rec_action = "Preserve NULL"
                confidence = "Medium"
                risk_level = "Low"

            # Cause H: Missingness Has Predictive Value
            if category_patterns:
                causes.append({
                    "cause": "Cause H: Missingness Has Predictive Value",
                    "explanation": "Missingness correlates heavily with other attributes, indicating predictive value in the absence of a value.",
                    "confidence": "High"
                })
                rec_action = "Create Missing Indicator Feature (e.g. " + col + "_missing = 1)"
                confidence = "High"
                risk_level = "Low"

            # Default fallback: Cause A (Data Entry Error)
            if not causes:
                causes.append({
                    "cause": "Cause A: Data Entry Error",
                    "explanation": "Missing values are randomly distributed and isolated. Likely representing human omissions or simple entry mistakes.",
                    "confidence": "Medium"
                })
                if pd.api.types.is_numeric_dtype(series):
                    rec_action = "Median Imputation"
                elif is_temporal:
                    rec_action = "Forward Fill"
                else:
                    rec_action = "Mode Imputation"
                confidence = "Medium"
                risk_level = "Low"

            analysis[col] = {
                "name": col,
                "missing_count": missing_count,
                "missing_percent": missing_percent,
                "consecutive_missing": consecutive_missing,
                "is_temporal": is_temporal,
                "missing_at_start": missing_at_start,
                "missing_at_end": missing_at_end,
                "category_patterns": category_patterns,
                "causes": causes,
                "recommended_action": rec_action,
                "confidence_score": confidence,
                "risk_level": risk_level
            }

        return analysis

    def _analyze_outliers(self) -> Dict[str, Any]:
        analysis = {}
        df = self.df

        for col in df.columns:
            series = df[col]
            # Skip ID columns and non-numeric columns
            if not pd.api.types.is_numeric_dtype(series):
                continue
            
            col_lower = str(col).lower()
            if any(x in col_lower for x in ['id', 'key', 'code', 'zip', 'postal', 'num']):
                continue

            non_null = series.dropna()
            if len(non_null) < 5:
                continue

            # Method 1: IQR
            q1 = non_null.quantile(0.25)
            q3 = non_null.quantile(0.75)
            iqr = q3 - q1
            lower_iqr = q1 - 1.5 * iqr
            upper_iqr = q3 + 1.5 * iqr
            outliers_iqr = set(non_null[(non_null < lower_iqr) | (non_null > upper_iqr)].index)

            # Method 2: Z-Score
            mean_val = non_null.mean()
            std_val = non_null.std()
            if std_val > 0:
                z_scores = (non_null - mean_val) / std_val
                outliers_z = set(non_null[z_scores.abs() > 3.0].index)
            else:
                outliers_z = set()

            # Method 3: Modified Z-Score
            median_val = non_null.median()
            mad = (non_null - median_val).abs().median()
            if mad > 0:
                mod_z = 0.6745 * (non_null - median_val) / mad
                outliers_mod_z = set(non_null[mod_z.abs() > 3.5].index)
            else:
                outliers_mod_z = outliers_z.copy()

            # Method 4: Isolation Forest
            outliers_iforest = set()
            try:
                from sklearn.ensemble import IsolationForest
                X = non_null.values.reshape(-1, 1)
                # We scale contamination based on dataset size, default to 0.05
                clf = IsolationForest(contamination=0.05, random_state=42)
                preds = clf.fit_predict(X)
                outliers_iforest = set(non_null.index[preds == -1])
            except Exception:
                pass

            # Method 5: Percentile Method
            p1 = non_null.quantile(0.01)
            p99 = non_null.quantile(0.99)
            outliers_percentile = set(non_null[(non_null < p1) | (non_null > p99)].index)

            # Union of all outliers
            all_outlier_indices = outliers_iqr.union(outliers_z, outliers_mod_z, outliers_iforest, outliers_percentile)
            outlier_count = len(all_outlier_indices)
            if outlier_count == 0:
                continue

            # Check method agreement for each outlier row
            outlier_details = []
            for idx in sorted(list(all_outlier_indices))[:15]:  # limit to sample of 15
                val = non_null.loc[idx]
                methods = []
                if idx in outliers_iqr: methods.append("IQR")
                if idx in outliers_z: methods.append("Z-Score")
                if idx in outliers_mod_z: methods.append("Modified Z-Score")
                if idx in outliers_iforest: methods.append("Isolation Forest")
                if idx in outliers_percentile: methods.append("Percentiles")
                outlier_details.append({
                    "row_index": int(idx),
                    "value": float(val) if isinstance(val, (int, float, np.integer, np.floating)) else str(val),
                    "methods": methods
                })

            # Heuristics to evaluate Causes
            causes = []
            rec_action = "Keep Outliers"
            confidence = "High"
            risk_level = "Low"
            business_impact = "None detected. Outliers are statistical fluctuations."

            # Cause A: Data Entry Error (extra zeros, negative where impossible)
            has_extra_zeros = False
            has_impossible_negatives = False
            if (non_null < 0).any() and any(x in col_lower for x in ['age', 'salary', 'revenue', 'price', 'amount', 'spend', 'quantity']):
                has_impossible_negatives = True
            
            # Check if any outlier is 10x or 100x the median
            extreme_highs = pd.Series(dtype=float)  # default: empty
            if median_val > 0:
                extreme_highs = non_null[list(all_outlier_indices)] / median_val
                if (extreme_highs >= 10.0).any():
                    has_extra_zeros = True

            if has_extra_zeros or has_impossible_negatives:
                causes.append({
                    "cause": "Cause A: Data Entry Error",
                    "explanation": f"Detected values that are highly suspect (e.g., negatives where impossible, or values >10x the median suggesting fat-finger typo or extra zeros).",
                    "confidence": "High"
                })
                rec_action = "Correct or Remove"
                confidence = "High"
                risk_level = "Medium"
                business_impact = "Data entry errors lead to heavily skewed financial reporting and distorted averages."

            # Cause B: Measurement Error
            if (non_null > 150).any() and 'age' in col_lower:
                causes.append({
                    "cause": "Cause B: Measurement Error",
                    "explanation": "Values exceed humanly possible limits (e.g. age > 150), likely indicating sensor malfuction or hardware overflow.",
                    "confidence": "High"
                })
                rec_action = "Remove or Correct"
                confidence = "High"
                risk_level = "Medium"
                business_impact = "Measurement failures introduce invalid outliers that corrupt analytics modeling."

            # Cause H: Unit Conversion Error
            if median_val > 0:
                # E.g. mixed grams and kg (1000x difference) or mixed currencies (80x difference for USD/INR)
                if (extreme_highs.round() == 1000).any() or (extreme_highs.round() == 100).any():
                    causes.append({
                        "cause": "Cause H: Unit Conversion Error",
                        "explanation": "Outliers match exact 100x or 1000x scaling factor of the median value, suggesting unit confusion (e.g. grams vs kilograms).",
                        "confidence": "Medium"
                    })
                    rec_action = "Standardize Units / Scale Column"
                    confidence = "Medium"
                    risk_level = "Medium"
                    business_impact = "Mixed units corrupt aggregations and result in extreme statistical spreads."

            # Cause C: Genuine High/Low Value
            sales_keywords = ['sales', 'revenue', 'profit', 'spend', 'amount', 'salary', 'income']
            if any(k in col_lower for k in sales_keywords):
                causes.append({
                    "cause": "Cause C: Genuine High/Low Value",
                    "explanation": "Outliers represent high-performing assets, VIP clients, premium products, or top executives. These are real events that drive the business.",
                    "confidence": "High"
                })
                if rec_action == "Keep Outliers":
                    rec_action = "Keep (Do NOT Remove)"
                    confidence = "High"
                    risk_level = "Low"
                    business_impact = "These outliers represent key performance drivers (e.g. VIP customers or premium product lines) which must be kept to preserve strategic visibility."

            # Cause E: Fraud or Anomaly
            if any(k in col_lower for k in ['transaction', 'transfer', 'amount', 'withdrawal', 'payment']):
                causes.append({
                    "cause": "Cause E: Fraud or Anomaly",
                    "explanation": "Extremely high value in transactional fields, indicating potential operational risk, system bugs, or fraudulent activities.",
                    "confidence": "Medium"
                })
                rec_action = "Flag for Investigation"
                confidence = "Medium"
                risk_level = "High"
                business_impact = "Potential financial leakage or system exploitation. Automatically removing these hides security flaws."

            # Cause G: Different Population Segment
            # If standard deviation is high, segmenting might be useful
            causes.append({
                "cause": "Cause G: Different Population Segment",
                "explanation": "The extreme values may belong to a distinct segment of the population (e.g., enterprise contracts vs retail clients, executives vs staff).",
                "confidence": "Medium"
            })
            if rec_action == "Keep Outliers":
                rec_action = "Segment Analysis"
                confidence = "Medium"
                risk_level = "Low"
                business_impact = "Helps build separate models for enterprise vs retail clients to gain tailored insights."

            # Fallback Cause I: Statistical Outlier Only
            if not causes or rec_action == "Keep Outliers":
                causes.append({
                    "cause": "Cause I: Statistical Outlier Only",
                    "explanation": "The value is unusual statistically but completely valid in a business context. No evidence of errors or anomalies.",
                    "confidence": "High"
                })
                rec_action = "Keep"
                confidence = "High"
                risk_level = "Low"
                business_impact = "No operational errors detected. Removing them sacrifices valid historical data variations."

            analysis[col] = {
                "name": col,
                "outlier_count": outlier_count,
                "outlier_percentage": (outlier_count / len(non_null)) * 100.0 if len(non_null) > 0 else 0.0,
                "outlier_details": outlier_details,
                "causes": causes,
                "recommended_action": rec_action,
                "confidence_score": confidence,
                "risk_level": risk_level,
                "business_impact": business_impact,
                "iqr_bounds": (float(lower_iqr), float(upper_iqr)),
                "z_bounds": (float(mean_val - 3*std_val), float(mean_val + 3*std_val)) if std_val > 0 else (0.0, 0.0)
            }

        return analysis

    def apply_custom_cleaning(self, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """
        Applies cleaning configurations approved by the user.
        Generates audit log records for each step.
        """
        df_cleaned = self.df.copy()
        
        # 1. Standard preprocessing (Duplication & Empty Rows) if selected
        if config.get("remove_duplicates"):
            dup_count = df_cleaned.duplicated().sum()
            if dup_count > 0:
                df_cleaned = df_cleaned.drop_duplicates().reset_index(drop=True)
                self.audit_log.append(f"[APPROVED] Removed {dup_count} duplicate rows to ensure dataset uniqueness.")
            else:
                self.audit_log.append("[DECLINED/SKIPPED] No duplicate rows found.")
        else:
            self.audit_log.append("[DECLINED/SKIPPED] Duplicate row removal bypassed by user.")

        if config.get("remove_empty_rows"):
            empty_mask = df_cleaned.isna().all(axis=1)
            empty_count = empty_mask.sum()
            if empty_count > 0:
                df_cleaned = df_cleaned[~empty_mask].reset_index(drop=True)
                self.audit_log.append(f"[APPROVED] Removed {empty_count} completely empty rows.")
            else:
                self.audit_log.append("[DECLINED/SKIPPED] No completely empty rows found.")
        else:
            self.audit_log.append("[DECLINED/SKIPPED] Empty row removal bypassed by user.")

        # 2. Missing Value Imputation
        missing_actions = config.get("missing_actions", {})
        for col, action in missing_actions.items():
            if col not in df_cleaned.columns:
                continue
            
            series = df_cleaned[col]
            missing_count = int(series.isna().sum())
            if missing_count == 0:
                continue

            if action == "keep_null":
                self.audit_log.append(f"[APPROVED] Preserved {missing_count} missing values in '{col}' as NULL (User explicitly decided to keep blank).")
            elif action == "median":
                median_val = series.median()
                if pd.notna(median_val):
                    df_cleaned[col] = series.fillna(median_val)
                    self.audit_log.append(f"[APPROVED] Imputed {missing_count} missing values in '{col}' with median value ({median_val}).")
            elif action == "mean":
                mean_val = series.mean()
                if pd.notna(mean_val):
                    df_cleaned[col] = series.fillna(mean_val)
                    self.audit_log.append(f"[APPROVED] Imputed {missing_count} missing values in '{col}' with mean value ({mean_val:.4f}).")
            elif action == "mode":
                mode_series = series.mode()
                if not mode_series.empty:
                    mode_val = mode_series[0]
                    df_cleaned[col] = series.fillna(mode_val)
                    self.audit_log.append(f"[APPROVED] Imputed {missing_count} missing values in '{col}' with mode value ('{mode_val}').")
            elif action == "ffill":
                df_cleaned[col] = series.ffill().bfill()
                self.audit_log.append(f"[APPROVED] Imputed {missing_count} missing values in '{col}' using forward fill (ffill).")
            elif action == "na_string":
                df_cleaned[col] = series.fillna("N/A")
                self.audit_log.append(f"[APPROVED] Filled {missing_count} missing values in '{col}' with 'N/A' placeholder.")
            elif action == "indicator":
                # Create indicator and fill NaNs with mode/median
                df_cleaned[f"{col}_missing"] = series.isna().astype(int)
                fallback_val = series.median() if pd.api.types.is_numeric_dtype(series) else (series.mode().iloc[0] if not series.mode().empty else "")
                df_cleaned[col] = series.fillna(fallback_val)
                self.audit_log.append(f"[APPROVED] Created missing indicator feature '{col}_missing' and filled {missing_count} gaps in '{col}' with '{fallback_val}'.")
            else:
                self.audit_log.append(f"[DECLINED/SKIPPED] No action taken for {missing_count} missing values in '{col}' (bypassed).")

        # 3. Outlier Handling
        outlier_actions = config.get("outlier_actions", {})
        for col, action in outlier_actions.items():
            if col not in df_cleaned.columns or not pd.api.types.is_numeric_dtype(df_cleaned[col]):
                continue

            # Recompute bounds for reporting/clipping
            series = df_cleaned[col]
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            # Find row indices of outliers (IQR based is default bounds for removal/cap)
            outlier_mask = (series < lower_bound) | (series > upper_bound)
            outlier_count = int(outlier_mask.sum())
            if outlier_count == 0:
                continue

            if action == "keep":
                self.audit_log.append(f"[APPROVED] Kept {outlier_count} outliers in '{col}' (User confirmed values represent valid business context).")
            elif action == "remove":
                df_cleaned = df_cleaned[~outlier_mask].reset_index(drop=True)
                self.audit_log.append(f"[APPROVED] Removed {outlier_count} rows containing outliers in '{col}' to eliminate severe skew.")
            elif action == "cap":
                # Cap outliers to bounds
                df_cleaned[col] = series.clip(lower=lower_bound, upper=upper_bound)
                self.audit_log.append(f"[APPROVED] Capped {outlier_count} outliers in '{col}' to IQR bounds ({lower_bound:.2f} to {upper_bound:.2f}).")
            elif action == "nullify":
                df_cleaned.loc[outlier_mask, col] = np.nan
                self.audit_log.append(f"[APPROVED] Nullified {outlier_count} outlier values in '{col}' (converted to NaN for separate missing analysis).")
            else:
                self.audit_log.append(f"[DECLINED/SKIPPED] Kept outliers in '{col}' (bypassed outlier cleaning).")

        return df_cleaned, self.audit_log

