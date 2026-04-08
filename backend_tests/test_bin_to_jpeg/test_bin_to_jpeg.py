import bin_to_jpeg
import os
import shutil
from pathlib import Path
from PIL import Image
import io

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
        """Checks extracted images match reference images."""
        output_dir = str(tmp_path / "Images")
        os.makedirs(output_dir, exist_ok=True)

        t = bin_to_jpeg.BinToJPEG(image_dir=IMAGE_DIR, image_output=output_dir)
        t.extract_jpg_from_all_files()

        assert self.compare_files(REF_DIR, output_dir)

    def test_real_images_with_noise(self, tmp_path):
        """Adds true random noise around images and verifies extraction."""
        self.noise_sandwich(IMAGE_DIR, NOISY_DIR)

        output_dir = str(tmp_path / "Images")
        os.makedirs(output_dir, exist_ok=True)

        t = bin_to_jpeg.BinToJPEG(image_dir=NOISY_DIR, image_output=output_dir)
        t.extract_jpg_from_all_files()

        if not os.path.exists(REF_DIR) or not os.listdir(REF_DIR):
            raise FileNotFoundError(f"Reference directory {REF_DIR} is empty or does not exist")

        assert self.compare_files(REF_DIR, output_dir)

    def test_pure_noise(self, tmp_path):
        """Generate true random noise and ensure no invalid JPGs are produced."""
        KB_TESTED = 100
        KB_MULTIPLIER = 1024

        output_dir = str(tmp_path / "Images")
        os.makedirs(output_dir, exist_ok=True)

        for kb in range(KB_TESTED):
            self.clear_dir(NOISY_DIR)
            self.clear_dir(output_dir)

            noise_file = os.path.join(NOISY_DIR, f"noise_{kb}.bin")
            with open(noise_file, 'wb') as f:
                f.write(os.urandom(kb * KB_MULTIPLIER))

            jpg_extractor = bin_to_jpeg.BinToJPEG(
                image_dir=NOISY_DIR,
                image_output=output_dir
            )

            result = jpg_extractor.extract_jpg_from_all_files()

            # If something was extracted, validate it's a real JPEG
            if result:
                for file in os.listdir(output_dir):
                    file_path = os.path.join(output_dir, file)

                    with open(file_path, 'rb') as f:
                        data = f.read()

                    # Must have JPEG markers
                    assert data.startswith(b'\xff\xd8')
                    assert data.endswith(b'\xff\xd9')

                    # Must be a valid image
                    try:
                        img = Image.open(io.BytesIO(data))
                        img.verify()
                    except Exception:
                        assert False, "Invalid JPEG extracted from pure noise"
            else:
                # If nothing extracted, that's also valid
                assert len(os.listdir(output_dir)) == 0

    def compare_files(self, dir_ref, dir_output):
        """Compares all files with the same names between two directories."""
        ref_files = sorted([f for f in os.listdir(dir_ref) if not f.startswith('.')])
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
        """Adds true random noise before and after each binary image."""
        self.clear_dir(dir_output)
        os.makedirs(dir_output, exist_ok=True)

        noise_length = 1024 * 10  # 10 KB on each side

        for filename in os.listdir(dir_ref):
            if filename.startswith('.'):
                continue

            with open(os.path.join(dir_ref, filename), 'rb') as f:
                data = f.read()

            noisy_data = os.urandom(noise_length) + data + os.urandom(noise_length)

            output_path = os.path.join(dir_output, filename)
            with open(output_path, 'wb') as f:
                f.write(noisy_data)

    def clear_dir(self, dir_path):
        """Deletes all files in a directory."""
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        else:
            os.makedirs(dir_path, exist_ok=True)