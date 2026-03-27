import sys
import os
import shutil
import pytest
import numpy as np
import random
import gc
import time
from PIL import Image

# For type hints
from pytestqt.qtbot import QtBot
from PyQt6.QtWidgets import QApplication
from _pytest.capture import CaptureFixture

# To match type of components
from PyQt6.QtWidgets import QLabel

# Helper components
from ground_station.frontend.data_api import ImageAPI
from pathlib import Path
from PyQt6.QtGui import QImage

# Widget to test
from ground_station.frontend.main_window import GroundStationMainWindow

DIR_PATH = Path("front_end_tests") / "unit_tests" / "imgs"  # Path for directory in which test images are created
DEFAULT_MAX_IMGS = 50   # Default upper-limit for no. of images used in testing

# Hook for optional user input of custom upper-limit for the no. of images to test with
def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--max_images",
        action="store",
        default=DEFAULT_MAX_IMGS,
        type=int,
        help="Max no. of images to generate for stress test"
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "count" in metafunc.fixturenames:
        max_images = metafunc.config.getoption("max_images")

        if not isinstance(max_images, int) or max_images <= 0:
            print(f"Invalid input for --max_images. Using default value of {DEFAULT_MAX_IMGS}")
            max_images = DEFAULT_MAX_IMGS

        metafunc.parametrize("count", range(1, max_images+1))


# Class which generates different types of images for testing
class GenerateDummyImage:
    def __init__(self,
                 dir_path: Path):
        """
        :param dir_path: Directory path where the images generated will be stored.
        """

        self.dir_path = dir_path
        self.dir_path.mkdir(parents=True, exist_ok=True)    # Makes the directory if it doesnt already exist


    def generate_valid_image(self,
                             file_name: str) -> Path:
        """
        Generates a valid random RGB image.

        :param file_name: Name of image file (include `.jpg`)
        """

        image_path = self.dir_path / file_name
        width, height = 580, 400

        random_pixels = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        image = Image.fromarray(random_pixels, 'RGB')
        image.save(image_path, 'JPEG')

        return image_path


    def generate_corrupted_image(self,
                                 file_name: str):
        """
        Generates a corrupted image file with random binary data.

        :param file_name: Name of image file (include `.jpg`)
        """

        image_path = self.dir_path / file_name

        random_size = random.randint(100, 10000)
        random_data = os.urandom(random_size)

        with open(image_path, "wb") as f:
            f.write(random_data)
    

    def delete_contents(self):
        """
        Deletes all the contents of the directory refered to by `dir_path`.
        """

        for item in self.dir_path.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)


# Fixtures
@pytest.fixture(scope="session")
def image_generator(dir_path: Path = DIR_PATH):
    """
    Provides a `GenerateDummyImage` instance to use for image generation.

    :param dir_path: File path of directory in which test images will be stored.
    """

    gen = GenerateDummyImage(dir_path)

    yield gen   # Yeilds control of GenerateDummyImage instance to tests

    gc.collect()    # To trigger Python's garbage collection so temporary directory can be deleted

    # Deletes directory and all its contents after all tests using this fixture are done
    if dir_path.exists() and dir_path.is_dir():
        try:
            time.sleep(1)   # To give the OS time to release locks
            shutil.rmtree(dir_path)
        except Exception as e:
            print(f"Failed to deleted temporary directory. Error:{e}")
    # Deletes directory and all its contents after all tests using this fixture are done
    if dir_path.exists() and dir_path.is_dir():
        try:
            time.sleep(1)   # To give the OS time to release locks
            shutil.rmtree(dir_path)
        except Exception as e:
            print(f"Failed to deleted temporary directory. Error:{e}")


