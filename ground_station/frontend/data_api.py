# data_api.py

import csv                      # for reading csv files
import os                       # needed for ImageAPI class
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

    # Gets all values from the last row as a tuple (in column order)
    def get_latest_row_tuple(self) -> tuple | None:
        row = self._latest()
        if row:
            return tuple(row.values())  # Returns all column values as a tuple
        return None


# ImageAPI
class ImageAPI:
    """
    Serves paths to Diljot's image assets via simple getters.
    """
    def __init__(self, image_dir: Path):
        self.image_dir = image_dir   # Base directory containing images (e.g., /images)

    # Returns the most recently modified JPEG file in the image directory
    def get_latest_image_path(self) -> str | None:
        jpg_files = list(self.image_dir.glob("*.jpg"))  # not sure whether to type jpeg or jpg here
        if not jpg_files:
            return None
        latest_file = max(jpg_files, key=os.path.getmtime)
        # Im using getmtime to find the most recently modified .jpg file,
        # not sure if filenames are guaranteed to imply the creation order so sticking to this method for now.
        # If there is an equivalent to reading the last line in a CSV for this such as filename storing timestamp please let me know.

        return str(latest_file)


"""    # These are a few examples for specific image getters 
    def get_satellite_status_image(self) -> str:
        return self.get_image_path("satellite_status")

    def get_orbit_path_image(self) -> str:
        return self.get_image_path("orbit_path")

    def get_health_chart_image(self) -> str:
        return self.get_image_path("health_chart")"""

# quick local test for ImageAPI
"""if __name__ == "__main__":
    from pathlib import Path

    image_api = ImageAPI(Path("ground_station/backend/Images"))
    latest_image = image_api.get_latest_image_path()

    if latest_image:
        print(f"Latest image path: {latest_image}")
    else:
        print("No JPEG images found.")
"""