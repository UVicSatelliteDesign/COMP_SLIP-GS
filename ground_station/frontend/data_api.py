# data_api.py

import csv                      # for reading csv files
from pathlib import Path  

# Path: From pathlib, makes file-path manipulation (and cross-platform paths) easier.

class DataAPI:
    """
    Reads uvsd.csv and exposes the most recent timestamp & value via getters.
    """
    # This constructor simply stores those settings on the object.
    def __init__(self,
                 csv_path: Path,
                 timestamp_col: str = "timestamp",
                 value_col: str   = "value"):
        self.csv_path      = csv_path                           # location of uvsd.csv file
        self.timestamp_col = timestamp_col        # Column names in the CSV for the timestamp      
        self.value_col     = value_col           # and the numeric value—defaults match your file’s headers           

    # A Generator Over CSV Rows - It reads one row at a time, which is memory-efficient for large files.
    def _rows(self):
        with open(self.csv_path, newline="") as f:
            for row in csv.DictReader(f):       # gives each row as a dict mapping column names to string values.
                yield row

    # Finding the Most Recent Row (reads last line only)
    def _latest(self):
        with open(self.csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
            if not rows:
                return None
            return rows[-1]  # Return the last row (assumed to be the latest)

    # public getters

    # Gets the latest value from the last row
    def get_latest_value(self) -> float | None:
        row = self._latest()
        if row and self.value_col in row:
            try:
                return float(row[self.value_col])
            except ValueError:
                pass
        return None

    # Gets the timestamp from the last row
    def get_latest_timestamp(self) -> str | None:
        row = self._latest()
        if row and self.timestamp_col in row:
            return row[self.timestamp_col]   # No datetime parsing needed
        return None
