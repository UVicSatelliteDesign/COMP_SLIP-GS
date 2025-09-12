import sys
import os
from pathlib import Path
import pytest

def pytest_configure(config):
    """Ensure backend is importable by adding it to sys.path once at startup."""
    backend_path = Path(__file__).resolve().parents[2] / "ground_station" / "backend"
    sys.path.insert(0, str(backend_path))

@pytest.fixture(autouse=True)
def mock_output_directory(tmp_path, monkeypatch):
    """Redirect BinToJPEG output into pytest's tmp_path/Images instead of the real project folder."""
    import bin_to_jpeg

    def mock_init(self, image_dir="images"):
        self.image_dir = image_dir
        self.output_dir = str(tmp_path / "Images")
        os.makedirs(self.output_dir, exist_ok=True)

    monkeypatch.setattr(bin_to_jpeg.BinToJPEG, "__init__", mock_init)
    return tmp_path