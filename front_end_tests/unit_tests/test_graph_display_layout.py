import sys
import pytest
import matplotlib.pyplot as plt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from concurrent.futures import ThreadPoolExecutor

# For type hints
from _pytest.capture import CaptureFixture
from pytestqt.qtbot import QtBot
from typing import Callable

# To match type of components
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QApplication, QPushButton

# Widgets to test
from ground_station.frontend.graphs_display.graph_display_layout import GraphDisplayLayout
from ground_station.frontend.graphs_display.graph_display_area import GraphDisplayArea, DefaultDisplay
from ground_station.frontend.graphs_display.graph_wrapper_class import GraphWrapperClass

DEFAULT_MAX_NO_OF_GRAPHS = 6 # Default upper-limit for no. of graphs used in testing

# Hook for optional user input of custom upper-limit for the no. of graphs to test with
def pytest_addoption(parser: pytest.Parser) -> None:
    """
    `pytest` hook to customize upper-limit of no. of graphs to be used in testing.
    Default upper limit is stored in `DEFAULT_MAX_NO_OF_GRAPHS`.

    :param parser: `pytest` command line parser object.
    """

    parser.addoption(
        "--max-graphs",
        action = "store",
        default = DEFAULT_MAX_NO_OF_GRAPHS,
        type = int,
        help = "Max graph count for parametrize",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    `pytest` hook for dynamic parametrization of test functions.

    If a function uses a `count` fixture, this hook parametrizes it with a range from 0 to the value
    obtained from `--max-graphs` on the command line.

    :param metafunc: `Metafunc` object for the test function.
    """

    if "count" in metafunc.fixturenames:
        max_graphs = metafunc.config.getoption("max-graphs")

        # Error handling of user-input
        if max_graphs <= 0 or not isinstance(max_graphs, int):
            print(f"Invalid input for --max-graphs. Using default value of {DEFAULT_MAX_NO_OF_GRAPHS}")
            max_graphs = DEFAULT_MAX_NO_OF_GRAPHS

        metafunc.parametrize("count", range(0, max_graphs+1))


# Mock version of ExpandingGraph class
class DummyGraph:
    def __init__(self, title: str = "Dummy"):
        self.fig = plt.figure()
        self.title = title
    

    def get_title(self) -> str:
        return self.title
    

    def start_animation(self, interval):
        pass


# Fixtures
@pytest.fixture(scope="session")
def app() -> QApplication:
    """
    Provides a single `QApplication` instance for all tests.
    """

    return QApplication(sys.argv)


@pytest.fixture(autouse=True)
def disable_background_threads(monkeypatch: pytest.MonkeyPatch):
    """
    Prevents `start_thread()` in `GraphDisplayArea` from spawning real threads.
    """

    monkeypatch.setattr(GraphDisplayArea, "start_thread", lambda self, graph: None)


@pytest.fixture
def widget(app: QApplication,
           qtbot: QtBot,
           dummy_graphs: Callable[[int], list[DummyGraph]]) -> GraphDisplayLayout:
    """
    Provides a `GraphDisplayLayout` instance initialized with 1 `DummyGraph` and registers it with `qtbot`
    for proper event-loop handling and cleanup.
    """

    graphs = dummy_graphs(1)
    w = GraphDisplayLayout(graphs)

    qtbot.addWidget(w)

    return w


@pytest.fixture
def dummy_graphs() -> Callable[[int], list[DummyGraph]]:
    """
    Provides a factory for creating `DummyGraph` instances.
    """

    def _factory(count: int) -> list[DummyGraph]:
        return [DummyGraph(f"Graph {i+1}") for i in range(count)]
    
    return _factory


# Tests for GraphDisplayLayout in graph_display_layout.py
class TestGraphDisplayLayout:
    def test_layout_initialization(self,
                                   app: QApplication,
                                   qtbot: QtBot,
                                   dummy_graphs: Callable[[int], list[DummyGraph]],
                                   count: int):
        """
        Tests if the GUI of `GraphDisplayLayout` initializes correctly.

        Specifically tests:
        - If each `DummyGraph` object is properly wrapped in a `GraphWrapperClass` object.
        - If the no. of buttons matches the no. of graphs in the input.
        - If the `QStackedLayout` has the correct number of graphs.
        - `DefaultDisplay` is the default `QWidget` in the `QStackedLayout`

        :param app: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        :param dummy_graphs: Factory which returns `count` `DummyGraph` instances.
        :param count: No. of graphs to test with.
        """

        graphs = dummy_graphs(count)
        widget = GraphDisplayLayout(graphs)
        qtbot.addWidget(widget)

        area = widget.graphs_display

        # Checks if correct no. of graphs have been created
        assert len(widget.graphs) == count, f"Expected {count} graphs, got {len(widget.graphs)}"

        # Testing each graph for correct wrapper class implementation
        for index, wrapper in enumerate(widget.graphs, start=1):
            # Checks if wrapper class is an instance of GraphWrapperClass
            assert isinstance(wrapper, GraphWrapperClass), \
                f"Graph {index}: Expected a GraphWrapperClass instance, got {type(wrapper).__name__}"
            
            # Checks if wrapper class has expected ID and if title of graph has been preserved
            assert wrapper.get_id() == index, f"Expected {index}, got {wrapper.get_id()}"
            assert wrapper.get_title() == graphs[index-1].get_title(), \
                f"Expected \"{graphs[index-1].get_title()}\", got \"{wrapper.get_title()}\""

            # Checks if the wrapper class contains a FigureCanvasQTAgg to display the graph
            current_widget = area.stackedLayout.widget(index)
            canvas = current_widget.findChild(FigureCanvas)
            
            assert canvas is not None, "Expected a FigureCanvasQTAgg instance inside GraphWrapperClass"

        # Checks if the no. of buttons matches the no. of graphs in the input
        buttons = widget.findChildren(QPushButton)
        assert len(buttons) == count, f"Expected {count} buttons, got {len(buttons)}"

        # Checks if the default display is correct
        assert area.stackedLayout.currentIndex() == 0, \
            f"Expected index 0, got {area.stackedLayout.currentIndex()}"

        assert isinstance(area.stackedLayout.currentWidget(), DefaultDisplay), \
            f"Expected a DefaultDisplay instance, got {type(area.stackedLayout.currentWidget()).__name__}"


    def test_buttons_functionality(self,
                                  app: QApplication,
                                  qtbot: QtBot,
                                  dummy_graphs: Callable[[int], list[DummyGraph]],
                                  count: int):
        """
        Tests if all buttons in `GraphDisplayLayout` function properly.

        Specifically tests:
        - If each `QPushButton`'s label matched the title of the graph its linked to.
        - If clicking each button switches the display to the correct graph.

        :param app: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        :param dummy_graphs: Factory which returns `count` `DummyGraph` instances.
        :param count: No. of graphs to test with.
        """

        graphs = dummy_graphs(count)
        widget = GraphDisplayLayout(graphs)
        qtbot.addWidget(widget)

        area = widget.graphs_display    # GraphDisplayArea widget
        buttons = widget.findChildren(QPushButton)
        
        # Clicks each button using qtbot to test functionality
        for index, button in enumerate(buttons, start=1):
            # Checks if button text matches graph title
            expected_text = graphs[index-1].get_title()
            assert button.text().replace("\n", " ") == expected_text, \
                f"Button {index}: Expected \"{expected_text}\", got \"{button.text().replace("\n", " ")}\""

            # Checks if pressing button displays correct graph
            qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
            assert area.stackedLayout.currentIndex() == index, \
                f"Button {index}: Expected graph {index}, got graph {area.stackedLayout.currentIndex()}"
    

    def test_stop_threads_shuts_down_and_replaces_executor(self,
                                                           app: QApplication,
                                                           widget: GraphDisplayLayout,
                                                           monkeypatch: pytest.MonkeyPatch):
        """
        Tests if `stop_threads()` properly shuts down and replaces the `ThreadPoolExecutor`.

        Specifically testing:
        - If `shutdown()` is called on existing `ThreadPoolExecutor`.
        - If `background_threads` is replaced with a new `ThreadPoolExecutor` instance after `shutdown()`.

        :param app: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `GraphDisplayLayout`.
        :param monkeypatch: Fixture used to patch `executor.shutdown()`.
        """

        old_exec = widget.graphs_display.background_threads # ThreadPoolExecutor
        shutdown_called = False

        # Mock version of shutdown()
        def fake_shutdown(wait: bool):
            nonlocal shutdown_called
            shutdown_called = True

        # Monkey-patch the existing executor’s shutdown() method with fake_shutdown() to verify if 
        # shutdown() was invoked, without actually shutting down threads.
        monkeypatch.setattr(old_exec, "shutdown", fake_shutdown)

        # Checks if shutdown() was called
        widget.graphs_display.stop_threads()
        assert shutdown_called, "Expected shutdown() to be called on the old ThreadPoolExecutor"

        # Checks if background_threads has been set to a new ThreadPoolExecutor
        new_exec = widget.graphs_display.background_threads # ThreadPoolExecutor
        assert isinstance(new_exec, ThreadPoolExecutor), \
            f"Expected a ThreadPoolExecutor instance, got {type(new_exec).__name__}"
        assert new_exec is not old_exec, "Expected new ThreadPoolExecutor instance"
    

    def test_stop_threads_exception_handling(self,
                                             app: QApplication,
                                             widget: GraphDisplayLayout,
                                             monkeypatch: pytest.MonkeyPatch,
                                             capsys: CaptureFixture[str]):
        """
        Tests if forcing `shutdown()` to raise exception prints the exception message.

        :param app: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `GraphDisplayLayout`.
        :param monkeypatch: Fixture used to patch `executor.shutdown()`.
        :param capsys: Fixture for capturing `stdout`/`stderr` output.
        """

        # Mock version of shut-down which always raises an error
        def raise_err(wait: bool):
            raise Exception("shutdown error")

        # Monkey-patch the executor’s shutdown() method with raise_error() to forcing stop_threads() to 
        # hit its exception handler
        monkeypatch.setattr(
            widget.graphs_display.background_threads,
            "shutdown",
            raise_err
        )

        # Checks if except block was reached
        widget.graphs_display.stop_threads()
        captured = capsys.readouterr()
        assert "shutdown error" in captured.out, "Expected exception message to be printed"


    def test_close_event_calls_stop_threads(self,
                                            app: QApplication,
                                            widget: GraphDisplayLayout,
                                            monkeypatch: pytest.MonkeyPatch):
        """
        Tests if `closeEvent()` calls `stop_threads()` and accepts the event.

        :param app: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `GraphDisplayLayout` for testing.
        :param monkeypatch: Fixture used to patch `stop_threads()`.
        """

        stop_called = False

        # Mock version of stop_threads()
        def fake_stop_threads():
            nonlocal stop_called
            stop_called = True

        # Monkey-patch stop_threads() method with fake_stop_threads() to verify if stop_threads() 
        # was invoked by closeEvent(), without actually shutting down threads.
        monkeypatch.setattr(widget.graphs_display, "stop_threads", fake_stop_threads)

        evt = QCloseEvent()

        # Checks if stop_threads() was invoked and if closeEvent() was accepted
        widget.closeEvent(evt)
        assert evt.isAccepted(), "Expected the close event to be accepted"
        assert stop_called, "Expected stop_threads() to be called by closeEvent()"