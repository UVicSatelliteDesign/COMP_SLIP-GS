from queue import Queue

# Global shared command queue
command_queue: Queue[str] = Queue()

# Transfer acknowledgment variable
# NOTE: only used in tests, set to True when an entry is added to the command_queue.
transfer_acknowledgment = False


# Function to add the converted bits to the Queue
def add_to_queue(bits: str) -> None:
    global transfer_acknowledgment
    command_queue.put(bits)
    transfer_acknowledgment = True  # Set transfer acknowledgment to True
    print("Acknowledgment: Data moved to queue.")


# Function to retrieve the next item from the queue
def get_from_queue() -> str | None:
    if not command_queue.empty():
        return command_queue.get()
    return None


# Function to show acknowledgment message
def show_acknowledgment() -> None:
    print("Conversion complete. Data added to queue.")
