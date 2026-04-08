import os
import glob
from PIL import Image
import io


class BinToJPEG:
    def __init__(self, image_dir="images", image_output=None):
        try:
            self.image_dir = image_dir
            self.output_dir = image_output or os.path.join(os.getcwd(), "Images")
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            print(f"Init error: {e}")
            raise

    def extract_jpg_from_all_files(self):
        try:
            bin_files = glob.glob(os.path.join(self.image_dir, "*.bin"))

            if not bin_files:
                print(f"No .bin files found in {self.image_dir}")
                return False

            valid_count = 0

            for bin_file in bin_files:
                print(f"Processing: {bin_file}")
                if self.extract_jpg_image(bin_file):
                    valid_count += 1

            return valid_count > 0

        except Exception as e:
            print(f"Error processing all files: {e}")
            return False

    def extract_jpg_image(self, input_file):
        try:
            if not os.path.isfile(input_file):
                return False

            jpg_start = b'\xff\xd8'
            jpg_end = b'\xff\xd9'

            with open(input_file, 'rb') as f:
                data = f.read()

            if not data:
                return False

            # --- Find ALL start and end positions ---
            start_positions = []
            end_positions = []

            i = 0
            while True:
                i = data.find(jpg_start, i)
                if i == -1:
                    break
                start_positions.append(i)
                i += 1

            i = 0
            while True:
                i = data.find(jpg_end, i)
                if i == -1:
                    break
                end_positions.append(i)
                i += 1

            if not start_positions or not end_positions:
                return False

            best_candidate = None

            # --- Try ALL valid (start, end) combinations ---
            for start in start_positions:
                for end in end_positions:
                    if end <= start:
                        continue

                    end_final = end + 2
                    candidate = data[start:end_final]

                    # Reject tiny junk
                    if len(candidate) < 100:
                        continue

                    is_valid = False

                    # --- Tier 1: PIL validation ---
                    try:
                        img = Image.open(io.BytesIO(candidate))
                        img.verify()
                        is_valid = True
                    except Exception:
                        pass

                    # --- Tier 2: structured JPEG ---
                    if not is_valid and (b'JFIF' in candidate or b'Exif' in candidate):
                        is_valid = True

                    if is_valid:
                        if best_candidate is None or len(candidate) > len(best_candidate):
                            best_candidate = candidate

            if best_candidate is None:
                return False

            print(f"Extracted JPG size: {len(best_candidate)} bytes from {input_file}")

            base = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(self.output_dir, f"{base}.jpg")

            with open(output_file, 'wb') as f:
                f.write(best_candidate)

            print(f"Saved: {output_file}")
            return True

        except Exception as e:
            print(f"Error processing '{input_file}': {e}")
            return False

    def get_latest_image(self):
        try:
            files = glob.glob(os.path.join(self.image_dir, "*.bin"))
            return max(files, key=os.path.getmtime) if files else None
        except Exception:
            return None

    def process_latest_image(self):
        latest = self.get_latest_image()
        if not latest:
            return False
        return self.extract_jpg_image(latest)