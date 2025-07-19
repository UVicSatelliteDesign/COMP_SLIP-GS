import os
import pytest
import pandas as pd
from unittest.mock import patch
import matplotlib
matplotlib.use('Agg')

@pytest.fixture
def setup_test_environment(tmp_path):
    telemetry_dir = tmp_path / "telemetry"
    database_dir = tmp_path / "database"
    telemetry_dir.mkdir()
    database_dir.mkdir()

    telemetry_data = {
        'Field_0': [1, 2, 3, 4, 5],
        'Field_1': [10, 20, 30, 40, 50],
        'Field_2': [100, 200, 300, 400, 500]
    }
    telemetry_df = pd.DataFrame(telemetry_data)
    telemetry_df.to_csv(telemetry_dir / "telemetry.csv", index=False)

    for field, values in telemetry_data.items():
        field_df = pd.DataFrame({field: values})
        field_df.to_csv(database_dir / f"{field}.csv", index=False)

    return telemetry_dir, database_dir

def test_initialization(setup_test_environment):
    telemetry_dir, database_dir = setup_test_environment
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir)
    
    assert graph.x_field == "Field_0"
    assert graph.y_field == "Field_1"
    assert os.path.exists(graph.telemetry_file)
    assert os.path.exists(graph.x_file)
    assert os.path.exists(graph.y_file)

def test_check_data_sources(setup_test_environment):
    telemetry_dir, database_dir = setup_test_environment
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))

    telemetry_exists, individual_exists = graph.check_data_sources()
    assert telemetry_exists is True
    assert individual_exists is True

    os.remove(graph.telemetry_file)
    telemetry_exists, individual_exists = graph.check_data_sources()
    assert telemetry_exists is False
    assert individual_exists is True

def test_read_from_telemetry_file(setup_test_environment):
    telemetry_dir, database_dir = setup_test_environment
    for field in ['Field_0', 'Field_1', 'Field_2']:
        field_file = database_dir / f"{field}.csv"
        if field_file.exists():
            field_file.unlink()
    
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    x_data, y_data = graph.read_from_telemetry_file()
    assert x_data == [1, 2, 3, 4, 5]
    assert y_data == [10, 20, 30, 40, 50]
    
    graph.x_field = "NonExistent"
    x_data, y_data = graph.read_from_telemetry_file()
    assert x_data is None
    assert y_data is None

def test_read_from_individual_files(setup_test_environment):
    telemetry_dir, database_dir = setup_test_environment
    telemetry_file = telemetry_dir / "telemetry.csv"
    if telemetry_file.exists():
        telemetry_file.unlink()
    
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    x_data, y_data = graph.read_from_individual_files()
    assert x_data == [1, 2, 3, 4, 5]
    assert y_data == [10, 20, 30, 40, 50]
    
    (database_dir / "Field_1.csv").unlink()
    x_data, y_data = graph.read_from_individual_files()
    assert x_data is None
    assert y_data is None

def test_update_plot(setup_test_environment):
    telemetry_dir, database_dir = setup_test_environment
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    graph.update_plot(0)
    assert len(graph.x_data) == 5
    assert len(graph.y_data) == 5

    x_data, y_data = graph.line.get_data()
    assert list(x_data) == [1, 2, 3, 4, 5]
    assert list(y_data) == [10, 20, 30, 40, 50]

def test_animation_control():
    with patch('matplotlib.animation.FuncAnimation'):
        graph = ExpandingGraph("Field_0", "Field_1", "X", "Y", "Test")
        graph.start_animation()
        assert graph.ani is not None
        graph.stop_animation()
        assert graph.ani is None

def test_save_plot(setup_test_environment, tmp_path):
    telemetry_dir, database_dir = setup_test_environment
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    graph.update_plot(0)
    
    test_file = tmp_path / "test_plot.png"
    graph.save_plot(str(test_file))
    assert os.path.exists(test_file)

def test_error_handling(setup_test_environment, capsys):
    telemetry_dir, database_dir = setup_test_environment
    with open(telemetry_dir / "telemetry.csv", 'w') as f:
        f.write("Field_0,Field_1\n1,invalid\n2,20")
    
    graph = ExpandingGraph(
        "Field_0", "Field_1", "X", "Y", "Test",
        str(telemetry_dir), str(database_dir))
    
    x_data, y_data = graph.read_from_telemetry_file()
    assert len(x_data) == 1
    
    graph.update_plot(0)
    captured = capsys.readouterr()
    assert "Error updating plot" not in captured.out
