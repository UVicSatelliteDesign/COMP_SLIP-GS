import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation


# Get the base directory (moves up from backend/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")


class ExpandingGraph:
    def __init__(self, x_file, y_file, x_label, y_label, title):
        self.x_path = os.path.join(DATABASE_DIR, x_file)
        self.y_path = os.path.join(DATABASE_DIR, y_file)

        self.x_data = [] #initialize x_data and y_data
        self.y_data = [] 

        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'r-', label=y_label)  # Red line plot
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
        self.ax.legend()
        self.ax.grid(True)

        # Assert that the CSV files exist before proceeding
        assert os.path.exists(self.x_path), f"Error: {self.x_path} does not exist!"
        assert os.path.exists(self.y_path), f"Error: {self.y_path} does not exist!"

    def get_title(self):
        """Getter function for the title."""
        return self._title

    def update_plot(self, frame):
        """Updates the graph dynamically by reading the latest CSV data."""
        try:
            # Assert that files still exist before reading
            assert os.path.exists(self.x_path), f"File missing: {self.x_path}"
            assert os.path.exists(self.y_path), f"File missing: {self.y_path}"

            x_df = pd.read_csv(self.x_path)
            y_df = pd.read_csv(self.y_path)

            # Assert that CSV files are not empty
            assert not x_df.empty, f"Error: {self.x_path} is empty!"
            assert not y_df.empty, f"Error: {self.y_path} is empty!"

            # Extract the first column (assuming numeric values)
            self.x_data = x_df.iloc[:, 0].tolist()
            self.y_data = y_df.iloc[:, 0].tolist()

            # Assert that extracted data is numeric
            assert all(isinstance(i, (int, float)) for i in self.x_data), "Error: x_data contains non-numeric values!"
            assert all(isinstance(i, (int, float)) for i in self.y_data), "Error: y_data contains non-numeric values!"

            # Update the line data
            self.line.set_data(self.x_data, self.y_data)
            self.ax.relim()  # Adjust axis limits
            self.ax.autoscale_view()
        except Exception as e:
            print(f"Error updating plot: {e}")

        return self.line,

    def start_animation(self, interval=1000):
        """Starts real-time updating of the plot."""
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=interval, blit=False)

"""
Example usage:

class GraphWindow(QMainWindow):
    def __init__(self, graphs):
        super().__init__()
        self.setWindowTitle("Real-Time Graphs")
        self.setGeometry(100, 100, 1200, 800)

        # Create a central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add each graph to the window
        for graph in graphs:
            canvas = FigureCanvas(graph.fig)
            layout.addWidget(canvas)
            graph.start_animation()

if __name__ == "__main__":
    # Create instances for each graph
    graphs = [
        ExpandingGraph("longitude.csv", "latitude.csv", "Longitude", "Latitude", "Latitude vs Longitude"),
        ExpandingGraph("altitude.csv", "pressure.csv", "Altitude", "Pressure", "Pressure vs Altitude"),
        ExpandingGraph("time.csv", "altitude.csv", "Time", "Altitude", "Altitude vs Time"),
        ExpandingGraph("altitude.csv", "temperature.csv", "Altitude", "Temperature", "Temperature vs Altitude"),
        ExpandingGraph("time.csv", "gyro.csv", "Time", "Gyro", "Gyro vs Time")
    ]

    # Start the PyQt6 application
    app = QApplication(sys.argv)
    window = GraphWindow(graphs)
    window.show()
    sys.exit(app.exec())
"""