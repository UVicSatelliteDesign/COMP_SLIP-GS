
# data_api.py

import csv                      # for reading csv files
from pathlib import Path  
from datetime import datetime
# Path: From pathlib, makes file-path manipulation (and cross-platform paths) easier.
# datetime: We need this to parse the timestamp strings into real date/time objects, so we can compare which row is newest.

class DataAPI:
    """
    Reads uvsd.csv and exposes the most recent timestamp & value via getters.
    """
    # This constructor simply stores those settings on the object.
    def __init__(self,
                 csv_path: Path,
                 timestamp_col: str = "timestamp",
                 value_col: str   = "value",
                 fmt: str         = "%Y-%m-%d %H:%M:%S"):
        self.csv_path      = csv_path                           # location of uvsd.csv file
        self.timestamp_col = timestamp_col        # Column names in the CSV for the timestamp      
        self.value_col     = value_col           # and the numeric value—defaults match your file’s headers           
        self.fmt           = fmt                # The format string used by datetime.strptime to parse timestamp text


    # A Generator Over CSV Rows - It reads one row at a time, which is memory-efficient for large files.
    def _rows(self):
        with open(self.csv_path, newline="") as f:
            for row in csv.DictReader(f):       # gives each row as a dict mapping column names to string values.
                yield row


    # Finding the Most Recent Row
    def _latest(self):
        latest_row = None
        latest_time = None
        for row in self._rows():
            try:
                t = datetime.strptime(row[self.timestamp_col], self.fmt)
            except Exception:
                continue
            if latest_time is None or t > latest_time:
                latest_time = t
                latest_row = row
        return latest_time, latest_row          # At the end, return a tuple (latest_time, latest_row_dict)


    # public getters

    # Calls _latest(), grabs the row dict, converts the value field to : float, or returns None on any error.
    def get_latest_value(self) -> float | None:
        _, row = self._latest()
        if row and self.value_col in row:
            try:
                return float(row[self.value_col])
            except ValueError:
                pass
        return None

    # Takes the datetime object from _latest(), 
    # formats it back to : the original string format, or None if there was no valid timestamp
    def get_latest_timestamp(self) -> str | None:
        t, _ = self._latest()
        if t:
            return t.strftime(self.fmt)
        return None
