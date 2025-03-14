"""
This script demonstrates reading a CSV file, verifying required columns,
and displaying the most recent entry based on a timestamp.
"""

import csv
from datetime import datetime

def read_csv_data(file_path, expected_columns):
    """
    Reads the CSV file and returns a list of rows as dictionaries.

    Parameters:
        file_path (str): The path to the CSV file.
        expected_columns (list): A list of expected column names in the CSV file.

    Returns:
        list: A list of dictionaries representing each row in the CSV file.
    """
    data = []
    try:
        # Open the CSV file in read mode with UTF-8 encoding
        with open(file_path, 'r', newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            
            # Check if the CSV contains all expected columns
            if not all(col in reader.fieldnames for col in expected_columns):
                raise ValueError("CSV file does not contain all expected columns.")
            
            # Read and store each row from the CSV
            for row in reader:
                data.append(row)

    except FileNotFoundError as fnf_error:
        # Handles the case where the CSV file is not found
        print(f"File not found: {fnf_error}")
    except ValueError as val_error:
        # Handles missing columns or other value-related errors
        print(f"Value error: {val_error}")
    except Exception as e:
        # Catches any other unexpected errors
        print(f"An unexpected error occurred while reading the CSV file: {e}")
    
    return data

def display_latest_value(data, timestamp_column, value_column):
    """
    Sorts the CSV data based on the timestamp column and displays the most recent value.

    Parameters:
        data (list): The list of CSV data rows (each as a dictionary).
        timestamp_column (str): The column name that contains the timestamp.
        value_column (str): The column name for the value to be displayed.

    Returns:
        None
    """
    try:
        # Sort the data by converting timestamp strings to datetime objects in descending order
        data_sorted = sorted(
            data,
            key=lambda row: datetime.strptime(row[timestamp_column], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )
        
        # If no data is available, inform the user and exit the function
        if not data_sorted:
            print("No data available to display.")
            return
        
        # The first element in the sorted list is the most recent entry
        most_recent = data_sorted[0]
        print("Most Recent Data:")
        print(f"{timestamp_column}: {most_recent[timestamp_column]}")
        print(f"{value_column}: {most_recent[value_column]}")
    
    except KeyError as ke:
        # Handles the case where expected columns are missing in the data
        print(f"Missing expected column in data: {ke}")
    except ValueError as ve:
        # Handles errors in converting timestamp strings to datetime objects
        print(f"Error processing date format: {ve}")
    except Exception as e:
        # Catches any other unexpected errors
        print(f"An unexpected error occurred while processing the data: {e}")

# ----- Configuration and Execution -----

# Define the expected structure of the CSV file.
expected_columns = ["timestamp", "value"]

# Define the path to the CSV file.
csv_file_path = "/Users/dilrajsingh/Desktop/uvsd.csv"

# Read data from the CSV file.
csv_data = read_csv_data(csv_file_path, expected_columns)

# Display the most recent values from the CSV data.
display_latest_value(csv_data, "timestamp", "value")
