import bin_to_jpeg
import os
import filecmp
import random
from pathlib import Path
import shutil

# Get the directory where this test file is located
TEST_DIR = Path(__file__).parent

# Define paths relative to the test directory
IMAGE_DIR = str(TEST_DIR / "real_binary_images")
REF_DIR = str(TEST_DIR / "reference_images")
NOISY_DIR = str(TEST_DIR / "noisy_binary_images")
OUTPUT_DIR = str(TEST_DIR / "Images")


class TestClass:
    """Tests for the BinToJPEG class."""

    def setup_method(self):
        """Clean directories before each test."""
        self.clear_dir(NOISY_DIR)
        self.clear_dir(OUTPUT_DIR)

    def clear_dir(self, dir_path):
        """Deletes all files and folders in a directory. Creates the directory if it doesn't exist."""
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            return
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

    def test_dummy_data(self, tmp_path):
        """Test BinToJPEG functionality with dummy data."""
        os.makedirs(NOISY_DIR, exist_ok=True)

        # Create a dummy bin file with fake JPG markers
        dummy_jpg_data = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'
        test_file = os.path.join(NOISY_DIR, "test_A.bin")
        with open(test_file, 'wb') as f:
            f.write(b'\x00' * 50)  # random data before JPG
            f.write(dummy_jpg_data)
            f.write(b'\x00' * 20)  # random data after JPG

        # Extract JPG
        jpg_extractor = bin_to_jpeg.BinToJPEG(image_output=str(tmp_path / "Images"))
        result = jpg_extractor.extract_jpg_image(test_file)

        assert result is True
        output_file = tmp_path / "Images" / "test_A.jpg"
        assert output_file.exists()

        with open(output_file, 'rb') as f:
            extracted_data = f.read()

        assert extracted_data.startswith(b'\xff\xd8')
        assert extracted_data.endswith(b'\xff\xd9')
        assert len(extracted_data) > 0

        print("BinToJPEG dummy data test completed.")

    def test_real_images(self, tmp_path):
        """Check if converted real .bin images match reference images."""
        output_dir = str(tmp_path / "Images")
        os.makedirs(output_dir, exist_ok=True)

        t = bin_to_jpeg.BinToJPEG(image_dir=IMAGE_DIR, image_output=output_dir)
        t.extract_jpg_from_all_files()

        assert self.compare_files(REF_DIR, output_dir)

    def test_real_images_with_noise(self, tmp_path):
        """Adds noise around bin images and checks extraction."""
        self.noise_sandwich(IMAGE_DIR, NOISY_DIR)
        output_dir = str(tmp_path / "Images")
        os.makedirs(output_dir, exist_ok=True)

        t = bin_to_jpeg.BinToJPEG(image_dir=NOISY_DIR, image_output=output_dir)
        t.extract_jpg_from_all_files()

        if not os.path.exists(REF_DIR) or not os.listdir(REF_DIR):
            raise FileNotFoundError(f"Reference directory {REF_DIR} is empty or does not exist")

        assert self.compare_files(REF_DIR, output_dir)

    def test_pure_noise(self, tmp_path):
        """Generates random noise files and ensures no JPG is falsely extracted."""
        KB_TESTED = 100  # Reduce for speed
        KB_MULTIPLIER = 1024

        for kb in range(KB_TESTED):
            self.clear_dir(NOISY_DIR)
            noise_file = os.path.join(NOISY_DIR, f"noise_test_number_{kb}.bin")
            with open(noise_file, 'wb') as f:
                f.write(os.urandom(kb * KB_MULTIPLIER))

            jpg_extractor = bin_to_jpeg.BinToJPEG(image_dir=NOISY_DIR, image_output=str(tmp_path / "Images"))
            # Should return False for pure noise
            assert not jpg_extractor.extract_jpg_from_all_files()

    def compare_files(self, dir_ref, dir_output):
        """Compares files between reference and output directories."""
        common_files = [f for f in os.listdir(dir_ref) if not f.startswith('.')]
        filecmp.clear_cache()
        match, mismatch, errors = filecmp.cmpfiles(dir_ref, dir_output, common_files, shallow=False)

        print("Matched files:", match)
        print("Mismatched files:", mismatch)
        print("Errored files:", errors)

        return len(mismatch) == 0 and len(errors) == 0 and len(match) == len(common_files)

    def noise_sandwich(self, dir_ref, dir_output):
        """Adds random noise around bin files."""
        self.clear_dir(dir_output)

        NOISE_LENGTH = 1024 * 10  # 10 KB on each side (adjustable)
        for filename in os.listdir(dir_ref):
            with open(os.path.join(dir_ref, filename), 'rb') as f:
                data = f.read()

            noisy_data = os.urandom(NOISE_LENGTH) + data + os.urandom(NOISE_LENGTH)
            with open(os.path.join(dir_output, filename), 'wb') as f:
                f.write(noisy_data)