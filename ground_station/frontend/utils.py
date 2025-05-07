# utils.py
# Dictionary where keys are commands and values are their binary translations
valid_commands = {
    "ping": "0000",
    "nominal": "0001",
    "low power": "0010",
    "telemetry": "0011",
}

# Function to check if the command is valid
def is_valid_command(command):
    return command in valid_commands

# Function to get the binary from the dictionary
def get_binary_from_dict(command):
    return valid_commands.get(command, "")

# Buffer to hold the converted data
buffer = []

# Transfer acknowledgment variable
transfer_acknowledgment = False

# Function to add the converted bits to the buffer
def add_to_buffer(bits):
    buffer.append(bits)
    print("Acknowledgment: Data moved to buffer.")
    global transfer_acknowledgment
    transfer_acknowledgment = True  # Set transfer acknowledgment to True

# Function to show acknowledgment message
def show_acknowledgment():
    print("Conversion complete. Data added to buffer.")


# Example payload types
payload_type_1 = "nominal"
payload_type_2 = "low power"
payload_type_3 = "ping"

# Merge the payloads for transfer
def merge_payloads():
    return payload_type_1 + payload_type_2 + payload_type_3

