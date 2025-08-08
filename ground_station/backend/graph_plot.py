import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

class ExpandingGraph:
    def __init__(self, x_field, y_field, x_label, y_label, title, telemetry_dir="telemetry", database_dir="database"):
        """
        Initialize the ExpandingGraph with field names and directories.
        
        :param x_field: Field name for X-axis data (e.g., "Field_0")
        :param y_field: Field name for Y-axis data (e.g., "Field_1")
        :param x_label: Label for X-axis
        :param y_label: Label for Y-axis
        :param title: Graph title
        :param telemetry_dir: Directory where telemetry.csv is stored
        :param database_dir: Directory where individual field CSV files are stored
        """
        self.x_field = x_field
        self.y_field = y_field
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        self.telemetry_dir = telemetry_dir
        self.database_dir = database_dir
        
        # File paths
        self.telemetry_file = os.path.join(telemetry_dir, "telemetry.csv")
        self.x_file = os.path.join(database_dir, f"{x_field}.csv")
        self.y_file = os.path.join(database_dir, f"{y_field}.csv")
        
        self.ani = None
        self.x_data = []
        self.y_data = []

        # Create matplotlib figure and axis
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.line, = self.ax.plot([], [], 'r-', label=y_label, linewidth=2)
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        
        # Create directories if they don't exist
        os.makedirs(self.telemetry_dir, exist_ok=True)
        os.makedirs(self.database_dir, exist_ok=True)

    def get_title(self):
        """Getter function for the title."""
        return self.title

    def check_data_sources(self):
        """
        Check if data sources exist and are accessible.
        
        :return: Tuple (telemetry_exists, individual_files_exist)
        """
        telemetry_exists = os.path.exists(self.telemetry_file) and os.path.getsize(self.telemetry_file) > 0
        x_file_exists = os.path.exists(self.x_file) and os.path.getsize(self.x_file) > 0
        y_file_exists = os.path.exists(self.y_file) and os.path.getsize(self.y_file) > 0
        
        return telemetry_exists, (x_file_exists and y_file_exists)

    def read_from_telemetry_file(self):
        """
        Read data from the main telemetry.csv file.
        
        :return: Tuple (x_data, y_data) or (None, None) if failed
        """
        try:
            if not os.path.exists(self.telemetry_file) or os.path.getsize(self.telemetry_file) == 0:
                return None, None
            
            df = pd.read_csv(self.telemetry_file)
            
            if df.empty:
                return None, None
            
            # Check if the required fields exist
            if self.x_field not in df.columns or self.y_field not in df.columns:
                print(f"Warning: Required fields '{self.x_field}' or '{self.y_field}' not found in telemetry.csv")
                print(f"Available columns: {list(df.columns)}")
                return None, None
            
            # Convert to numeric, coerce errors to NaN
            x_data = pd.to_numeric(df[self.x_field], errors='coerce').dropna().tolist()
            y_data = pd.to_numeric(df[self.y_field], errors='coerce').dropna().tolist()
            
            # Ensure both lists have the same length
            min_len = min(len(x_data), len(y_data))
            return x_data[:min_len], y_data[:min_len]
            
        except Exception as e:
            print(f"Error reading from telemetry file: {e}")
            return None, None

    def read_from_individual_files(self):
        """
        Read data from individual CSV files in the database directory.
        
        :return: Tuple (x_data, y_data) or (None, None) if failed
        """
        try:
            # Check if both files exist and are not empty
            if not (os.path.exists(self.x_file) and os.path.getsize(self.x_file) > 0):
                return None, None
            if not (os.path.exists(self.y_file) and os.path.getsize(self.y_file) > 0):
                return None, None
            
            x_df = pd.read_csv(self.x_file)
            y_df = pd.read_csv(self.y_file)
            
            if x_df.empty or y_df.empty:
                return None, None
            
            # Check if the required columns exist
            if self.x_field not in x_df.columns:
                print(f"Warning: Field '{self.x_field}' not found in {self.x_file}")
                return None, None
            if self.y_field not in y_df.columns:
                print(f"Warning: Field '{self.y_field}' not found in {self.y_file}")
                return None, None
            
            # Convert to numeric, coerce errors to NaN
            x_data = pd.to_numeric(x_df[self.x_field], errors='coerce').dropna().tolist()
            y_data = pd.to_numeric(y_df[self.y_field], errors='coerce').dropna().tolist()
            
            # Ensure both lists have the same length
            min_len = min(len(x_data), len(y_data))
            return x_data[:min_len], y_data[:min_len]
            
        except Exception as e:
            print(f"Error reading from individual files: {e}")
            return None, None

    def update_plot(self, frame):
        """Updates the graph dynamically by reading the latest data."""
        try:
            # Check data sources
            telemetry_exists, individual_files_exist = self.check_data_sources()
            
            x_data, y_data = None, None
            
            # Try to read from individual files first (more reliable)
            if individual_files_exist:
                x_data, y_data = self.read_from_individual_files()
            
            # If individual files failed, try telemetry file
            if (x_data is None or y_data is None) and telemetry_exists:
                x_data, y_data = self.read_from_telemetry_file()
            
            # If we have valid data, update the plot
            if x_data is not None and y_data is not None and len(x_data) > 0 and len(y_data) > 0:
                self.x_data = x_data
                self.y_data = y_data
                
                # Update the line data
                self.line.set_data(self.x_data, self.y_data)
                
                # Adjust axis limits
                self.ax.relim()
                self.ax.autoscale_view()
            
        except Exception as e:
            print(f"Error updating plot '{self.title}': {e}")

        return self.line,

    def start_animation(self, interval=1000):
        """Starts real-time updating of the plot."""
        try:
            self.ani = animation.FuncAnimation(
                fig=self.fig,
                func=self.update_plot,
                interval=interval,
                blit=False,
                cache_frame_data=False
            )
        except Exception as e:
            print(f"Error starting animation for '{self.title}': {e}")

    def stop_animation(self):
        """Stops the animation."""
        if self.ani is not None:
            self.ani.event_source.stop()
            self.ani = None

    def save_plot(self, filename=None):
        """
        Save the current plot to a file.
        
        :param filename: Output filename (optional)
        """
        if filename is None:
            filename = f"{self.title.replace(' ', '_')}.png"
        
        try:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Plot saved as {filename}")
        except Exception as e:
            print(f"Error saving plot: {e}")


