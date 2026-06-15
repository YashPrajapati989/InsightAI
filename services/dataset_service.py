import pandas as pd
from flask import current_app

class DatasetError(Exception):
    """Custom exception for dataset processing errors."""
    pass

def load_dataset(filepath):
    """
    Safely load a dataset using pandas.
    Handles malformed files, encoding issues, and size protections.
    """
    try:
        if filepath.lower().endswith('.csv'):
            # Using python engine can be slower and riskier for weird encodings,
            # but setting 'c' engine with specific parameters is safer.
            # `on_bad_lines='skip'` handles malformed CSVs better than crashing.
            df = pd.read_csv(filepath, on_bad_lines='skip', engine='c')
        elif filepath.lower().endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            raise DatasetError("Unsupported file format for reading")

        if df.empty:
            raise DatasetError("The uploaded dataset is empty.")
            
        # Basic Safety Checks
        MAX_COLUMNS = 1000
        MAX_ROWS = 500000
        
        if len(df.columns) > MAX_COLUMNS:
            raise DatasetError(f"Dataset has too many columns (max {MAX_COLUMNS} allowed).")
            
        if len(df) > MAX_ROWS:
            raise DatasetError(f"Dataset has too many rows (max {MAX_ROWS} allowed).")
            
        # Convert blank cells to NaN for consistent detection
        df = df.replace(r"^\s*$", pd.NA, regex=True)
        
        return df
        
    except pd.errors.EmptyDataError:
        raise DatasetError("The dataset file is empty or corrupted.")
    except pd.errors.ParserError as e:
        current_app.logger.error(f"Parser error while reading dataset: {e}")
        raise DatasetError("Failed to parse the dataset. The file might be corrupted or malformed.")
    except Exception as e:
        current_app.logger.error(f"Unexpected error loading dataset: {e}")
        raise DatasetError(f"An unexpected error occurred while loading the dataset.")
