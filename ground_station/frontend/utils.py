# Valid Commands Dictionary
# Keys - Commands : Values - Binary

from queue import Queue

valid_commands = {
    "ping": "0000",
    "nominal": "0001",
    "low power": "0010",
    "telemetry": "0011",
    "Camera-1-End": "0100",
    "Camera-2-End": "0110",
    "Req Retransmission": "1000"
}

# Function to check if the command is valid
def is_valid_command(command: str) -> bool:
    return command in valid_commands

# Function to get the binary from the dictionary
def get_binary_from_dict(command: str) -> str:
    return valid_commands.get(command, "")

# Queue to hold the converted data
# queue = [] , not using this anymore.
queue = Queue()

# Transfer acknowledgment variable
transfer_acknowledgment = False

# Function to add the converted bits to the Queue
def add_to_queue(bits: str) -> None:
    global transfer_acknowledgment
    queue.put(bits)
    transfer_acknowledgment = True  # Set transfer acknowledgment to True
    print("Acknowledgment: Data moved to queue.")

# Function to retrieve the next item from the queue
def get_from_queue() -> str | None:
    if not queue.empty():
        return queue.get()
    return None

# Function to show acknowledgment message
def show_acknowledgment() -> None:
    print("Conversion complete. Data added to queue.")

# Example payload types 
payload_type_1 = "nominal"
payload_type_2 = "low power"
payload_type_3 = "ping"

# Merge the payloads for transfer (binary concatenation)
def merge_payloads() -> str:
    return ''.join(
        get_binary_from_dict(p) for p in (payload_type_1, payload_type_2, payload_type_3)
        if is_valid_command(p)
    )
