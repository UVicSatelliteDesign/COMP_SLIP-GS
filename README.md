# UVR_SLIP-GS
UVR SLIP ground station

## Running the application

### Install dependencies

Create a virtual environment:
```sh
python -m venv venv
```

Install dependencies:
```sh
source venv/bin/activate
pip install -r requirements.txt
```

### Run

To launch the GUI:
```sh
python3 -m ground_station.frontend.main_window
```

To run tests:
```sh
pytest
```
