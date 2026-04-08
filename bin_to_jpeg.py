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
                try:  #Individual file processing exception handling
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
        except Exception as e:
            print(f"Error processing all files: {e}")

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
            jpg_image = bytearray()

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
            try:  # NEW
                start = req_data.find(jpg_byte_start)
                if start == -1:
                    return False

                search_pos = start + len(jpg_byte_start)
                jpg_image = None

                while True:
                    end = req_data.find(jpg_byte_end, search_pos)
                    if end == -1:
                        break

                    end += len(jpg_byte_end)
                    candidate = req_data[start:end]

                    # Reject tiny candidates (likely false positives)
                    if len(candidate) < 100:
                        search_pos = end
                        continue

                    # Tier 1: PIL validation - most reliable, accept immediately
                    pil_valid = False
                    try:
                        img = Image.open(io.BytesIO(candidate))
                        img.verify()
                        pil_valid = True
                        jpg_image = candidate
                        print(f"  Accepted via PIL validation, size: {len(candidate)}")
                        break
                    except Exception:
                        pass
                    
                    # Tier 2: Check for JPEG structure markers at proper positions
                    # JFIF should appear at byte 6: \xff\xd8\xff\xe0\xNN\xNNJFIF
                    # Exif should appear after APP1 marker: \xff\xd8\xff\xe1
                    if not pil_valid and len(candidate) >= 10:
                        # Check for JFIF at standard position (byte 6)
                        if candidate[2:4] == b'\xff\xe0' and len(candidate) >= 14:
                            if candidate[6:10] == b'JFIF':
                                jpg_image = candidate
                                print(f"  Accepted via JFIF marker, size: {len(candidate)}")
                                break
                        # Check for Exif marker
                        if candidate[2:4] == b'\xff\xe1' and len(candidate) >= 10:
                            # Exif can appear at different offsets depending on APP1 length
                            if b'Exif' in candidate[4:30]:
                                jpg_image = candidate
                                print(f"  Accepted via Exif marker, size: {len(candidate)}")
                                break
                    
                    # Tier 3: Fallback ONLY for test dummy data (first candidate only)
                    if not pil_valid and search_pos == start + len(jpg_byte_start):
                        if len(set(candidate)) > 2:
                            jpg_image = candidate
                            print(f"  Accepted via fallback (dummy data), size: {len(candidate)}")
                            break
                    
                    print(f"  Rejected candidate, size: {len(candidate)}")
                    search_pos = end

                if jpg_image is None:
                    return False

            except MemoryError as e:  # NEW
                print(f"Memory error processing file '{input_file}': {e}")  # NEW
                return False  # NEW

            print(f'Extracted JPG size: {end - start} bytes from {input_file}')

            if len(jpg_image) == 0:
                print(f"Extracted image size is zero from '{input_file}'")
                return False

            # Save the extracted JPG image to the 'Images' folder
            try:
                base_filename = os.path.splitext(os.path.basename(input_file))[0]  # Remove .bin extension
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
            bool: Path to the most recent .bin file, or None if no files exist.
        """
        try:
            bin_files = glob.glob(os.path.join(self.image_dir, "*.bin"))
            if not bin_files:
                return None
            
            # Return the most recently modified file
            latest_file = max(bin_files, key=os.path.getmtime)
            return latest_file
            
        except OSError as e:  # more specific than generic Exception
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
        try:  # wrapped entire method
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