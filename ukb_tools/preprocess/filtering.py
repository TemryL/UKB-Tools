# Feel free to add any useful filtering functions here.
# Please make sure that each function don't modidy the original argument and:
#       - takes a DataFrame containing UKB data as the first argument
#       - returns the list of filtered eids

import pandas as pd
from functools import reduce
from ..tools import filter_cols

def filter_fully_populated_rows(ukb_data: pd.DataFrame, field_ids: list[str]) -> list[int]:
    """
    Filters and returns rows from a DataFrame that are fully populated (no NaN values)
    across specified columns.

    Parameters:
    data (pd.DataFrame): The DataFrame containing UK Biobank data.
    field_ids (list[str]): A list of field IDs used to identify the columns to check
                           for NaN values.

    Returns:
    pd.DataFrame: A DataFrame containing only rows where all specified fields are 
                  non-missing.
    """
    # Subset data for columns matching the specified field_ids
    cols = filter_cols(ukb_data.columns, field_ids)
    df = ukb_data[cols]
    # Remove row that contains NaN value and return valid eids
    eids = df.dropna().index
    return list(eids)

def filter_partially_populated_rows(ukb_data: pd.DataFrame, field_ids: list[str]) -> list[int]:
    """
    Filters and returns rows from a DataFrame that are partially populated, meaning
    at least one specified field is non-missing.

    Parameters:
    data (pd.DataFrame): The DataFrame containing UK Biobank data.
    field_ids (list[str]): A list of field IDs used to identify the columns to check
                           for non-NaN values.

    Returns:
    pd.DataFrame: A DataFrame containing rows where at least one of the specified fields
                  is non-missing.
    """
    # Initialize a list to store boolean Series for each field ID indicating non-NaN rows
    valid_data_flags = []

    for field_id in field_ids:
        # Filter columns for the current set of field IDs
        cols = filter_cols(ukb_data.columns, field_ids)
        df = ukb_data[cols]
        # Identify rows where at least one value in the column set is not NaN
        non_nan_rows = df.notna().any(axis=1)
        valid_data_flags.append(non_nan_rows)

    # Combine boolean Series with OR to flag rows valid in any field_id
    valid_rows = reduce(lambda x, y: x | y, valid_data_flags)
    
    # Return eids of valid rows
    return list(ukb_data[valid_rows].index)