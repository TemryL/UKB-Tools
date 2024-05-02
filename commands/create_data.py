# Script to create the data based on the field-to-basket mapping produced by get_newest_baskets.py
import sys

sys.path.append(".")
sys.path.append("..")

import argparse
from ukb_tools.logger import logger
from ukb_tools.tools import create_raw_data


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
        df = create_raw_data(mapping_file, ukb_folder)

        # Save to CSV file:
        logger.info(f"Saving data to {out_file}")
        df.to_csv(out_file, index=False)
        logger.info("Data saved successfully.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit()


if __name__ == "__main__":
    main()
