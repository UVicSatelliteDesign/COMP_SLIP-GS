import sys
import pytest

# For type hints
from _pytest.capture import CaptureFixture
from pytestqt.qtbot import QtBot
from typing import Callable

# To match class of components
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton
from PyQt6.QtCore import Qt

# Widgets to test
from ground_station.frontend.graphs_display.graph_display_layout import GraphDisplayLayout
from ground_station.frontend.graphs_display.graph_display_area import GraphDisplayArea
from ground_station.frontend.graphs_display.graph_wrapper_class import GraphWrapperClass

DEFAULT_MAX_GRAPHS = 7 # Upper-limit for no. of graphs used in testing

# Hook for optional user input of custom upper-limit for the no. of graphs to test with
def pytest_addoption(parser: pytest.Parser) -> None:
    """
    `pytest` hook to customize upper-limit of no. of graphs to be used in testing.
    Default upper limit is stored in `DEFAULT_MAX_GRAPHS`.

    :param parser: `pytest` command line parser object.
    """

    parser.addoption(
        "--max-graphs",
        action = "store",
        default = DEFAULT_MAX_GRAPHS,
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

        if metafunc.function.__name__ == "test_layout_initialization":
            metafunc.parametrize("count", range(0, max_graphs))
        elif metafunc.function.__name__ == "test_buttons_functionality":
            metafunc.parametrize("count", range(1, max_graphs))


# Mock ExpandingGraph class
class DummyGraph:
    def __init__(self, title: str = "Dummy"):
        import matplotlib.pyplot as plt

        self.fig = plt.figure()
        self._title = title
    

    def get_title(self):
        return self._title
    

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
def disable_background_threads(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Prevents `ThreadPoolExecutor` from spawning real threads
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


# Tests
class TestGraphDisplayLayout:
    def test_layout_initialization(self,
                                   app: QApplication,
                                   qtbot: QtBot,
                                   dummy_graphs: Callable[[int], list[DummyGraph]],
                                   count: int):
        """
        Verifies if `GraphDisplayLayout` initializes correctly for a varying number of graphs.

        Specifically testing if:
        - Each `DummyGraph` object is properly wrapped in a `GraphWrapperClass` object.
        - Exactly 1 `QPushButton` is created per graph.
        - The `QStackedLayout` has the correct number of graphs.
        - The default display displays the text "NO GRAPH SELECTED"

        :param app: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        :param dummy_graphs: Factory which returns `count` `DummyGraph` instances.
        :param count: No. of graphs to test initialization with.
        """

        graphs = dummy_graphs(count)
        widget = GraphDisplayLayout(graphs)
        qtbot.addWidget(widget)

        area = widget.graphs_display

        # Checking if correct no. of graphs have been created
        assert len(widget.graphs) == count, f"Expected {count} graphs, got {len(widget.graphs)}"

        # Checking if wrapper classes have been created correctly
        for index, wrapper in enumerate(widget.graphs, start=1):
            # Checking if wrapper class has sequential ID and if title of graph has been preserved.
            assert isinstance(wrapper, GraphWrapperClass), "Expected a GraphWrapperClass instance"
            assert wrapper.get_id() == index, f"Wrapper ID should be {index}"
            assert wrapper.get_title() == graphs[index-1].get_title(), "Title mismatch"

            # Checking if the wrapper class contains a FigureCanvasQTAgg to display the graph
            current_widget = area.stackedLayout.widget(index)
            canvas = current_widget.findChild(FigureCanvas)
            assert canvas is not None, "Expected a FigureCanvasQTAgg inside the wrapper"

        # Checking if only 1 button has been created per graph
        buttons = widget.findChildren(QPushButton)
        assert len(buttons) == count, "Button count does not match graph count"

        # Checking if the default display is correct
        assert area.stackedLayout.currentIndex() == 0, "Default page index should be 0"

        default_widget = area.stackedLayout.widget(0)
        label = default_widget.findChild(QLabel)
        assert label is not None, "Default widget must contain a QLabel"
        assert label.text() == "NO GRAPH SELECTED", "Default label text mismatch"


    def test_buttons_functionality(self,
                                  app: QApplication,
                                  qtbot: QtBot,
                                  dummy_graphs: Callable[[int], list[DummyGraph]],
                                  count: int):
        """
        Verifies if all buttons in `GraphDisplayLayout` function properly.

        Specifically testing if:
        - Each `QPushButton`'s label matched the title of the graph its linked to.
        - Clicking each button switches the display to the correct graph.

        :param app: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        :param dummy_graphs: Factory which returns `count` `DummyGraph` instances.
        :param count: No. of graphs to test button functionality with.
        """

        graphs = dummy_graphs(count)
        widget = GraphDisplayLayout(graphs)
        qtbot.addWidget(widget)

        area = widget.graphs_display
        buttons = widget.findChildren(QPushButton)
        
        for expected_index, button in enumerate(buttons, start=1):
            # Checking if button text matches graph title
            expected_text = graphs[expected_index-1].get_title().replace(" ", "\n")
            assert button.text() == expected_text, f"Button text mismatch at index {expected_index}"

            # Checking if pressing button displays correct graph
            qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
            assert area.stackedLayout.currentIndex() == expected_index, f"After click, expected graph with index {expected_index}"
    

    def test_stop_threads_shuts_down_and_replaces_executor(self,
                                                           app: QApplication,
                                                           widget: GraphDisplayLayout,
                                                           monkeypatch: pytest.MonkeyPatch):
        """
        Verifies that `stop_threads()` properly shuts down and replaces the `ThreadPoolExecutor`.

        Specifically testing if:
        - `shutdown()` is called on existing `ThreadPoolExecutor`.
        - `background_threads` is replace with a new `ThreadPoolExecutor` instance.

        :param app: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `GraphDisplayLayout` for testing.
        :param monkeypatch: Fixture used to patch `executor.shutdown()`.
        """

        from concurrent.futures import ThreadPoolExecutor

        old_exec = widget.graphs_display.background_threads
        shutdown_called = False

        # Mock version of shutdown()
        def fake_shutdown(wait: bool):
            nonlocal shutdown_called
            shutdown_called = True

        # Monkey-patch the existing executor’s shutdown() method so that when stop_threads() calls it,
        # our fake_shutdown() runs instead—letting us verify shutdown() was invoked without actually
        # shutting down threads.
        monkeypatch.setattr(old_exec, "shutdown", fake_shutdown)

        # Checking if shutdown() was called
        widget.graphs_display.stop_threads()
        assert shutdown_called, "Expected shutdown() to be called on the old executor"

        # Checking if background_threads has been set to a new ThreadPoolExecutor
        new_exec = widget.graphs_display.background_threads
        assert isinstance(new_exec, ThreadPoolExecutor), \
            f"Expected background_threads to be ThreadPoolExecutor, got {type(new_exec).__name__}"
        assert new_exec is not old_exec, "background_threads should be replaced"


    def test_stop_threads_does_not_print_error(self,
                                               app: QApplication,
                                               widget: GraphDisplayLayout,
                                               capsys: CaptureFixture[str]):
        """
        Verifies that `stop_threads()` does not trigger its `except` block (no stdout).

        Specifically testing if `stop_threads()` reached its `except` block.

        :param app: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `GraphDisplayLayout` for testing.
        :param capsys: Fixture for capturing `stdout`/`stderr` output.
        """

        # Checking if error message was printed
        widget.graphs_display.stop_threads()
        captured = capsys.readouterr()
        assert captured.out == "", f"Unexpected output: {captured.out!r}"


    def test_stop_threads_prints_on_shutdown_exception(self,
                                                       app: QApplication,
                                                       widget: GraphDisplayLayout,
                                                       monkeypatch: pytest.MonkeyPatch,
                                                       capsys: CaptureFixture[str]):
        """
        Forces `shutdown()` to raise exception to verify that `stop_threads()` prints the exception
        message.

        :param app: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `GraphDisplayLayout` for testing.
        :param monkeypatch: Fixture used to patch `executor.shutdown()`.
        :param capsys: Fixture for capturing `stdout`/`stderr` output.
        """

        # Mock version of shut-down which always raises an error
        def raise_err(wait: bool):
            raise Exception("shutdown error")

        # Monkey-patch the executor’s shutdown() method on background_threads to our raise_error() 
        # function, forcing stop_threads() to hit its exception handler
        monkeypatch.setattr(
            widget.graphs_display.background_threads,
            "shutdown",
            raise_err
        )

        # Checking if except block was reached
        widget.graphs_display.stop_threads()
        captured = capsys.readouterr()
        assert "shutdown error" in captured.out, "Expected exception message to be printed"


    def test_close_event_calls_stop_threads(self,
                                            app: QApplication,
                                            widget: GraphDisplayLayout,
                                            monkeypatch: pytest.MonkeyPatch):
        """
        Verifies that `closeEvent()` calls `stop_threads()` and accepts the event.

        :param app: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `GraphDisplayLayout` for testing.
        :param monkeypatch: Fixture used to patch `stop_threads()`.
        """

        stop_called = False

        # Mock version of stop_threads()
        def fake_stop_threads():
            nonlocal stop_called
            stop_called = True

        # Monkey-patch stop_threads() method so that when closeEvent() calls it,
        # our fake_stop_threads() runs instead, letting us verify that stop_threads() 
        # was invoked without actually shutting down threads.
        monkeypatch.setattr(widget.graphs_display, "stop_threads", fake_stop_threads)

        from PyQt6.QtGui import QCloseEvent
        evt = QCloseEvent()

        # Checking if stop_threads() was invoked and if closeEvent() was accepted
        widget.closeEvent(evt)
        assert evt.isAccepted(), "Expected the close event to be accepted"
        assert stop_called, "Expected stop_threads() to be called on closeEvent"