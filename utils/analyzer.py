import pandas as pd

class DataProfiler:

    def __init__(self, df):
        self.df = df

    def profile(self):

        return {
            "rows": self.df.shape[0],
            "columns": self.df.shape[1],
            "missing_values": self.df.isna().sum().sum(),
            "duplicate_rows": self.df.duplicated().sum(),
            "column_names": list(self.df.columns),
            "data_types": self.df.dtypes.astype(str).to_dict()
        }