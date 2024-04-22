# Feel free to add any useful filtering functions here.
# Please make sure that each function don't modidy the original argument and:
#       - takes a DataFrame containing UKB data as the first argument
#       - returns the list of filtered eids
import sys
import numpy as np
import pandas as pd
from functools import reduce
from ..tools import filter_cols
from ..logger import logger
from .utils import compute_medoid_mem_efficient


def filter_fully_populated_rows(
    ukb_data: pd.DataFrame, field_ids: list[str]
) -> list[int]:
    # Subset data for columns matching the specified field_ids
    cols = filter_cols(ukb_data.columns, field_ids)
    df = ukb_data[cols]
    # Remove row that contains NaN value and return valid eids
    eids = df.dropna().index
    return list(eids)


def filter_partially_populated_rows(
    ukb_data: pd.DataFrame, field_ids: list[str]
) -> list[int]:
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


def filter_ethnicity(ukb_data: pd.DataFrame, ethnicity_code: int) -> list[int]:
    logger.info("Filtering ethnicity...")
    try:
        # Keep eid and ethnicity:
        ethnicity_field = "21000"
        ethnicity_cols = filter_cols(ukb_data.columns, [ethnicity_field])
        if not ethnicity_cols:
            logger.error("No ethnicity columns found after filtering.")
            sys.exit()
        df = ukb_data[ethnicity_cols].copy()

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
        return ukb_data.index.isin(df.index)
    except Exception as e:
        logger.error(f"Error filtering ethnicity: {e}")
        sys.exit()


def filter_european_set(ukb_data: pd.DataFrame) -> list[int]:
    try:
        # Filter individuals with self-reported “British” (code 1001) ancestry according to UKB field 21000:
        eids = filter_ethnicity(ukb_data, ethnicity_code=1001)
        df = ukb_data[eids].copy()
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
