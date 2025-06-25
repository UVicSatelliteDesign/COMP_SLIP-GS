import sys
import pytest
import string
import random
from PyQt6.QtCore import Qt

# For type hints
from pytestqt.qtbot import QtBot

# To match type of components
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QComboBox

# Widgets, functions and variables to test
from ground_station.frontend.command_prompt import CommandPrompt
from ground_station.frontend.utils import add_to_queue, get_from_queue, valid_commands, queue, \
    transfer_acknowledgment

DEFAULT_MAX_NO_OF_COMMANDS = 7 # Default upper-limit for no. of commands used in testing

# Hook for optional user input of custom upper-limit for the no. of commands to test with
def pytest_addoption(parser: pytest.Parser):
    """
    `pytest` hook to customize the upper-limit of no. of commands to be used in testing.
    Default upper limit is stored in `DEFAULT_MAX_NO_OF_COMMANDS`.

    :param parser: `pytest` command line parser object.
    """

    parser.addoption(
        "--max-commands",
        action = "store",
        default = DEFAULT_MAX_NO_OF_COMMANDS,
        type = int,
        help = "Max no. of commands to be used for testing",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc):
    """
    `pytest` hook for dynamic parametrization of test functions.

    If a function uses a `count` fixture, this hook parametrizes it with a range from 1 to the value
    obtained from `--max-commands` on the command line.

    :param metafunc: `Metafunc` object for the test function.
    """

    if "count" in metafunc.fixturenames:
        max_commands = metafunc.config.getoption("max-commands")

        # Error handling of user-input
        if max_commands <= 0 or not isinstance(max_commands, int):
            print(f"Invalid input for --max-commands. Using default value of {DEFAULT_MAX_NO_OF_COMMANDS}")
            max_commands = DEFAULT_MAX_NO_OF_COMMANDS
        
        metafunc.parametrize("count", range(1, max_commands+1))


# Fixtures
@pytest.fixture(scope="session")
def app() -> QApplication:
    """
    Provides a single `QApplication` instance for all tests.
    """

    return QApplication(sys.argv)


@pytest.fixture
def widget(app: QApplication,
           qtbot: QtBot) -> CommandPrompt:
    """
    Provides a `CommandPrompt` instance and registers it with `qtbot` for proper event-loop
    handling and cleanup.
    """

    w = CommandPrompt()

    qtbot.addWidget(w)

    return w

@pytest.fixture
def reset_queue():
    """
    Removes all command codes from `queue` in `utils.py`.
    """
    
    while not queue.empty():
            queue.get()

@pytest.fixture
def reset_transfer_acknowledgement():
    """
    Resets `transfer_acknowledgment` to `False`.
    """

    transfer_acknowledgment = False


@pytest.fixture
def generate_invalid_commands(n: int) -> list[str]:
    """
    Generates `n` invalid commands containing letters, numbers, special characters and escape sequences.

    :param n: No. of invalid commands to generate.
    """

    gibberish_pool = (string.ascii_letters, string.digits, string.punctuation, "\n\t\r\\\"\'\b\f")

    return ["".join(random.choices(gibberish_pool, k=random.randint(5,15))) for _ in range(n)]


