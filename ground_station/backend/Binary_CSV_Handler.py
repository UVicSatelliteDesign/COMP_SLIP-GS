import os
import csv
import pickle

class DataHandler:
    def __init__(self, image_dir="images", telemetry_dir="telemetry"):
        try:
            assert isinstance(image_dir, str) and isinstance(telemetry_dir, str), "Directories must be strings"
            
            self.image_dir = image_dir
            self.telemetry_dir = telemetry_dir
            self.current_image = None
            self.current_csv = None
            self.previous_files = []

            # Ensuring directories exist
            os.makedirs(self.image_dir, exist_ok=True)
            os.makedirs(self.telemetry_dir, exist_ok=True)
        
        except AssertionError as e:
            print(f"Initialization error: {e}")
        except Exception as e:
            print(f"Unexpected error during initialization: {e}")

    def set_image(self, identifier, image_data, MF=False):
        """Stores image data in a binary file using pickle, handling More Fragment (MF) flag."""
        try:
            assert isinstance(identifier, str) and isinstance(image_data, bytes), "Invalid input types"
            
            image_filename = os.path.join(self.image_dir, f"{identifier}.pkl")
            
            if not MF:  # No more fragments, store and mark complete
                if self.current_image and self.current_image != image_filename:
                    self.previous_files.append(self.current_image)
                self.current_image = image_filename
                
                with open(image_filename, "wb") as f:
                    pickle.dump(image_data, f)
                
                print(f"Image saved: {image_filename}")

            else:                   # MF flag is True → append to an existing file (partial storage)
                if os.path.exists(image_filename):
                    with open(image_filename, "ab") as f:          # Append binary
                        f.write(image_data)
                else:
                    with open(image_filename, "wb") as f:
                        f.write(image_data)
                
                print(f"Image fragment saved: {image_filename} (MF=True)")

        except AssertionError as e:
            print(f"Image storage error: {e}")
        except Exception as e:
            print(f"Unexpected error in set_image(): {e}")

    def set_telemetry(self, identifier, telemetry_dict):
        """Stores telemetry data in a CSV file."""
        try:
            assert isinstance(identifier, str) and isinstance(telemetry_dict, dict), "Invalid input types"

            csv_filename = os.path.join(self.telemetry_dir, f"{identifier}.csv")
            file_exists = os.path.isfile(csv_filename)

            with open(csv_filename, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=telemetry_dict.keys())
                if not file_exists:
                    writer.writeheader()  # Write header only if the file is new
                writer.writerow(telemetry_dict)
            
            print(f"Telemetry data saved: {csv_filename}")

        except AssertionError as e:
            print(f"Telemetry storage error: {e}")
        except Exception as e:
            print(f"Unexpected error in set_telemetry(): {e}")

    def load_image(self, identifier):
        """Loads and returns image data from a pickle file."""
        try:
            assert isinstance(identifier, str), "Identifier must be a string"

            image_filename = os.path.join(self.image_dir, f"{identifier}.pkl")
            
            if not os.path.exists(image_filename):
                print(f"Image file {image_filename} not found.")
                return None

            with open(image_filename, "rb") as f:
                image_data = pickle.load(f)
                print(f"Image loaded: {image_filename}")
                return image_data

        except AssertionError as e:
            print(f"Load image error: {e}")
        except Exception as e:
            print(f"Unexpected error in load_image(): {e}")
            return None