@pytest.fixture
def widget(qapp: QApplication,
           qtbot: QtBot,
           dir_path: Path = DIR_PATH) -> GroundStationMainWindow:
    """
    Provides a `GroundStationMainWindow` instance whose `ImageAPI` path is set to `dir_path` and
    whose timers have been stopped.

    :param qapp: Fixture providing `Qt` application context.
    :param qtbot: Fixture for widget interaction.
    :param dir_path: File path of directory from which `ImageAPI` is going to fetch images.
    """

    # Replacement ImageAPI with the desired directory path for testing
    replacement_image_api = ImageAPI(dir_path)

    w = GroundStationMainWindow()
    w.image_api = replacement_image_api # Replaces the default ImageAPI with the testing version
    w.image_timer.stop()  # Stops the timer to prevent automatic image updates

    qtbot.addWidget(w)

    return w


class TestMainWindowImageDisplay:
    def test_image_display_initialization(self,
                                          qapp: QApplication,
                                          qtbot: QtBot,
                                          widget: GroundStationMainWindow):
        """
        Tests if the image display in `GroundStationMainWindow` initializes correctly.

        Specifically tests:
        - If the image label is a `QLabel` instance.
        - If the label text is set to "No image available".
        - If the label does not have a pixmap set initially.

        :param qapp: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        :param widget: Instance of `GroundStationMainWindow` to use in test.
        """

        image = widget.image_label

        # Checks if image display area is a QLabel instance
        assert isinstance(image, QLabel), f"Expected a QLabel instance, got {type(image).__name__}"
        
        # Checks if default text of image display area is correct
        assert image.text() == "No image available", \
            f'Expected "No image available", got "{image.text()}"'
        
        # Checks if no image is being displayed by default
        assert image.pixmap() is None or image.pixmap().isNull(), \
            "By default, the image label should not have a pixmap set."
    

    def test_image_display_with_valid_image(self,
                                            qapp: QApplication,
                                            qtbot: QtBot,
                                            widget: GroundStationMainWindow,
                                            image_generator: GenerateDummyImage,
                                            count: int):
        """
        Tests if images are displayed properly if only valid images is fetched by `ImageAPI`.
        `count` no. of valid images are generated.

        Specifically Tests:
        - Text in the image display area has been removed.
        - An image is being displayed.
        - The image being displayed matches the image generated.

        :param qapp: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        :param widget: Instance of `GroundStationMainWindow` to use in test.
        :param image_generator: Instance of `GenerateDummyImage` which is used to generate 
        valid images.
        :param count: No. of images to use for test.
        """

        # Skip tests if count is less than or equal to 1, as it will cause the tests to run with 0
        # images
        if(count <= 1):
            pytest.skip("Not enough images to test mixed behaviour")

        for i in range(1, count):
            image_path = image_generator.generate_valid_image(f"valid{i}.jpg")

            widget.update_image_display()
            image = widget.image_label

            # Checks if text on image display area is removed
            assert not image.text(), f'Expected no text, got "{image.text()}"'

            # Checks if image display area is displaying an image
            assert (image.pixmap() is not None) and (not image.pixmap().isNull()), \
                "Expected image to exist"

            # Checks if the image being displayed is the same as the image generated
            original = QImage(str(image_path))
            displayed = image.pixmap().toImage()

            assert original == displayed, "Original image and image displayed not same"
        
        image_generator.delete_contents()   # Deleting images created during test
    

    def test_image_display_with_corrupted_image(self,
                                                qapp: QApplication,
                                                qtbot: QtBot,
                                                widget: GroundStationMainWindow,
                                                image_generator: GenerateDummyImage,
                                                count: int):
        """
        Tests if proper text is displayed everytime if only corrupted images is fetched by 
        `ImageAPI`.
        `count` no. of corrupted images are generated.

        Specifically Tests:
        - No image is currently being displayed.
        - The proper message is being displayed in the image display area.

        :param qapp: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        :param widget: Instance of `GroundStationMainWindow` to use in test.
        :param image_generator: Instance of `GenerateDummyImage` which is used to generate 
        corrupted images.
        :param count: No. of images to use for test.
        """

        for i in range(1, count):
            image_generator.generate_corrupted_image(f"corrupted{i}.jpg")

            widget.update_image_display()
            image = widget.image_label

            # Checks if no image is currently being displayed
            assert image.pixmap() is None or image.pixmap().isNull(), "Expected no image to be displayed"

            # Checks if proper message is being displayed in the image display area
            assert image.text() == "Error loading image", \
                f'Expected "Error loading image", got {image.text()}'
        
        image_generator.delete_contents()   # Deleting images created during test


    def test_image_display_error_handling(self,
                                          qapp: QApplication,
                                          qtbot: QtBot,
                                          monkeypatch: pytest.MonkeyPatch,
                                          capsys: CaptureFixture,
                                          widget: GroundStationMainWindow):
        """
        Tests if image display handles unexpected exceptions properly.

        :param qapp: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `GraphDisplayLayout`.
        :param monkeypatch: Fixture used to patch `ImageAPI.get_latest_image_path()`.
        :param capsys: Fixture for capturing `stdout`/`stderr` output.
        :param widget: Instance of `GroundStationMainWindow` to use in test.
        """

        # Mock version of get_latest_image_path() of ImageAPI which always raises an error
        def raise_error():
            raise Exception("Unexpected Exception")
        
        # Monkey-patch the ImageAPI's get_latest_image_path() method raise_error() to force image
        # display to hit exception handler.
        monkeypatch.setattr(
            widget.image_api,
            "get_latest_image_path",
            raise_error
        )

        widget.update_image_display()
        image = widget.image_label

        # Checks if error message was printed to console
        captured = capsys.readouterr()
        assert "Error updating image display: Unexpected Exception" in captured.out, \
            f"Expected error message to be printed" 

        # Checks if no image is being displayed in image display area
        assert image.pixmap() is None or image.pixmap().isNull(), "Expected no image to be displayed"

        # Checks if proper message is being displayed in image display area
        assert image.text() == "Error loading image", \
            f'Expected "Error loading image", got {image.text()}'
    

    def test_image_display_with_mixed_images(self,
                                             qapp: QApplication,
                                             qtbot: QtBot,
                                             widget: GroundStationMainWindow,
                                             image_generator: GenerateDummyImage,
                                             count: int):
        """
        Tests if image display functions properly for a mixed series of valid and corrupted image
        inputs.

        :param qapp: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        :param widget: Instance of `GroundStationMainWindow` to test.
        :param image_generator: Instance of `GenerateDummyImage` which is used to generate a valid image.
        :param count: No. of images to use in test.
        """

        # Skip tests if count is less than or equal to 1, as it will cause the tests to run with 0
        # images
        if(count <= 1):
            pytest.skip("Not enough images to test mixed behaviour")

        indices = list(range(1, count))  # Total images

        # Randomly selects images to be corrupted
        corrupted_indices = set(random.sample(indices, random.randint(1, count-1)))

        for i in indices:
            filename = f"mixed{i}.jpg"
            is_corrupt = i in corrupted_indices

            # Generates image depending on image type
            if is_corrupt:
                image_generator.generate_corrupted_image(filename)
            else:
                image_path = image_generator.generate_valid_image(filename)

            widget.update_image_display()
            image = widget.image_label

            # Checks expected output base on image type
            if is_corrupt:
                # Checks if no image is currently being displayed
                assert image.pixmap() is None or image.pixmap().isNull(), "Expected no image to be displayed"

                # Checks if proper message is being displayed in the image display area
                assert image.text() == "Error loading image", \
                    f'Expected "Error loading image", got {image.text()}'
            else:
                # Checks if text on image display area is removed
                assert not image.text(), f'Expected no text, got "{image.text()}"'

                # Checks if image display area is displaying an image
                assert (image.pixmap() is not None) and (not image.pixmap().isNull()), \
                    "Expected image to exist"

                # Checks if the image being displayed is the same as the image generated
                original = QImage(str(image_path))
                displayed = image.pixmap().toImage().convertToFormat(original.format())

                assert original.size() == displayed.size(), \
                    "Original and displayed image sizes differ"

                assert original.bits().asstring(original.sizeInBytes()) == \
                    displayed.bits().asstring(displayed.sizeInBytes()), \
                        "Original image and image displayed not same"

        image_generator.delete_contents()   # Deleting images created during test