import os
import json
import pandas as pd

# Append new data to JSON file
def append_to_json_file(new_data, json_path='data.json'):
    # Load existing data if the file exists, otherwise create an empty list
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Append the new data
    data.append(new_data)

    # Save the updated data back to the JSON file
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)

# Convert JSON file to CSV
def json_to_csv(json_path='data.json', csv_path='data.csv'):
    # Load the JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Convert the JSON data to a pandas DataFrame
    df = pd.DataFrame(data)

    # Save the DataFrame to a CSV file
    df.to_csv(csv_path, index=False)

    return csv_path