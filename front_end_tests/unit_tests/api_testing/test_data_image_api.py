import pytest
import csv
import os
import random
from pathlib import Path
from ground_station.frontend.data_api import DataAPI, ImageAPI

# -------------------------------
# DataAPI Tests
# -------------------------------
class TestDataAPI:

    @pytest.fixture
    def valid_csv(self, tmp_path):
        """
        Creates a CSV file with valid timestamp-value pairs.
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
        Creates a CSV file with invalid formatting or non-numeric data.
        """
        file = tmp_path / "uvsd.csv"
        with file.open("w", newline="") as f:
            f.write("bad,format\nnonsense,data\n")
        return file

    def test_latest_value_and_timestamp(self, valid_csv):
        """
        Checks that the latest value and timestamp are extracted correctly.
        """
        api = DataAPI(csv_path=valid_csv)
        assert api.get_latest_value() == 20
        assert api.get_latest_timestamp() == "2024-01-02T00:00:00Z"

    def test_empty_csv(self, tmp_path):
        """
        Tests behavior when CSV has only headers and no data.
        """
        file = tmp_path / "uvsd.csv"
        file.write_text("timestamp,value\n")
        api = DataAPI(csv_path=file)
        assert api.get_latest_value() is None
        assert api.get_latest_timestamp() is None

    def test_malformed_csv(self, malformed_csv):
        """
        Tests graceful failure on malformed CSV data.
        """
        api = DataAPI(csv_path=malformed_csv)
        assert api.get_latest_value() is None
        assert api.get_latest_timestamp() is None


# -------------------------------
# ImageAPI Tests
# -------------------------------
class TestImageAPI:

    @pytest.fixture
    def populated_dir(self, tmp_path):
        """
        Creates a folder with two image files and one text file.
        """
        dir_path = tmp_path / "images"
        dir_path.mkdir()
        (dir_path / "20240701.jpeg").write_bytes(os.urandom(1024))
        (dir_path / "20240702.jpeg").write_bytes(os.urandom(1024))
        (dir_path / "note.txt").write_text("not an image")
        return dir_path

    @pytest.fixture
    def empty_dir(self, tmp_path):
        """
        Creates an empty directory.
        """
        dir_path = tmp_path / "empty"
        dir_path.mkdir()
        return dir_path

    def test_latest_image_name(self, populated_dir):
        """
        Checks if latest image (by name) is returned correctly.
        """
        api = ImageAPI(image_dir=populated_dir)
        assert api.get_latest_image_path() == "20240702"

    def test_ignores_non_image_files(self, populated_dir):
        """
        Confirms that text files are ignored when finding the latest image.
        """
        api = ImageAPI(image_dir=populated_dir)
        latest = api.get_latest_image_path()
        assert latest.endswith("20240702")

    def test_empty_image_folder(self, empty_dir):
        """
        Confirms that None is returned when the folder has no images.
        """
        api = ImageAPI(image_dir=empty_dir)
        assert api.get_latest_image_path() is None

    def test_folder_with_only_non_images(self, tmp_path):
        """
        Confirms that non-image-only folder returns None.
        """
        dir_path = tmp_path / "nons"
        dir_path.mkdir()
        (dir_path / "hello.txt").write_text("text")
        api = ImageAPI(image_dir=dir_path)
        assert api.get_latest_image_path() is None

    def test_get_latest_image_path(self, populated_dir):
        """
        Checks that the correct image Path object is returned.
        """
        api = ImageAPI(image_dir=populated_dir)
        path = api.get_latest_image_path()
        assert path.name == "20240702.jpeg"
        assert path.exists()
