import os
import glob

class BinToJPEG:
    def __init__(self, image_dir="images"):
        """
        Initialize BinToJPEG with the image directory path.
        
        :param image_dir: Directory where binary image files are stored (matches DataHandler)
        """
        self.image_dir = image_dir
        # Ensure the output directory exists
        self.output_dir = os.path.join(os.getcwd(), "Images")
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_jpg_from_all_files(self):
        """
        Extract JPG images from all .bin files in the image directory.
        """
        try:
            # Get all .bin files from the image directory
            bin_files = glob.glob(os.path.join(self.image_dir, "*.bin"))
            
            if not bin_files:
                print(f"No .bin files found in {self.image_dir}")
                return
            
            for bin_file in bin_files:
                print(f"Processing: {bin_file}")
                self.extract_jpg_image(bin_file)
                
        except Exception as e:
            print(f"Error processing all files: {e}")

    def extract_jpg_image(self, input_file):
        """
        Extracts a JPG image from a binary file and saves it to the 'Images' folder.
        
        :param input_file: Path to the input binary file.
        """
        try:
            # Ensure input file exists
            if not os.path.isfile(input_file):
                print(f"File '{input_file}' does not exist.")
                return False

            # JPG start and end markers
            jpg_byte_start = b'\xff\xd8'
            jpg_byte_end = b'\xff\xd9'
            jpg_image = bytearray()

            # Read the binary file
            with open(input_file, 'rb') as f:
                req_data = f.read()

            # Check if file is empty
            if len(req_data) == 0:
                print(f"File '{input_file}' is empty.")
                return False

            # Find the start of the JPG image
            start = req_data.find(jpg_byte_start)
            if start == -1:
                print(f"Could not find JPG start marker in '{input_file}'")
                return False

            # Find the final instance of the end marker for the JPG image
            end = req_data.rfind(jpg_byte_end)
            if end == -1:
                print(f"Could not find JPG end marker in '{input_file}'")
                return False

            end += len(jpg_byte_end)
            jpg_image += req_data[start:end]

            print(f'Extracted JPG size: {end - start} bytes from {input_file}')

            if len(jpg_image) == 0:
                print(f"Extracted image size is zero from '{input_file}'")
                return False

            # Save the extracted JPG image to the 'Images' folder
            base_filename = os.path.splitext(os.path.basename(input_file))[0]  # Remove .bin extension
            output_file = os.path.join(self.output_dir, f'{base_filename}.jpg')
            
            with open(output_file, 'wb') as f:
                f.write(jpg_image)

            print(f"Image saved successfully at: {output_file}")
            return True

        except Exception as e:
            print(f"Unexpected error processing '{input_file}': {e}")
            return False

    def get_latest_image(self):
        """
        Get the most recently created binary image file.
        
        :return: Path to the most recent .bin file, or None if no files exist
        """
        try:
            bin_files = glob.glob(os.path.join(self.image_dir, "*.bin"))
            if not bin_files:
                return None
            
            # Return the most recently modified file
            latest_file = max(bin_files, key=os.path.getmtime)
            return latest_file
            
        except Exception as e:
            print(f"Error getting latest image: {e}")
            return None

    def process_latest_image(self):
        """
        Process the most recently created binary image file.
        """
        latest_file = self.get_latest_image()
        if latest_file:
            print(f"Processing latest image: {latest_file}")
            return self.extract_jpg_image(latest_file)
        else:
            print("No binary image files found to process.")
            return False


# Test functionality with dummy data
def test_bin_to_jpeg():
    """
    Test the BinToJPEG functionality with dummy data.
    """
    print("Testing BinToJPEG class...")
    
    # Create test directory and dummy binary file
    test_dir = "test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a dummy binary file with fake JPG markers for testing
    dummy_jpg_data = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'  # Fake JPG data
    test_file = os.path.join(test_dir, "test_A_1.bin")
    
    with open(test_file, 'wb') as f:
        f.write(b'\x00' * 50)  # Some random data before JPG
        f.write(dummy_jpg_data)  # JPG data
        f.write(b'\x00' * 20)   # Some random data after JPG
    
    # Test the BinToJPEG class
    jpg_extractor = BinToJPEG(test_dir)
    jpg_extractor.extract_jpg_image(test_file)
    
    # Clean up test files
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    shutil.rmtree("Images", ignore_errors=True)
    
    print("BinToJPEG test completed.")


if __name__ == "__main__":
    test_bin_to_jpeg()