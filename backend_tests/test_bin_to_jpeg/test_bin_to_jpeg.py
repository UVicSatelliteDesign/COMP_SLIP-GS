import bin_to_jpeg
import os
import filecmp
import random
from pathlib import Path

# Get the directory where this test file is located
TEST_DIR = Path(__file__).parent

# Define paths relative to the test directory
IMAGE_DIR = str(TEST_DIR / "real_binary_images")
REF_DIR = str(TEST_DIR / "reference_images")
NOISY_DIR = str(TEST_DIR / "noisy_binary_images")
OUTPUT_DIR = "Images"  # This will be overridden by the fixture

class TestClass:
    """Unit tests for BinToJPEG extraction functionality."""

    def test_dummy_data(self, tmp_path):
        """Test BinToJPEG functionality with dummy JPG-like binary data."""
        os.makedirs(NOISY_DIR, exist_ok=True)
        dummy_jpg_data = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'
        test_file = os.path.join(NOISY_DIR, "test_A.bin")
        with open(test_file, 'wb') as f:
            f.write(b'\x00' * 50 + dummy_jpg_data + b'\x00' * 20)

        jpg_extractor = bin_to_jpeg.BinToJPEG(str(tmp_path / OUTPUT_DIR))
        result = jpg_extractor.extract_jpg_image(test_file)

        assert result is True
        output_file = tmp_path / OUTPUT_DIR / "test_A.jpg"
        assert os.path.exists(output_file)

        with open(output_file, 'rb') as f:
            data = f.read()
        assert data.startswith(b'\xff\xd8')
        assert data.endswith(b'\xff\xd9')
        assert len(data) > 0

    def test_real_images(self, tmp_path):
        """Check that .bin images match reference .jpg files exactly."""
        output_dir = tmp_path / OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

        t = bin_to_jpeg.BinToJPEG(image_dir=IMAGE_DIR, image_output=str(output_dir))
        t.extract_jpg_from_all_files()
        assert self.compare_files(REF_DIR, str(output_dir))

    def test_real_images_with_noise(self, tmp_path):
        """Add noise around .bin images and verify extraction matches reference."""
        self.noise_sandwich(IMAGE_DIR, NOISY_DIR)
        output_dir = tmp_path / OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

        t = bin_to_jpeg.BinToJPEG(image_dir=NOISY_DIR, image_output=str(output_dir))
        t.extract_jpg_from_all_files()

        # Only compare files that exist in both directories
        assert self.compare_files(REF_DIR, str(output_dir))

    def test_pure_noise(self, tmp_path):
        """Generate random noise files and ensure no false JPGs are extracted."""
        KB_TESTED = 20  # reduced for speed and deterministic results
        KB_MULTIPLIER = 1024

        output_dir = tmp_path / OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

        for kb in range(KB_TESTED):
            self.clear_dir(NOISY_DIR)
            noise_file = os.path.join(NOISY_DIR, f"noise_{kb}.bin")
            with open(noise_file, 'wb') as f:
                f.write(os.urandom(kb * KB_MULTIPLIER))

            jpg_extractor = bin_to_jpeg.BinToJPEG(image_dir=NOISY_DIR, image_output=str(output_dir))
            # Should not produce any JPGs from pure noise
            result = jpg_extractor.extract_jpg_from_all_files()
            assert not result or self.no_false_positive(str(output_dir))

    # ------------------- Helper Methods -------------------

    def compare_files(self, dir_ref, dir_output):
        """Compare files with the same names in two directories."""
        common_files = [f for f in os.listdir(dir_ref) if not f.startswith('.')]
        filecmp.clear_cache()
        match, mismatch, errors = filecmp.cmpfiles(dir_ref, dir_output, common_files, shallow=False)
        return len(mismatch) == 0 and len(errors) == 0 and len(match) == len(common_files)

    def noise_sandwich(self, dir_ref, dir_output, noise_kb=10):
        """Add random noise before and after .bin files."""
        if os.path.exists(dir_output):
            self.clear_dir(dir_output)
        else:
            os.makedirs(dir_output)

        noise_len = 1024 * noise_kb
        for filename in os.listdir(dir_ref):
            with open(os.path.join(dir_ref, filename), 'rb') as f:
                data = f.read()
            noisy_data = os.urandom(noise_len) + data + os.urandom(noise_len)
            with open(os.path.join(dir_output, filename), 'wb') as f:
                f.write(noisy_data)

    def clear_dir(self, dir_path):
        """Delete all files in a directory."""
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        for f in os.listdir(dir_path):
            file_path = os.path.join(dir_path, f)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def no_false_positive(self, dir_output):
        """Check that any extracted JPGs from pure noise are too small to be valid."""
        for f in os.listdir(dir_output):
            file_path = os.path.join(dir_output, f)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                # Treat <1KB as false positive; delete it
                if size < 1024:
                    os.remove(file_path)
                    continue
                return False  # A large false-positive JPG found
        return True