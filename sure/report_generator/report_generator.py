import subprocess
import pkg_resources

import json
import os
import pandas as pd
import polars as pl
import numpy as np

# Function to run the streamlit app
def report_generator():
    report_path = pkg_resources.resource_filename('SURE.sure.report_generator', 'report.py')
    process = subprocess.run(['streamlit', 'run', report_path])
    print("Streamlit app is running...")
    return process

# def stop_report(process):
#     process.terminate()
#     process.wait()
#     print("Streamlit app has been stopped.")

def _convert_to_serializable(obj):
    """Recursively convert DataFrames and other non-serializable objects in a nested dictionary to serializable formats."""
    if isinstance(obj, (pd.DataFrame, pl.DataFrame, pl.LazyFrame)):
        if isinstance(obj, pl.DataFrame):
            obj = obj.to_pandas()
        if isinstance(obj, pl.LazyFrame):
            obj = obj.collect().to_pandas()
        
        # Convert index to column only if index is non-numerical
        if obj.index.dtype == 'object' or pd.api.types.is_string_dtype(obj.index):
            obj = obj.reset_index()
        
        # Convert datetime columns to string
        for col in obj.columns:
            if pd.api.types.is_datetime64_any_dtype(obj[col]):
                obj[col] = obj[col].astype(str)
        
        return obj.to_dict(orient='records')
    elif isinstance(obj, dict):
        return {k: _convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_to_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def _save_to_json(data_name, new_data):
    """This function saves data into a JSON file in the folder where the user is working."""
    # Check if the file exists
    if os.path.exists("data.json"):
        # Read the existing data from the file
        with open("data.json", 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}  # Initialize to an empty dictionary if the file is empty or invalid
    else:
        data = {}

    # Convert new_data to a serializable format if it is a DataFrame or contains DataFrames
    serializable_data = _convert_to_serializable(new_data)

    # Update the data dictionary with the new_data
    data[data_name] = serializable_data

    # Write the updated data back to the file
    with open("data.json", 'w') as file:
        json.dump(data, file, indent=4)

def _load_from_json(data_name):
    ''' This function loads data from a JSON file in the folder where the user is working
    '''
    # Check if the file exists
    if not os.path.exists("data.json"):
        raise FileNotFoundError("The data.json file does not exist.")
    
    # Read the data from the file
    with open("data.json", 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            raise ValueError("The data.json file is empty or invalid.")

    # Extract the relevant data
    new_data = data.get(data_name, None)
    if new_data is None:
        raise ValueError(f"No data found for the key: {data_name}")
    
    # Convert nested dictionaries back to DataFrames
    def _convert_to_dataframe(obj):
        if isinstance(obj, list) and all(isinstance(item, dict) for item in obj):
            return pd.DataFrame(obj)
        elif isinstance(obj, dict):
            return {k: _convert_to_dataframe(v) for k, v in obj.items()}
        else:
            return obj

    return _convert_to_dataframe(new_data)