'''

import os
import shutil
import pickle
import csv
from Binary_CSV_Handler import DataHandler  # Assuming the class is in `data_handler.py`

def setup_test_env():
    """Setup: Ensure a clean test environment before running tests."""
    test_dirs = ["test_images", "test_telemetry"]
    for directory in test_dirs:
        if os.path.exists(directory):
            shutil.rmtree(directory)  # Delete existing test directories
        os.makedirs(directory)

def test_store_and_load_image():
    """Test storing and loading an image."""
    handler = DataHandler(image_dir="test_images", telemetry_dir="test_telemetry")
    image_data = b"\x89PNG\r\n\x1a\nTEST_IMAGE"

    handler.set_image("test1", image_data)
    loaded_data = handler.load_image("test1")

    assert loaded_data == image_data, "Image data mismatch!"
    print("✅ test_store_and_load_image passed!")

def test_store_and_append_telemetry():
    """Test storing and appending telemetry data."""
    handler = DataHandler(image_dir="test_images", telemetry_dir="test_telemetry")

    telemetry1 = {"time": "12:00", "speed": "30km/h", "altitude": "100m"}
    telemetry2 = {"time": "12:10", "speed": "35km/h", "altitude": "105m"}

    handler.set_telemetry("test1", telemetry1)
    handler.set_telemetry("test1", telemetry2)

    csv_file = os.path.join("test_telemetry", "test1.csv")
    assert os.path.exists(csv_file), "CSV file not created!"

    with open(csv_file, "r") as f:
        reader = list(csv.reader(f))
    
    assert len(reader) == 3, "Telemetry rows mismatch!"  # Header + 2 entries
    print("✅ test_store_and_append_telemetry passed!")

def test_multiple_identifiers():
    """Test handling of multiple identifiers."""
    handler = DataHandler(image_dir="test_images", telemetry_dir="test_telemetry")

    handler.set_image("test1", b"IMAGE1")
    handler.set_image("test2", b"IMAGE2")

    assert os.path.exists("test_images/test1.pkl"), "Image file for test1 missing!"
    assert os.path.exists("test_images/test2.pkl"), "Image file for test2 missing!"

    assert handler.load_image("test1") == b"IMAGE1", "Incorrect data for test1"
    assert handler.load_image("test2") == b"IMAGE2", "Incorrect data for test2"

    print("✅ test_multiple_identifiers passed!")

def test_empty_telemetry():
    """Test storing an empty telemetry dictionary."""
    handler = DataHandler(image_dir="test_images", telemetry_dir="test_telemetry")

    handler.set_telemetry("test_empty", {})
    csv_file = os.path.join("test_telemetry", "test_empty.csv")

    assert os.path.exists(csv_file), "Empty CSV file was not created!"
    
    with open(csv_file, "r") as f:
        assert f.read().strip() == "", "Empty telemetry file should have no content!"

    print("✅ test_empty_telemetry passed!")

def test_overwrite_image():
    """Test overwriting an image with new data."""
    handler = DataHandler(image_dir="test_images", telemetry_dir="test_telemetry")

    handler.set_image("overwrite_test", b"OLD_IMAGE")
    handler.set_image("overwrite_test", b"NEW_IMAGE")

    loaded_data = handler.load_image("overwrite_test")
    assert loaded_data == b"NEW_IMAGE", "Image was not overwritten!"

    print("✅ test_overwrite_image passed!")

def test_load_nonexistent_image():
    """Test loading a non-existent image."""
    handler = DataHandler(image_dir="test_images", telemetry_dir="test_telemetry")

    result = handler.load_image("does_not_exist")
    assert result is None, "Expected None when loading a non-existent file!"

    print("✅ test_load_nonexistent_image passed!")

def test_special_characters_in_identifiers():
    """Test identifiers with special characters."""
    handler = DataHandler(image_dir="test_images", telemetry_dir="test_telemetry")

    special_id = "test@123#"
    handler.set_image(special_id, b"SPECIAL_IMAGE")
    handler.set_telemetry(special_id, {"time": "13:00", "speed": "40km/h"})

    assert os.path.exists(f"test_images/{special_id}.pkl"), "Special character image file missing!"
    assert os.path.exists(f"test_telemetry/{special_id}.csv"), "Special character CSV file missing!"

    print("✅ test_special_characters_in_identifiers passed!")

if __name__ == "__main__":
    setup_test_env()
    test_store_and_load_image()
    test_store_and_append_telemetry()
    test_multiple_identifiers()
    test_empty_telemetry()
    test_overwrite_image()
    test_load_nonexistent_image()
    test_special_characters_in_identifiers()

    print("\n All tests passed successfully!")



'''