import os
import pytest
import pandas as pd
from unittest.mock import patch
import matplotlib
from ground_station.backend.Binary_CSV_Handler import DataHandler 
matplotlib.use('Agg')

@pytest.fixture
def setup_test_environment(tmp_path):
    """Setup test environment with sample data"""
    telemetry_dir = tmp_path / "telemetry"
    database_dir = tmp_path / "database"
    telemetry_dir.mkdir()
    database_dir.mkdir()

    # Create sample test data
    telemetry_data = {
        'Field_0': [1, 2, 3, 4, 5],
        'Field_1': [10, 20, 30, 40, 50],
        'Field_2': [100, 200, 300, 400, 500]
    }
    
    # Create combined telemetry file
    telemetry_df = pd.DataFrame(telemetry_data)
    telemetry_df.to_csv(telemetry_dir / "telemetry.csv", index=False)

    # Create individual field files
    for field, values in telemetry_data.items():
        field_df = pd.DataFrame({field: values})
        field_df.to_csv(database_dir / f"{field}.csv", index=False)

    return telemetry_dir, database_dir

def test_initialization(setup_test_environment):
    """Test that ExpandingGraph initializes correctly with proper file paths"""
    telemetry_dir, database_dir = setup_test_environment
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    assert graph.x_field == "Field_0"
    assert graph.y_field == "Field_1"
    assert os.path.exists(graph.telemetry_file)
    assert os.path.exists(graph.x_file)
    assert os.path.exists(graph.y_file)

def test_check_data_sources(setup_test_environment):
    """Test detection of existing data sources"""
    telemetry_dir, database_dir = setup_test_environment
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))

    # Verify both data sources exist initially
    telemetry_exists, individual_exists = graph.check_data_sources()
    assert telemetry_exists is True
    assert individual_exists is True

    # Safely remove telemetry file and verify detection
    try:
        if os.path.exists(graph.telemetry_file):
            os.remove(graph.telemetry_file)
    except Exception:
        pass
        
    telemetry_exists, individual_exists = graph.check_data_sources()
    assert telemetry_exists is False
    assert individual_exists is True

def test_read_from_telemetry_file(setup_test_environment):
    """Test reading data from telemetry.csv file"""
    telemetry_dir, database_dir = setup_test_environment
    
    # Remove individual files to test telemetry.csv reading in isolation
    for field in ['Field_0', 'Field_1', 'Field_2']:
        field_file = database_dir / f"{field}.csv"
        if field_file.exists():
            field_file.unlink()
    
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    # Test successful data reading
    x_data, y_data = graph.read_from_telemetry_file()
    assert x_data == [1, 2, 3, 4, 5]
    assert y_data == [10, 20, 30, 40, 50]
    
    # Test handling of non-existent field
    graph.x_field = "NonExistent"
    x_data, y_data = graph.read_from_telemetry_file()
    assert x_data is None
    assert y_data is None

def test_read_from_individual_files(setup_test_environment):
    """Test reading data from individual field files"""
    telemetry_dir, database_dir = setup_test_environment
    
    # Remove telemetry.csv to force reading from individual files
    telemetry_file = telemetry_dir / "telemetry.csv"
    if telemetry_file.exists():
        telemetry_file.unlink()
    
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    # Test successful data reading
    x_data, y_data = graph.read_from_individual_files()
    assert x_data == [1, 2, 3, 4, 5]
    assert y_data == [10, 20, 30, 40, 50]
    
    # Test handling when one required file is missing
    (database_dir / "Field_1.csv").unlink()
    x_data, y_data = graph.read_from_individual_files()
    assert x_data is None
    assert y_data is None

def test_update_plot(setup_test_environment):
    """Test that plot updates with correct data"""
    telemetry_dir, database_dir = setup_test_environment
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    # Trigger plot update and verify data
    graph.update_plot(0)
    assert len(graph.x_data) == 5
    assert len(graph.y_data) == 5

    # Verify plotted data matches expected values
    x_data, y_data = graph.line.get_data()
    assert list(x_data) == [1, 2, 3, 4, 5]
    assert list(y_data) == [10, 20, 30, 40, 50]

def test_animation_control():
    """Test animation start/stop functionality"""
    with patch('matplotlib.animation.FuncAnimation'):
        graph = ExpandingGraph("Field_0", "Field_1", "X", "Y", "Test")
        graph.start_animation()
        assert graph.ani is not None
        graph.stop_animation()
        assert graph.ani is None

def test_save_plot(setup_test_environment, tmp_path):
    """Test plot saving functionality"""
    telemetry_dir, database_dir = setup_test_environment
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    # First update plot with data
    graph.update_plot(0)
    
    # Test saving to file
    test_file = tmp_path / "test_plot.png"
    graph.save_plot(str(test_file))
    assert os.path.exists(test_file)

def test_error_handling(setup_test_environment, capsys):
    """Test error handling with malformed data"""
    telemetry_dir, database_dir = setup_test_environment
    
    # Create corrupted telemetry data
    with open(telemetry_dir / "telemetry.csv", 'w') as f:
        f.write("Field_0,Field_1\n1,invalid\n2,20")
    
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    # Test reading handles invalid data gracefully
    x_data, y_data = graph.read_from_telemetry_file()
    assert len(x_data) == 1  # Only the valid row should be processed
    
    # Verify no errors during plot update
    graph.update_plot(0)
    captured = capsys.readouterr()
    assert "Error updating plot" not in captured.out
