# Predefined tuple
valid_commands = ("nominal", "low power", "image", "ping")

# Function to check if the command is valid
def is_valid_command(command):
    return command in valid_commands

# Function to convert the string to its binary representation
def string_to_bits(input_string):
    return ' '.join(format(ord(c), '08b') for c in input_string)

# Buffer to hold the converted data
buffer = []

# Function to add the converted bits to the buffer
def add_to_buffer(bits):
    buffer.append(bits)
    print("Acknowledgment: Data moved to buffer.")

# Function to show acknowledgment message
def show_acknowledgment():
    print("Conversion complete. Data added to buffer.")
