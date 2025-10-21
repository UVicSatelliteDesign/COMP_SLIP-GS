# Valid Commands Dictionary
# Keys - Commands : Values - Binary

valid_commands = {
    "ping": "0000",
    "nominal": "0001",
    "low power": "0010",
    "telemetry": "0011",
    "Camera-1-End": "0100",
    "Camera-2-End": "0110",
    "Req Retransmission": "1000",
}


# Function to check if the command is valid
def is_valid_command(command: str) -> bool:
    return command in valid_commands


# Function to get the binary from the dictionary
def get_binary_from_dict(command: str) -> str:
    return valid_commands.get(command, "")


# Example payload types
payload_type_1 = "nominal"
payload_type_2 = "low power"
payload_type_3 = "ping"


# Merge the payloads for transfer (binary concatenation)
def merge_payloads() -> str:
    return "".join(
        get_binary_from_dict(p)
        for p in (payload_type_1, payload_type_2, payload_type_3)
        if is_valid_command(p)
    )
