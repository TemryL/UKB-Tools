import sys
sys.path.append(".")
sys.path.append("..")

import argparse
import numpy as np
import pandas as pd
from ukb_tools.logger import logger
from ukb_tools.tools import get_data, filter_cols
from scipy.spatial.distance import cdist, pdist, squareform
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_data", help="Path to UKB raw data in CSV.")
    parser.add_argument(
        "out_file",
        help="Text file to write the resulting eids.",
        default="eu_eids.txt",
        nargs="?",
        const=1,
    )
    return parser.parse_args()


def filter_ethnicity(ukb_data, ethnicity_code):
    logger.info("Filtering ethnicity...")
    try:
        # Keep eid and ethnicity:
        ethnicity_field = "21000"
        ethnicity_cols = filter_cols(ukb_data.columns, [ethnicity_field])
        if not ethnicity_cols:
            logger.error("No ethnicity columns found after filtering.")
            sys.exit()
        df = ukb_data[ethnicity_cols]
        
        # Keep participant that only provided the same ethnicity accross instances, excluding NaN:
        valid_rows = df[ethnicity_cols].nunique(axis=1, dropna=True) == 1
        df = df[valid_rows]
        
        # Merge the ethnicity columns into a single column, avoiding NaNs:
        df[ethnicity_field] = df.apply(
            lambda row: next(
                (row[col] for col in ethnicity_cols if pd.notna(row[col])), np.nan
            ),
            axis=1,
        )
        df[ethnicity_field] = df[ethnicity_field].astype(int)
        
        # Keep self-reported ethnicity_code:
        df = df[df[ethnicity_field] == ethnicity_code]

        logger.info(f"Filtered ethnicity successfully, {len(df)} rows retained.")
        return ukb_data[ukb_data.index.isin(df.index)]
    except Exception as e:
        logger.error(f"Error filtering ethnicity: {e}")
        sys.exit()


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
            distances = cdist(X[i:i+1], X, metric="euclidean").flatten()
            sum_distance = np.sum(distances)
            if sum_distance < min_sum_distance:
                min_sum_distance = sum_distance
                medoid_index = i
                
        logger.info("Computed medoid successfully.")
        return X[medoid_index, :]
    except Exception as e:
        logger.error(f"Error computing medoid: {e}")
        sys.exit()


def create_european_set(ukb_data):
    try:
        # Filter individuals with self-reported “British” (code 1001) ancestry according to UKB field 21000:
        df = filter_ethnicity(ukb_data, ethnicity_code=1001)
        if df.empty:
            logger.error("European set is empty after filtering ethnicity.")
            sys.exit()

        # Compute the medoid of the "“British”" ancestry set in the 15 first dimension of genetic principal components (PC):
        dim = 15
        genetic_PC_field = "22009"
        genetic_PC_cols = filter_cols(ukb_data.columns, [genetic_PC_field])
        if not genetic_PC_cols:
            logger.error("No genetic PC columns found after filtering.")
            sys.exit()

        genetic_PC = df[genetic_PC_cols[:dim]]
        medoid = compute_medoid_mem_efficient(genetic_PC)
        if medoid is None:
            logger.error("Failed to compute medoid.")
            sys.exit()

        # Compute the distance of each individual in the UK Biobank to this medoid:
        logger.info("Computing distance to medoid...")
        distances = np.sqrt(
            ((ukb_data[genetic_PC_cols[:dim]] - medoid) ** 2).sum(axis=1)
        )
        
        # Select all individuals with a British-medoid distance of less than 40:
        eids = list(ukb_data[distances < 40].eid)
        logger.info(
            f"Created European set successfully, {len(eids)} individuals included."
        )
        return eids
    except Exception as e:
        logger.error(f"Error creating European set: {e}")
        sys.exit()


def main():
    try:
        # Parse arguments:
        logger.info("Parsing arguments...")
        args = parse_args()
        raw_data = args.raw_data
        out_file = args.out_file

        # Load UKB raw data
        logger.info("Loading UKB raw data...")
        eid = "eid"
        ethnicity_field = "21000"
        genetic_PC_field = "22009"
        ukb_data = get_data(raw_data, field_list=[eid, ethnicity_field, genetic_PC_field])
        logger.info(f"Loaded UKB raw data from {raw_data}.")
        ukb_data = ukb_data[[col for col in ukb_data.columns if "Unnamed" not in col]]
        
        # Create european set:
        eids = create_european_set(ukb_data)
        
        # Save eids:
        logger.info("Saving European set eids...")
        with open(out_file, "w") as f:
            for eid in eids:
                f.write(f"{eid}\n")
        logger.info(f"European set eids saved to {out_file}.")
    except Exception as e:
        logger.error(f"Failed in main execution: {e}")
        sys.exit()


if __name__ == "__main__":
    main()