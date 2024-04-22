import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
from ..tools import filter_cols
from ..logger import logger
from scipy.spatial.distance import cdist, pdist, squareform


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

    feature_names = (
        []
    )  # Initialize a list to store the new feature names assigned to columns

    for feat, field_id in features.items():
        # Find all columns in the DataFrame that match the given field ID
        cols = filter_cols(ukb_data.columns, [field_id])

        if len(cols) > 1:
            # If multiple columns match, rename each by appending an index
            for i, col in enumerate(cols):
                ukb_data = ukb_data.rename(columns={col: f"{feat}_{i}"})
                feature_names.append(f"{feat}_{i}")
        else:
            # If only one column matches, rename it directly
            ukb_data = ukb_data.rename(columns={cols[0]: feat})
            feature_names.append(feat)

    return ukb_data, feature_names


def compute_medoid(X):
    # Drop NaN and convert to numpy
    X = X.dropna().copy()
    X = X.to_numpy()

    logger.info("Computing medoid...")
    try:
        # Calculate the pairwise Euclidean distance matrix:
        distance_matrix = squareform(pdist(X, metric="euclidean"))

        # Compute the sum of distances from each point to all others:
        sum_of_distances = np.sum(distance_matrix, axis=1)

        # Identify the index of the medoid:
        medoid_index = np.argmin(sum_of_distances)
        logger.info("Computed medoid successfully.")
        return X[medoid_index, :]
    except Exception as e:
        logger.error(f"Error computing medoid: {e}")
        sys.exit()


def compute_medoid_mem_efficient(X):
    # Drop NaN and convert to numpy
    X = X.dropna().copy()
    X = X.to_numpy()

    logger.info("Computing medoid...")
    try:
        n_samples = X.shape[0]
        medoid_index = -1
        min_sum_distance = np.inf

        for i in tqdm(range(n_samples)):
            distances = cdist(X[i : i + 1], X, metric="euclidean").flatten()
            sum_distance = np.sum(distances)
            if sum_distance < min_sum_distance:
                min_sum_distance = sum_distance
                medoid_index = i

        logger.info("Computed medoid successfully.")
        return X[medoid_index, :]
    except Exception as e:
        logger.error(f"Error computing medoid: {e}")
        sys.exit()