# Test functionality with dummy data
def test_expanding_graph():
    """
    Test the ExpandingGraph functionality with dummy data.
    """
    print("Testing ExpandingGraph class...")
    
    # Create test directories
    test_telemetry_dir = "test_telemetry"
    test_database_dir = "test_database"
    os.makedirs(test_telemetry_dir, exist_ok=True)
    os.makedirs(test_database_dir, exist_ok=True)
    
    # Create dummy telemetry data
    telemetry_data = {
        'Field_0': [1, 2, 3, 4, 5],
        'Field_1': [10, 20, 30, 40, 50],
        'Field_2': [100, 200, 300, 400, 500]
    }
    
    # Save to telemetry.csv
    telemetry_df = pd.DataFrame(telemetry_data)
    telemetry_df.to_csv(os.path.join(test_telemetry_dir, "telemetry.csv"), index=False)
    
    # Save to individual field files
    for field, values in telemetry_data.items():
        field_df = pd.DataFrame({field: values})
        field_df.to_csv(os.path.join(test_database_dir, f"{field}.csv"), index=False)
    
    # Test the ExpandingGraph class
    graph = ExpandingGraph(
        x_field="Field_0",
        y_field="Field_1", 
        x_label="Time",
        y_label="Temperature",
        title="Temperature vs Time",
        telemetry_dir=test_telemetry_dir,
        database_dir=test_database_dir
    )
    
    # Test data reading
    telemetry_exists, individual_files_exist = graph.check_data_sources()
    print(f"Telemetry file exists: {telemetry_exists}")
    print(f"Individual files exist: {individual_files_exist}")
    
    # Test data reading from individual files
    x_data, y_data = graph.read_from_individual_files()
    print(f"Individual files data - X: {x_data}, Y: {y_data}")
    
    # Test data reading from telemetry file
    x_data, y_data = graph.read_from_telemetry_file()
    print(f"Telemetry file data - X: {x_data}, Y: {y_data}")
    
    # Test plot update
    graph.update_plot(0)
    print(f"Plot updated successfully. X data: {graph.x_data}, Y data: {graph.y_data}")
    
    # Clean up test files
    import shutil
    shutil.rmtree(test_telemetry_dir, ignore_errors=True)
    shutil.rmtree(test_database_dir, ignore_errors=True)
    
    print("ExpandingGraph test completed.")


# Example usage showing how to create multiple graphs
def create_example_graphs():
    """
    Example of how to create multiple graphs that work with DataHandler output.
    """
    graphs = [
        ExpandingGraph("Field_0", "Field_1", "Time", "Temperature", "Temperature vs Time"),
        ExpandingGraph("Field_0", "Field_2", "Time", "Pressure", "Pressure vs Time"),
        ExpandingGraph("Field_1", "Field_2", "Temperature", "Pressure", "Pressure vs Temperature"),
        ExpandingGraph("Field_0", "Field_3", "Time", "Altitude", "Altitude vs Time"),
        ExpandingGraph("Field_0", "Field_4", "Time", "Gyro", "Gyro vs Time")
    ]
    
    return graphs


if __name__ == "__main__":
    test_expanding_graph()