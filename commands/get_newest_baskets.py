# Script to retrieve the most recent basket for a specified UKB project ID for each provided field
# Save the field-to-basket mapping in JSON
import sys

sys.path.append(".")
sys.path.append("..")

import json
import argparse
from ukb_tools.logger import logger
from ukb_tools.tools import get_baskets


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("ukb_folder", help="Folder containing the UKB baskets.")
    parser.add_argument("project_id", help="ID of the UKB project.")
    parser.add_argument("field_list", help="Text file containing the fields.")
    parser.add_argument(
        "out_file",
        help="JSON file to write the field-to-basket mapping",
        default="field_to_basket.json",
        nargs="?",
        const=1,
    )
    return parser.parse_args()


def main():
    # Parse arguments:
    logger.info("Parsing arguments.")
    args = parse_args()
    ukb_folder = args.ukb_folder
    project_id = args.project_id
    out_file = args.out_file

    # Get list of field from the provided file:
    logger.info("Retrieving fields from provided text file.")
    try:
        with open(args.field_list, "r") as f:
            field_list = f.read().splitlines()
    except FileNotFoundError:
        logger.error(f"The specified file {args.field_list} was not found.")
        sys.exit()
    except Exception as e:
        logger.error(f"An error occurred while reading the file: {e}")
        sys.exit()

    # Retrieve baskets for the specified UKB project ID for each provided field:
    logger.info("Retrieving baskets.")
    baskets = get_baskets(ukb_folder, project_id, field_list)

    # Keep only the newest basket:
    logger.info("Keeping only most recent basket for each field.")
    for f, b in baskets.items():
        if len(b) == 0:
            logger.warning(f"Field {f} is missing in project {project_id}.")
        else:
            baskets[f] = max(b)

    # Save baskets in JSON file:
    logger.info("Saving the baskets in JSON file.")
    try:
        with open(out_file, "w") as f:
            json.dump(baskets, f, indent=4, sort_keys=False)
    except FileNotFoundError:
        logger.error(f"Failed to open file: {out_file}. File not found.")
        sys.exit()
    except Exception as e:
        logger.error(f"An error occurred while saving the baskets to JSON file: {e}")
        sys.exit()


if __name__ == "__main__":
    main()
