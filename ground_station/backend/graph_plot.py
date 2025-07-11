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
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        self.ani = None  # <--- Initialize animation object here

        self.x_data = []
        self.y_data = []

        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'r-', label=y_label)
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
        self.ax.legend()
        self.ax.grid(True)

        assert os.path.exists(self.x_path), f"Error: {self.x_path} does not exist!"
        assert os.path.exists(self.y_path), f"Error: {self.y_path} does not exist!"

    def get_title(self):
        """Getter function for the title."""
        return self.title

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

            # Check if the specified columns exist
            assert self.x_label in x_df.columns, (
                f"Column '{self.x_label}' not found in {self.x_path}. "
                f"Available columns: {list(x_df.columns)}"
            )
            assert self.y_label in y_df.columns, (
                f"Column '{self.y_label}' not found in {self.y_path}. "
                f"Available columns: {list(y_df.columns)}"
            )

            # Extract data using the specified column labels
            self.x_data = x_df[self.x_label].tolist()
            self.y_data = y_df[self.y_label].tolist()

            # Assert that extracted data is numeric
            assert all(isinstance(i, (int, float)) for i in self.x_data), "x_data contains non-numeric values!"
            assert all(isinstance(i, (int, float)) for i in self.y_data), "y_data contains non-numeric values!"

            # Update the line data
            self.line.set_data(self.x_data, self.y_data)
            self.ax.relim()  # Adjust axis limits
            self.ax.autoscale_view()
        except Exception as e:
            print(f"Error updating plot: {e}")

        return self.line,

    def start_animation(self, interval=1000):
        """Starts real-time updating of the plot."""
        self.ani = animation.FuncAnimation(
        fig=self.fig,          # Matplotlib figure to animate
        func=self.update_plot, # Frame update callback
        interval=interval,     # Delay between updates (ms)
        blit=False             # Full figure redraw (not optimized)
        )

"""
This script demonstrates how to create a PyQt6 application that displays multiple real-time animated graphs using Matplotlib.

### Key Components:
1. **GraphWindow Class**:
   - A PyQt6 `QMainWindow` subclass that serves as the main application window.
   - Displays multiple real-time graphs in a vertical layout.
   - Each graph is an instance of the `ExpandingGraph` class, which uses Matplotlib for plotting and animation.

2. **ExpandingGraph Class**:
   - Handles the creation and real-time updating of individual graphs.
   - Reads data from CSV files and uses Matplotlib's `FuncAnimation` to update the plots dynamically.

3. **Libraries Used**:
   - **Matplotlib**: For creating and animating graphs.
   - **PyQt6**: For building the GUI application.
   - **Pandas**: For reading and processing CSV data.

### How It Works:
1. **Graph Initialization**:
   - Multiple `ExpandingGraph` instances are created, each representing a real-time graph.
   - Each graph reads data from CSV files and sets up a Matplotlib figure.

2. **PyQt6 GUI Setup**:
   - A `GraphWindow` class inherits from `QMainWindow` to create the application window.
   - A central widget (`QWidget`) and a vertical layout (`QVBoxLayout`) are used to organize the graphs.

3. **Embedding Matplotlib in PyQt6**:
   - For each graph, a `FigureCanvas` is created to embed the Matplotlib figure into the PyQt6 window.
   - The `start_animation()` method is called to begin real-time updates for each graph.

4. **Application Execution**:
   - The PyQt6 application is started with `QApplication`.
   - The main window (`GraphWindow`) is displayed, and the event loop begins with `app.exec()`.

### Example Usage:
```python
class GraphWindow(QMainWindow):
    def __init__(self, graphs):
        super().__init__()
        self.setWindowTitle("Real-Time Graphs")  # Set window title
        self.setGeometry(100, 100, 1200, 800)  # Set window size and position

        # Create a central widget and layout
        central_widget = QWidget()              # Central widget for the main window
        self.setCentralWidget(central_widget)   # Set it as the main window's central widget
        layout = QVBoxLayout(central_widget)    # Use a vertical layout to organize graphs

        # Add each graph to the window
        for graph in graphs:
            # Create a Matplotlib FigureCanvas to embed the graph in the PyQt6 window
            canvas = FigureCanvas(graph.fig)
            layout.addWidget(canvas)            # Add the canvas to the layout
            graph.start_animation()             # Start the animation for the graph


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
    app = QApplication(sys.argv)  # Create the PyQt6 application instance
    window = GraphWindow(graphs)  # Create the main window with the list of graphs
    window.show()                 # Display the window
    sys.exit(app.exec())          # Start the application event loop"
    """