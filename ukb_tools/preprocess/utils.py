import pandas as pd
from ..tools import filter_cols

def rename_features(ukb_data: pd.DataFrame, features: dict) -> (pd.DataFrame, list):
    """
    Renames columns in a DataFrame based on a mapping from new feature names to field IDs.
    It handles cases where multiple columns correspond to a single field ID by appending an index to the feature name.

    Parameters:
    ukb_data (pd.DataFrame): The DataFrame whose columns are to be renamed.
    features (dict): A dictionary where keys are new feature names and values are the corresponding field IDs.

    Returns:
    tuple:
        - pd.DataFrame: The DataFrame with renamed columns.
        - list: A list of new feature names that have been assigned to the columns.
    """

    feature_names = []  # Initialize a list to store the new feature names assigned to columns

    for feat, field_id in features.items():
        # Find all columns in the DataFrame that match the given field ID
        cols = filter_cols(ukb_data.columns, [field_id])
        
        if len(cols) > 1:
            # If multiple columns match, rename each by appending an index
            for i, col in enumerate(cols):
                ukb_data = ukb_data.rename(columns={col: f'{feat}_{i}'})
                feature_names.append(f'{feat}_{i}')
        else:
            # If only one column matches, rename it directly
            ukb_data = ukb_data.rename(columns={cols[0]: feat})
            feature_names.append(feat)

    return ukb_data, feature_names
