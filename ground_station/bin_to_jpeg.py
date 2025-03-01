import os
import sys

import numpy as np
from PIL import Image

class BinToJPEG:
    def __init__(self, width=720, height=480, channels=3):
        self.width = width
        self.height = height
        self.channels = channels

    def convert(self, input_file, output_file):
        """Reads a binary file, converts it to an image, and saves it as a JPEG."""
        try:
            with open(input_file, "rb") as f:
                d = np.fromfile(f, dtype=np.uint8, count=self.width * self.height * self.channels)

            # Ensure correct shape
            if d.size != self.width * self.height * self.channels:
                raise ValueError("File size does not match expected dimensions for an RGB image.")

            d = d.reshape((self.height, self.width, self.channels))

            # Convert to PIL Image and save as JPEG
            image = Image.fromarray(d, mode="RGB")
            # output_path = os.path.join(os.getcwd(), output_file)
            output_path = "C:\COMP_SLIP-GS\ground_station"
            image.save(output_path, format="JPEG")

            print(f"Image saved successfully at: {output_path}")

        except FileNotFoundError:
            print(f"Error: '{input_file}' file not found.")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

# Example usage
if __name__ == "__main__":
    converter = BinToJPEG()
    converter.convert()
