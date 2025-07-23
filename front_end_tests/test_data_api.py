import pytest
import csv
from pathlib import Path
from ground_station.frontend.data_api import DataAPI

class TestDataAPI:

    @pytest.fixture
    def valid_csv(self, tmp_path):
        """
        Creates a temporary CSV file with valid timestamp-value pairs.
        """
        file = tmp_path / "uvsd.csv"
        with file.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "value"])
            writer.writerow(["2024-01-01T00:00:00Z", 10])
            writer.writerow(["2024-01-02T00:00:00Z", 20])
        return file

    @pytest.fixture
    def malformed_csv(self, tmp_path):
        """
        Creates a malformed CSV file with random, non-parseable text.
        """
        file = tmp_path / "uvsd.csv"
        with file.open("w", newline="") as f:
            f.write("this,is,not,proper\njust some text\n")
        return file

    def test_latest_value_correct(self, valid_csv):
        """
        Test that DataAPI returns the correct latest timestamp and value.
        """
        api = DataAPI(csv_path=valid_csv)
        assert api.get_latest_value() == 20
        assert api.get_latest_timestamp() == "2024-01-02T00:00:00Z"

    def test_empty_csv_handling(self, tmp_path):
        """
        Test that DataAPI returns None if the CSV has no data rows.
        """
        file = tmp_path / "uvsd.csv"
        file.write_text("timestamp,value\n")  # header only
        api = DataAPI(csv_path=file)
        assert api.get_latest_value() is None
        assert api.get_latest_timestamp() is None

    def test_malformed_csv_handling(self, malformed_csv):
        """
        Test that DataAPI handles bad CSV format gracefully and returns None.
        """
        api = DataAPI(csv_path=malformed_csv)
        assert api.get_latest_value() is None
        assert api.get_latest_timestamp() is None
