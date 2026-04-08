import bin_to_jpeg
import os
import random
import shutil
from pathlib import Path

# Get the directory where this test file is located
TEST_DIR = Path(__file__).parent

# Define paths relative to the test directory
IMAGE_DIR = str(TEST_DIR / "real_binary_images")
REF_DIR = str(TEST_DIR / "reference_images")
NOISY_DIR = str(TEST_DIR / "noisy_binary_images")
OUTPUT_DIR = "Images"  # overridden per test with tmp_path


class TestClass:
    """for testing the class bin to jpeg"""

    def setup_method(self):
        """Clean test input directories before each test."""
        self.clear_dir(NOISY_DIR)

    def test_dummy_data(self, tmp_path):
        """Test BinToJPEG functionality with dummy data."""
        os.makedirs(NOISY_DIR, exist_ok=True)

        dummy_jpg_data = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'
        test_file = os.path.join(NOISY_DIR, "test_A.bin")

        with open(test_file, 'wb') as f:
            f.write(b'\x00' * 50)
            f.write(dummy_jpg_data)
            f.write(b'\x00' * 20)

        output_dir = str(tmp_path / "Images")
        os.makedirs(output_dir, exist_ok=True)

        jpg_extractor = bin_to_jpeg.BinToJPEG(image_output=output_dir)
        result = jpg_extractor.extract_jpg_image(test_file)

        assert result is True
        expected_output = os.path.join(output_dir, "test_A.jpg")
        assert os.path.exists(expected_output)

        with open(expected_output, 'rb') as f:
            extracted_data = f.read()

        assert extracted_data.startswith(b'\xff\xd8')
        assert extracted_data.endswith(b'\xff\xd9')
        assert len(extracted_data) > 0

    def test_real_images(self, tmp_path):
        """takes jpeg images that have had their extension changed from .jpeg to .bin,
        Checks if the resulting images are the same as the original images.
        """
        output_dir = str(tmp_path / "Images")
        os.makedirs(output_dir, exist_ok=True)

        t = bin_to_jpeg.BinToJPEG(image_dir=IMAGE_DIR, image_output=output_dir)
        t.extract_jpg_from_all_files()

        assert self.compare_files(REF_DIR, output_dir)

    def test_real_images_with_noise(self, tmp_path):
        """takes jpeg images that have had their extension changed from .jpeg to .bin,
        adds deterministic binary noise leading up to, and out of the jpeg data.
        Checks if the resulting images are the same as the original images.
        """
        self.noise_sandwich(IMAGE_DIR, NOISY_DIR)

        output_dir = str(tmp_path / "Images")
        os.makedirs(output_dir, exist_ok=True)

        t = bin_to_jpeg.BinToJPEG(image_dir=NOISY_DIR, image_output=output_dir)
        t.extract_jpg_from_all_files()

        if not os.path.exists(REF_DIR) or not os.listdir(REF_DIR):
            raise FileNotFoundError(f"Reference directory {REF_DIR} is empty or does not exist")

        assert self.compare_files(REF_DIR, output_dir)

    def test_pure_noise(self, tmp_path):
        """Generates random-looking noise files and ensures no JPGs are extracted."""
        KB_TESTED = 100
        KB_MULTIPLIER = 1024

        output_dir = str(tmp_path / "Images")
        os.makedirs(output_dir, exist_ok=True)

        for kb in range(KB_TESTED):
            self.clear_dir(NOISY_DIR)
            self.clear_dir(output_dir)

            output_path = os.path.join(NOISY_DIR, f"noise_test_number_{kb}.bin")
            with open(output_path, 'wb') as f:
                f.write(self.noise_bytes(kb * KB_MULTIPLIER))

            jpg_extractor = bin_to_jpeg.BinToJPEG(image_dir=NOISY_DIR, image_output=output_dir)
            result = jpg_extractor.extract_jpg_from_all_files()

            assert not result
            assert len(os.listdir(output_dir)) == 0

    def compare_files(self, dir_ref, dir_output):
        """Compares all files with the same names between two directories, byte by byte."""
        common_files = [f for f in os.listdir(dir_ref) if not f.startswith('.')]

        ref_files = sorted(common_files)
        out_files = sorted([f for f in os.listdir(dir_output) if not f.startswith('.')])
        if ref_files != out_files:
            print("Reference files:", ref_files)
            print("Output files:", out_files)
            return False

        for filename in ref_files:
            ref_path = os.path.join(dir_ref, filename)
            out_path = os.path.join(dir_output, filename)

            with open(ref_path, 'rb') as f1, open(out_path, 'rb') as f2:
                if f1.read() != f2.read():
                    print("Mismatch in:", filename)
                    return False

        return True

    def noise_sandwich(self, dir_ref, dir_output):
        """Concatenates deterministic noise to the start and end of bin files.

        Noise is generated without byte 0xFF, so JPEG markers cannot appear by chance.
        """
        self.clear_dir(dir_output)
        os.makedirs(dir_output, exist_ok=True)

        noise_length = 1024 * 10  # 10 KB on each side
        for filename in os.listdir(dir_ref):
            if filename.startswith('.'):
                continue

            with open(os.path.join(dir_ref, filename), 'rb') as f:
                data = f.read()

            noisy_data = self.noise_bytes(noise_length) + data + self.noise_bytes(noise_length)

            output_path = os.path.join(dir_output, filename)
            with open(output_path, 'wb') as f:
                f.write(noisy_data)

    def noise_bytes(self, length):
        """Generate deterministic noise bytes that never include 0xFF."""
        rng = random.Random(12345 + length)
        return bytes(rng.randrange(0, 255) for _ in range(length))

    def clear_dir(self, dir_path):
        """Deletes all files in a directory, for testing purposes."""
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        else:
            os.makedirs(dir_path, exist_ok=True)