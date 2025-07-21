import bin_to_jpeg
import os
import filecmp
import random

IMAGE_DIR = "real_binary_images"
REF_DIR = "reference_images"
NOISY_DIR = "noisy_binary_images"
OUTPUT_DIR = "Images"
    

class TestClass:
    """for testing the class bin to jpeg
    """
    def test_dummy_data(self):
        """
        Test BinToJPEG functionality with dummy data.
        """        
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
        jpg_extractor.extract_jpg_image(test_file)
        
        print("BinToJPEG test completed.")
        
    def test_real_images(self):
        """takes jpeg images that have had their extension changed from .jpeg to .bin, 
        Checks if the resulting images are the same as the original images.
        """
        t = bin_to_jpeg.BinToJPEG(image_dir=IMAGE_DIR)
        t.extract_jpg_from_all_files()
        assert self.compare_files(REF_DIR, OUTPUT_DIR)
        
    def test_real_images_with_noise(self):
        """takes jpeg images that have had their extension changed from .jpeg to .bin, 
        adds binary noise leading up to, and out of the jpeg data.
        Checks if the resulting images are the same as the original images.
        """
        self.noise_sandwich(IMAGE_DIR, NOISY_DIR)
        t = bin_to_jpeg.BinToJPEG(image_dir=NOISY_DIR)
        t.extract_jpg_from_all_files()
        assert self.compare_files(REF_DIR, OUTPUT_DIR)
        
    def test_pure_noise(self):
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
            try:
                os.remove(os.path.join("Images", "noise_test_number_" + str(kb) + ".jpg"))
            except:
                continue
                
            
            
   # def test_empty_file():
   #     """tests an input bin file that is totally empty."""
   #     self.clear_dir(NOISY_DIR)
   #     output_path = os.path.join(NOISY_DIR, "empty")
                
        
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
