import os
import csv
import sys
import json
import pandas as pd
import functools as ft
from .logger import logger


def get_baskets(ukb_folder, project_id, field_list):
    try:
        # Get baskets in the folder:
        baskets = os.listdir(ukb_folder)
        basket_dict = {f: [] for f in field_list}
    except FileNotFoundError:
        logger.error(f"The specified folder '{ukb_folder}' does not exist.")
        sys.exit()
    except Exception as e:
        logger.error(f"An error occurred while retrieving baskets: {e}")
        sys.exit()

    # For each basket, load the associated fields:
    for basket in baskets:
        if f"project_{project_id}" in basket:
            try:
                with open(os.path.join(ukb_folder, basket, "fields.ukb"), "r") as f:
                    basket_fields = f.read().splitlines()

                # For each provided field, check if the basket contains it:
                for field in field_list:
                    if field in basket_fields:
                        basket_dict[field].append(basket)

            except FileNotFoundError:
                logger.error(f"fields.ukb file not found for basket: {basket}")
                sys.exit()
            except Exception as e:
                logger.error(f"An error occurred while processing basket {basket}: {e}")
                sys.exit()

    return basket_dict


def create_raw_data(mapping_file, ukb_folder):
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


def get_column_names(csv_file):
    try:
        with open(csv_file, "r", newline="") as file:
            reader = csv.reader(file)
            first_row = next(reader)
        return first_row
    except Exception as e:
        logger.error(
            f"An error occurred while reading column names from {csv_file}: {e}"
        )
        sys.exit()


def get_data(main_ukb_path, field_list, nrows=None):
    try:
        cols = get_column_names(main_ukb_path)
        cols = filter_cols(cols, field_list)
        df = pd.read_csv(main_ukb_path, usecols=cols, nrows=nrows, encoding="latin1")
        return df
    except Exception as e:
        logger.error(f"An error occurred while getting data from {main_ukb_path}: {e}")
        sys.exit()


def get_dtypes(ukb_dict_path, columns):
    ukb_dict = pd.read_csv(ukb_dict_path, sep="\t", dtype=str)
    dtypes = {}

    for col in columns:
        if col == "eid":
            dtypes[col] = int
            continue

        field_id, instance_id, array_id = split_ukb_column(col)
        value_type = ukb_dict[ukb_dict.FieldID == field_id].ValueType.iloc[0]

        if value_type == "Integer":
            dtypes[col] = int
        elif value_type == "Continuous":
            dtypes[col] = float
        else:
            dtypes[col] = str
    return dtypes


def split_ukb_path(ukb_path):
    try:
        _, project_id, basket_id = os.path.split(ukb_path)[-1].split("_")
        return project_id, basket_id
    except Exception as e:
        logger.error(f"An error occurred while splitting UKB path {ukb_path}: {e}")
        sys.exit()


def split_ukb_column(column):
    try:
        if "-" not in column:
            logger.error(
                f"Invalid format for column: {column}. Missing '-' to separate field_id and instance_id/array_id."
            )
            return None, None, None
        if "." not in column:
            logger.error(
                f"Invalid format for column: {column}. Missing '.' to separate instance_id and array_id."
            )
            return None, None, None

        field_id, col = column.split("-")
        instance_id, array_id = col.split(".")
        return field_id, instance_id, array_id
    except ValueError as e:
        logger.error(f"Error splitting column: {column}. Error: {e}")
        return None, None, None


def generate_ukb_column(field_id, instance_id, array_id):
    return f"{field_id}-{instance_id}.{array_id}"


def filter_cols(cols, field_list):
    return [col for col in cols if col.split("-")[0] in field_list]
