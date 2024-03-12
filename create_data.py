# Script to create the data based on the field-to-basket mapping produced by get_newest_baskets.py
import os
import csv
import sys
import json
import argparse
import pandas as pd
import functools as ft
from logger import logger


def get_column_names(csv_file):
    try:
        with open(csv_file, "r", newline="") as file:
            reader = csv.reader(file)
            first_row = next(reader)
        return first_row
    except Exception as e:
        logger.error(f"An error occurred while reading column names from {csv_file}: {e}")
        sys.exit()


def filter_cols(cols, field_list):
    return [col for col in cols if col.split("-")[0] in field_list]


def split_ukb_path(ukb_path):
    try:
        _, project_id, basket_id = os.path.split(ukb_path)[-1].split("_")
        return project_id, basket_id
    except Exception as e:
        logger.error(f"An error occurred while splitting UKB path {ukb_path}: {e}")
        sys.exit()


def get_data(main_ukb_path, field_list, nrows=None):
    try:
        cols = get_column_names(main_ukb_path)
        cols = filter_cols(cols, field_list)
        df = pd.read_csv(main_ukb_path, usecols=cols, nrows=nrows, encoding='latin1')
        return df
    except Exception as e:
        logger.error(f"An error occurred while getting data from {main_ukb_path}: {e}")
        sys.exit()


def create_data(mapping_file, ukb_folder):
    try:
        # Load field to basket mapping:
        with open(mapping_file, "r") as f:
            field_to_basket = json.load(f)

        # Revert mapping:
        basket_to_fields = {}
        for key, value in field_to_basket.items():
            if value not in basket_to_fields:
                basket_to_fields[value] = [key]
            else:
                basket_to_fields[value].append(key)

        # For each baskets load the corresponding fields:
        dfs = []
        for basket, field_list in basket_to_fields.items():
            _, basket_id = split_ukb_path(basket)
            main_ukb_path = os.path.join(ukb_folder, basket, f"ukb{basket_id}.csv")
            logger.info(f"Loading data from {main_ukb_path}")
            df = get_data(main_ukb_path, ["eid"] + field_list)
            if df is not None:
                dfs.append(df)

        # Join all dataframe on "eid" columns:
        df = ft.reduce(lambda left, right: pd.merge(left, right, on="eid"), dfs)
        return df
    except Exception as e:
        logger.error(f"An error occurred while creating data: {e}")
        sys.exit()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("ukb_folder", help="Folder containing the UKB baskets.")
    parser.add_argument(
        "mapping_file", help="Path of JSON file containing the field-to-basket mapping."
    )
    parser.add_argument(
        "out_file",
        help="File to write the resulting dataframe.",
        default="raw_data.csv",
        nargs="?",
        const=1,
    )
    return parser.parse_args()


def main():
    try:
        # Parse arguments:
        args = parse_args()
        ukb_folder = args.ukb_folder
        mapping_file = args.mapping_file
        out_file = args.out_file

        # Create and save the data:
        logger.info("Creating data...")
        df = create_data(mapping_file, ukb_folder)

        # Save to CSV file:
        logger.info(f"Saving data to {out_file}")
        df.to_csv(out_file)
        logger.info("Data saved successfully.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit()


if __name__ == "__main__":
    main()