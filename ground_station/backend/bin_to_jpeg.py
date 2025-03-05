import os

class BinToJPEG:
    def __init__(self):
        pass

    def extract_jpg_image(self, input_file):
        """
        Extracts a JPG image from a binary file and saves it to the 'Images' folder.
        
        :param input_file: Path to the input binary file.
        """
        try:
            # Define the output directory
            output_dir = os.path.join(os.getcwd(), "Images")
            os.makedirs(output_dir, exist_ok=True)

            # JPG start and end markers
            jpg_byte_start = b'\xff\xd8'
            jpg_byte_end = b'\xff\xd9'
            jpg_image = bytearray()

            # Read the binary file
            with open(input_file, 'rb') as f:
                req_data = f.read()

                # Find the start of the JPG image
                start = req_data.find(jpg_byte_start)
                if start == -1:
                    print('Could not find JPG start of image marker!')
                    return

                # Find the end of the JPG image
                end = req_data.find(jpg_byte_end, start) + len(jpg_byte_end)
                jpg_image += req_data[start:end]

                print(f'Size: {end - start} bytes')

            # Save the extracted JPG image to the 'Images' folder
            output_file = os.path.join(output_dir, f'{os.path.basename(input_file)}.jpg')
            with open(output_file, 'wb') as f:
                f.write(jpg_image)

            print(f"Image saved successfully at: {output_file}")

        except FileNotFoundError:
            print(f"Error: '{input_file}' file not found.")
        except Exception as e:
            print(f"Unexpected error: {e}")