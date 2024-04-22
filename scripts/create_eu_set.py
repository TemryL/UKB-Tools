import sys

sys.path.append(".")
sys.path.append("..")

import argparse
from ukb_tools.logger import logger
from ukb_tools.tools import get_data
from ukb_tools.preprocess.filtering import filter_european_set


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
        ukb_data = get_data(
            raw_data, field_list=[eid, ethnicity_field, genetic_PC_field]
        )
        logger.info(f"Loaded UKB raw data from {raw_data}.")
        ukb_data = ukb_data[[col for col in ukb_data.columns if "Unnamed" not in col]]

        # Create european set:
        eids = filter_european_set(ukb_data)

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