# Tests for CommandPrompt in command_prompt.py
class TestCommandPrompt:
    def test_layout_initialization(self,
                                   app: QApplication,
                                   qtbot: QtBot):
        """
        Tests if the GUI of `CommandPrompt` initializes correctly.

        Specifically tests:
        - If all components of the widget are of the proper type.
        - The no. of commands in the drop-down are same as the no. of valid commands.
        - The commands in the drop-down are identical to the valid commands.

        :param app: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        """
        
        widget = CommandPrompt()
        qtbot.addWidget(widget)

        # Checks if all components have been correctly created
        assert isinstance(widget.command_dropdown, QComboBox), \
            f"Expected QComboBox instance, got {type(widget.command_dropdown).__name__}"
        assert isinstance(widget.submit_button, QPushButton), \
            f"Expected QPushButton instance, got {type(widget.submit_button).__name__}"
        assert isinstance(widget.label, QLabel), \
            f"Expected QLabel instance, got {type(widget.label).__name__}"

        # Checks if the no. of commands in drop-down is same as the no. of valid commands
        assert widget.command_dropdown.count() == len(valid_commands), \
            f"Expected {widget.command_dropdown.count()} commands, got {len(valid_commands)}"

        # Checks if drop-down only has valid commands
        dropdown_items = [widget.command_dropdown.itemText(i) \
                          for i in range(widget.command_dropdown.count())]
        
        for command in dropdown_items:
            assert command in valid_commands.keys(), f"Invalid command \"{command}\" given as option"


    def test_drop_down_and_submit_button_functionality(self,
                                                       app: QApplication,
                                                       qtbot: QtBot,
                                                       reset_queue,
                                                       reset_transfer_acknowledgement):
        """
        Tests if all commands in the drop-down menu are processed correctly.

        :param app: Fixture providing `Qt` application context.
        :param qtbot: Fixture for widget interaction.
        :param reset_queue: Fixture to reset `queue` in `utils.py` after testing.
        :param reset_transfer_acknowledgement: Fixture to reset `transfer_acknowledgement` in `utils.py` 
        after testing.
        """
        
        widget = CommandPrompt()
        qtbot.addWidget(widget)

        dropdown = widget.command_dropdown
        commands_submitted = []

        # Selecting each command and submitting it
        for i in range(dropdown.count()):
            dropdown.setCurrentIndex(i)

            # Checks if correct command was selected
            assert dropdown.currentIndex() == i and dropdown.currentText() == dropdown.itemText(i), \
                f"Expected \"{dropdown.itemText(i)}\", got \"{dropdown.currentText()}\""
            
            commands_submitted.append(dropdown.itemText(i).strip())

            # Checks if transfer is acknowledged before submission
            assert transfer_acknowledgment == False, \
                "Transfer to queue should not have been acknowledged yet"

            qtbot.mouseClick(widget.submit_button, Qt.MouseButton.LeftButton)
            
            # Checks if submit was acknowledged
            assert transfer_acknowledgment == True, "Transfer to queue should have been acknowledged"
        
        # Checks if all the commands were added to queue
        assert queue.qsize() == dropdown.count(), \
            f"Expected {queue.qsize()} commands, got {dropdown.count()}"
        
        # Checks if all commands were enqueued in the correct order
        for command in commands_submitted:
            dequeued_command_code = queue.get()

            assert dequeued_command_code == valid_commands[command], \
                f"Expected {dequeued_command_code}, got {valid_commands[command]}"


    def test_process_command_invalid_command_handling(self,
                                                      app: QApplication,
                                                      widget: CommandPrompt,
                                                      monkeypatch: pytest.MonkeyPatch,
                                                      generate_invalid_commands: list[str],
                                                      reset_queue,
                                                      reset_transfer_acknowledgement,
                                                      count: int):
        """
        Tests if `process_command()` processes invalid commands correctly.

        :param app: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `CommandPrompt`.
        :param monkeypatch: Fixture to patch `currentText()` of `widget.command_dropdown`.
        :param reset_queue: Fixture to reset `queue` in `utils.py` after testing.
        :param reset_transfer_acknowledgement: Fixture to reset `transfer_acknowledgement` in `utils.py` 
        after testing.
        :param count: No. of invalid commands to test with.
        """
        
        sample_invalid_commands = generate_invalid_commands(count)
        dummy_command = ""

        # Mock version of currentText() method of QComboBox
        def fake_current_text():
            nonlocal dummy_command
            return dummy_command
        
        # Monkey-patch currentText() method of command_dropdown with fake_current_text() to have 
        # control over commands selected
        monkeypatch.setattr(widget.command_dropdown, "currentText", fake_current_text)

        # Checks if process_command() uploads invalid commands to queue
        for command in sample_invalid_commands:
            dummy_command = command

            if dummy_command not in valid_commands:
                widget.process_command()

                assert queue.empty(), "Command should not have been uploaded to queue"
                assert transfer_acknowledgment == False, "Transfer should not have been acknowledged"
                assert widget.result_label == "Invalid command.", \
                    f"Expected \"Invalid command.\" got \"{widget.result_label}\""
            else:
                continue
    

    def test_process_command_mixed_input_handling(self,
                                                  app: QApplication,
                                                  widget: CommandPrompt,
                                                  monkeypatch: pytest.MonkeyPatch,
                                                  generate_invalid_commands: list[str],
                                                  reset_queue,
                                                  reset_transfer_acknowledgement,
                                                  count: int):
        """
        Tests if `process_command()` processes a mix of valid and invalid commands correctly.

        :param app: Fixture providing `Qt` application context.
        :param widget: Fixture providing an instance of `CommandPrompt`.
        :param monkeypatch: Fixture to patch `currentText()` of `widget.command_dropdown`.
        :param reset_queue: Fixture to reset `queue` in `utils.py` after testing.
        :param reset_transfer_acknowledgement: Fixture to reset `transfer_acknowledgement` in `utils.py` 
        after testing.
        :param count: No. of commands to test with.
        """
        
        # Generating random selection of valid and invalid commands and creating shuffled list of those
        # commands
        sample_invalid_commands = generate_invalid_commands(count//2)
        sample_valid_commands = [random.choice(list(valid_commands.keys())) for _ in range(count//2)]
        sample_commands: list[str] = sample_valid_commands + sample_invalid_commands
        random.shuffle(sample_commands)

        dummy_command = ""

        # Mock version of currentText() method of QComboBox
        def fake_current_text():
            nonlocal dummy_command
            return dummy_command
        
        # Monkey-patch currentText() method of command_dropdown with fake_current_text() to have 
        # control over commands selected
        monkeypatch.setattr(widget.command_dropdown, "currentText", fake_current_text)

        # Submits all commands in sample_commands
        expected_commands_codes_queue = []

        for command in sample_commands:
            dummy_command = command
            widget.process_command()

            if command in valid_commands:
                # Appends command code of command to expected queue
                expected_commands_codes_queue.append(valid_commands[command.strip()])
            else:
                continue
        
        # Checks if ONLY all the valid commands were inserted into queue
        assert queue.qsize() == len(expected_commands_codes_queue), \
            f"Expected {len(expected_commands_codes_queue)} commands, got {queue.qsize()}"
        
        # Checks if all the valid commands were inserted in the correct order
        for command in expected_commands_codes_queue:
            assert not queue.empty(), "Queue empty. It should have more commands"

            command_extracted = queue.get()

            assert command == command_extracted, f"Expected {command}, got {command_extracted}"


# Tests for functions in utils.py
class TestUtils:
    def test_enqueue_dequeue(self,
                             reset_queue,
                             reset_transfer_acknowledgement,
                             count: int):
        """
        Tests if `add_to_queue()` enqueues and `get_from_queue()` dequeues properly.

        :param reset_queue: Fixture to reset `queue` in `utils.py` after test.
        :param reset_transfer_acknowledgement: Fixture to reset `transfer_acknowledgement` in `utils.py` 
        after test.
        :param count: No. of commands to test with.
        """
        
        sample_commands_codes = [random.choice(list(valid_commands.values())) for _ in range(count)]

        # Enqueueing commands
        for command in sample_commands_codes:
            add_to_queue(command)

        # Checking if commands are dequeued in correct order
        for command in sample_commands_codes:
            dequeued_command = get_from_queue()

            assert dequeued_command == command, f"Expected {command}, got {dequeued_command}"