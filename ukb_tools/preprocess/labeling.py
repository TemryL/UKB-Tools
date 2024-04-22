from typing import List, Tuple, Callable, Dict
from datetime import datetime
import pandas as pd
from ..tools import filter_cols, split_ukb_column, generate_ukb_column


def match_phenotype(
    row: pd.Series, phenotype_rules: List[Tuple[str, Callable[[str], bool]]]
) -> bool:
    """
    Evaluate a row from a DataFrame against a set of phenotype rules to determine if any condition is met.

    Parameters:
    row (pd.Series): A row of data, typically representing a single participant's record.
    phenotype_rules (list of tuples): Each tuple contains a field ID and a callable condition
                                      function to apply to values from columns associated with that field.

    Returns:
    bool: True if any of the conditions are met for the given row, otherwise False.
    """
    for field_id, condition in phenotype_rules:
        cols = filter_cols(row.index, [field_id])
        for col in cols:
            if field_id in ["41271", "41270"]:  # Specific handling for ICD codes
                val = str(row[col])
            else:
                val = row[col]

            if condition(val):
                return True
    return False


def match_phenotype_columns(
    row: pd.Series, phenotype_rules: List[Tuple[str, Callable[[str], bool]]]
) -> List[str]:
    """
    Identify and return column names from a row that match any condition specified in the phenotype rules.

    Parameters:
    row (pd.Series): A row of data, typically representing a single participant's record.
    phenotype_rules (list of tuples): Each tuple contains a field ID and a callable condition
                                      function that checks column values against the condition.

    Returns:
    list: A list of column names that match the specified conditions.
    """
    matching_columns = []
    for field_id, condition in phenotype_rules:
        cols = filter_cols(row.index, [field_id])
        for col in cols:
            if field_id in ["41271", "41270"]:  # Specific handling for ICD codes
                val = str(row[col])
            else:
                val = row[col]

            if condition(val):
                matching_columns.append(col)
    return matching_columns


def get_diagnosis_dates(
    row: pd.Series,
    phenotype_rules: List[Tuple[str, Callable[[str], bool]]],
    diagnosis_date_fields: Dict[str, str],
) -> List[str]:
    """
    Extracts and returns the diagnosis dates for all conditions met in the phenotype rules.

    Parameters:
    row (pd.Series): A row of data, typically representing a single participant's record.
    phenotype_rules (list of tuples): Phenotype rules to identify matching conditions.
    diagnosis_date_fields (dict): A mapping from field IDs to their respective date fields.

    Returns:
    list: A list of dates representing the diagnosis dates for matched conditions.
    """
    matching_cols = match_phenotype_columns(row, phenotype_rules)
    dates = []
    for col in matching_cols:
        field_id, instance_id, array_id = split_ukb_column(col)
        try:
            date_field = diagnosis_date_fields[field_id]
        except KeyError:
            date_field = "53"  # Default field if not specified
            array_id = 0

        date_col = generate_ukb_column(date_field, instance_id, array_id)
        dates.append(row[date_col])
    return dates


def get_first_diagnosis_date(
    row: pd.Series,
    phenotype_rules: List[Tuple[str, Callable[[str], bool]]],
    diagnosis_date_fields: Dict[str, str],
) -> str:
    """
    Finds and returns the first (earliest) diagnosis date from a set of matched conditions.

    Parameters:
    row (pd.Series): A row of data.
    phenotype_rules (list of tuples): Rules to match conditions.
    diagnosis_date_fields (dict): Field IDs to date field mappings.

    Returns:
    str: The earliest diagnosis date in "YYYY-MM-DD" format, or an empty string if no dates are found.
    """
    diagnosis_dates = get_diagnosis_dates(row, phenotype_rules, diagnosis_date_fields)
    dates = [datetime.strptime(date, "%Y-%m-%d") for date in diagnosis_dates if date]

    if dates:
        first_date = min(dates)
        return first_date.strftime("%Y-%m-%d")
    else:
        return ""
