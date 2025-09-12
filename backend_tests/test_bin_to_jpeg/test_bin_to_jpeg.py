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
    """for testing the class bin to jpeg"""
    def test_dummy_data(self, tmp_path):
        """Test BinToJPEG functionality with dummy data."""
        # Create test directory and dummy binary file
        os.makedirs(NOISY_DIR, exist_ok=True)
        
        # Create a dummy binary file with fake JPG markers for testing
        dummy_jpg_data = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'  # Fake JPG data
        test_file = os.path.join(NOISY_DIR, "test_A.bin")
        
        with open(test_file, 'wb') as f:
            f.write(b'\x00' * 50)  # Some random data before JPG
            f.write(dummy_jpg_data)  # JPG data
            f.write(b'\x00' * 20)   # Some random data after JPG
        
        # Test the BinToJPEG class
        jpg_extractor = bin_to_jpeg.BinToJPEG(OUTPUT_DIR)
        result = jpg_extractor.extract_jpg_image(test_file)
        
        assert result == True #JPG extraction should succeed
        assert os.path.exists(os.path.join(tmp_path / "Images", "test_A.jpg")) #JPG file should be created
        
        # Assert that the output file has the correct content
        expected_output = str(tmp_path / "Images" / "test_A.jpg")
        with open(expected_output, 'rb') as f:
            extracted_data = f.read()
        
        # Should contain the JPG markers and data we put in
        assert extracted_data.startswith(b'\xff\xd8') #Output should start with JPG start marker
        assert extracted_data.endswith(b'\xff\xd9') #Output should end with JPG end marker
        assert len(extracted_data) > 0 #Output file should not be empty
        
        print("BinToJPEG test completed.")
        
    def test_real_images(self, tmp_path):
        """takes jpeg images that have had their extension changed from .jpeg to .bin, 
        Checks if the resulting images are the same as the original images.
        """
        t = bin_to_jpeg.BinToJPEG(image_dir=IMAGE_DIR)
        t.extract_jpg_from_all_files()
        assert self.compare_files(REF_DIR, str(tmp_path / "Images"))
        
    def test_real_images_with_noise(self, tmp_path):
        """takes jpeg images that have had their extension changed from .jpeg to .bin, 
        adds binary noise leading up to, and out of the jpeg data.
        Checks if the resulting images are the same as the original images.
        """
        self.noise_sandwich(IMAGE_DIR, NOISY_DIR)
        t = bin_to_jpeg.BinToJPEG(image_dir=NOISY_DIR)
        t.extract_jpg_from_all_files()
        assert self.compare_files(REF_DIR, str(tmp_path / "Images"))
        
    def test_pure_noise(self, tmp_path):
        KB_TESTED = 1000 # different lengths of random noise tested, up until KB_TESTED
        KB_MULTIPLIER = 1024 # multiplier for the number of bits in a kb
        FILENAME = "noise_test_number_"
        
        def random_bytes(length):
            """Generates a random sequence of bytes"""
            return os.urandom(length)
                
        for kb in range(KB_TESTED):
            # empty the directory for noisy files.
            self.clear_dir(NOISY_DIR)
            output_path = os.path.join(NOISY_DIR, "noise_test_number_" + str(kb) + ".bin")
            with open(output_path, 'wb') as f:
                f.write(random_bytes(kb*KB_MULTIPLIER))
            jpg_extractor = bin_to_jpeg.BinToJPEG(NOISY_DIR)
            assert not jpg_extractor.extract_jpg_from_all_files()
            # Clean up from the temporary directory (not the real Images folder)
            try:
                temp_image_path = os.path.join(str(tmp_path / "Images"), "noise_test_number_" + str(kb) + ".jpg")
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
            except:
                continue
                
    def compare_files(self, dir_ref, dir_output):
        """Compares all files with the same names between two directories,
        byte by byte.

        Args:
            dir_ref (str): Path to the reference directory.
            dir_output (str): Path to the output directory to compare.

        Returns:
            bool: True if all files match exactly, False otherwise.
        """
        # Get files that exist in the reference directory, excluding hidden files
        common_files = [f for f in os.listdir(dir_ref) if not f.startswith('.')]
        print(dir_ref, dir_output)

        print(common_files)

        # unpack matching and mismatching files as a list (also errors if those occur)
        filecmp.clear_cache()
        match, mismatch, errors = filecmp.cmpfiles(dir_ref, dir_output, common_files, shallow=False)

        print("Matched files:", match)
        print("Mismatched files:", mismatch)
        print("Errored files:", errors)

        # check to see if all processed files match their originals prior to transmission
        return len(mismatch) == 0 and len(errors) == 0 and len(match) == len(common_files)

    def noise_sandwich(self, dir_ref, dir_output):
        """concatenates noise to the start and end of bin files.

        Args:
            dir_ref (binary file): the source directory containing only .bin files
            dir_output (binary file): the output directory for the new noisy files.
        """

        # Define how many random bytes to add at the start and end of each file
        LOWER = 1
        UPPER = 1000
        NOISE_LENGTH = 1024*random.randint(LOWER,UPPER)  # LOWER-UPPER KB of noise on each side
        NOISE_LENGTH = 1024*100 # high failure rate beyond 7 KB of noise on each side...
        # when noise is added to the start and end of the file, there is a high incidence
        # of false positive images generated. I assume at this range, the starting and end sequence
        # of JPG images occurs by chance.

        # Function to generate a given number of random bytes
        def random_bytes(length):
            """Generates a random sequence of bytes"""
            return os.urandom(length)

        # Process each file in the source directory
        for filename in os.listdir(dir_ref):

            # Read the binary data from the source file
            with open(os.path.join(dir_ref, filename), 'rb') as f:
                data = f.read()

            # Create new data by adding random noise before and after the original data
            noisy_data = random_bytes(NOISE_LENGTH) + data + random_bytes(NOISE_LENGTH)

            # Write the noisy data to a new file in the output directory
            output_path = os.path.join(dir_output, filename)
            with open(output_path, 'wb') as f:
                f.write(noisy_data)
                
    def clear_dir(self, dir):
        """Deletes all the files in a directory, for testing purposes."""
        shredder = os.listdir(dir)
        for file in shredder:
            os.remove(os.path.join(dir, file))
