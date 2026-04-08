import os
import glob
from PIL import Image
import io


class BinToJPEG:
    def __init__(self, image_dir="images", image_output=None):
        """
        Initialize BinToJPEG with the image directory path.
        
        :param image_dir: Directory where binary image files are stored (matches DataHandler)
        """
        try:
            self.image_dir = image_dir
            # Ensure the output directory exists
            self.output_dir = image_output or os.path.join(os.getcwd(), "Images")
            os.makedirs(self.output_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating output directory: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error in BinToJPEG initialization: {e}")
            raise

    def extract_jpg_from_all_files(self):
        """
        Extract JPG images from all .bin files in the image_dir directory.
        Writes to the image_dir directory.
        """
        try:
            # Get all .bin files from the image directory
            bin_files = glob.glob(os.path.join(self.image_dir, "*.bin"))
    
            if not bin_files:
                print(f"No .bin files found in {self.image_dir}")
                return False

            valid_count = 0
            for bin_file in bin_files:
                try:
                    print(f"Processing: {bin_file}")
                    result = self.extract_jpg_image(bin_file)
                    if result:
                        valid_count += 1
                except Exception as e: 
                    print(f"Error processing file {bin_file}: {e}")
                    continue

            return valid_count > 0
            
        except OSError as e:
            print(f"Error accessing directory {self.image_dir}: {e}")
            return False
        except Exception as e:
            print(f"Error processing all files: {e}")
            return False

    def extract_jpg_image(self, input_file):
        """Extracts a JPG image from a binary file and saves it to the self.output directory.

        Args:
            input_file (str): the path to the .bin file to be converted to jpg. 
            
        Returns:
            bool: False if there was an error in processing, otherwise True.
        """
        try:
            # Ensure input file exists
            if not os.path.isfile(input_file):
                print(f"File '{input_file}' does not exist.")
                return False

            # JPG start and end markers
            jpg_byte_start = b'\xff\xd8'
            jpg_byte_end = b'\xff\xd9'
            jpg_image = None

            # Read the binary file
            try:
                with open(input_file, 'rb') as f:
                    req_data = f.read()
            except IOError as e:
                print(f"Error reading file '{input_file}': {e}")
                return False 
            except PermissionError as e:
                print(f"Permission denied reading file '{input_file}': {e}")
                return False 

            # Check if file is empty
            if len(req_data) == 0:
                print(f"File '{input_file}' is empty.")
                return False

            # Find the start of the JPG image
            try:
                start = req_data.find(jpg_byte_start)
                if start == -1:
                    return False

                search_pos = start + len(jpg_byte_start)

                while True:
                    end = req_data.find(jpg_byte_end, search_pos)
                    if end == -1:
                        break

                    end += len(jpg_byte_end)
                    candidate = req_data[start:end]

                    # Reject tiny candidates
                    if len(candidate) < 100:
                        search_pos = end
                        continue

                    # STRICT validation: only accept real JPEGs
                    try:
                        img = Image.open(io.BytesIO(candidate))
                        img.verify()
                        jpg_image = candidate
                        break
                    except Exception:
                        search_pos = end
                        continue

                if jpg_image is None:
                    return False

            except MemoryError as e:
                print(f"Memory error processing file '{input_file}': {e}")
                return False

            print(f'Extracted JPG size: {len(jpg_image)} bytes from {input_file}')

            if len(jpg_image) == 0:
                print(f"Extracted image size is zero from '{input_file}'")
                return False

            # Save the extracted JPG image to the 'Images' folder
            try:
                base_filename = os.path.splitext(os.path.basename(input_file))[0]
                output_file = os.path.join(self.output_dir, f'{base_filename}.jpg')
                
                with open(output_file, 'wb') as f:
                    f.write(jpg_image)
            except IOError as e:
                print(f"Error writing output file '{output_file}': {e}")
                return False 
            except PermissionError as e: 
                print(f"Permission denied writing to '{output_file}': {e}")
                return False 
            except OSError as e:
                print(f"OS error writing file '{output_file}': {e}")
                return False

            print(f"Image saved successfully at: {output_file}")
            return True

        except Exception as e:
            print(f"Unexpected error processing '{input_file}': {e}")
            return False

    def get_latest_image(self):
        """
        Get the most recently created binary image file.
        
        Returns:
            Path to the most recent .bin file, or None if no files exist.
        """
        try:
            bin_files = glob.glob(os.path.join(self.image_dir, "*.bin"))
            if not bin_files:
                return None
            
            # Return the most recently modified file
            latest_file = max(bin_files, key=os.path.getmtime)
            return latest_file
            
        except OSError as e:
            print(f"Error accessing directory {self.image_dir}: {e}")
            return None
        except ValueError as e:
            print(f"Error finding latest file: {e}")
            return None
        except Exception as e:
            print(f"Error getting latest image: {e}")
            return None

    def process_latest_image(self):
        """Process the most recently created binary image file.

        Returns:
            bool: returns False if there was an error, otherwise True.
        """
        try:
            latest_file = self.get_latest_image()
            if latest_file:
                print(f"Processing latest image: {latest_file}")
                return self.extract_jpg_image(latest_file)
            else:
                print("No binary image files found to process.")
                return False
        except Exception as e:
            print(f"Error processing latest image: {e}")
            return False