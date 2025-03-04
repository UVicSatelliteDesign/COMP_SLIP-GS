#!usr/bin/env python3
import sys

import bin_to_jpeg as BinToJPEG

def main():
  # Hardcoded file path
  file_name = r"bin_images\IMG_1006-1.bin"  # Replace with your file path

  # Create an instance of the BinToJPEG converter
  converter = BinToJPEG.BinToJPEG()

  # Extract the JPG image from the binary file
  converter.extract_jpg_image(file_name)
  return 0

if __name__=="__main__":
  exit(main())
