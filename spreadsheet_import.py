#!/usr/bin/env python3

import os
import csv
import logging

from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
logger = logging.getLogger()


# Load environment variables from .env file
load_dotenv()

# The ID of the spreadsheet.
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

CSV_FILE_PATH = os.getenv("CSV_FILE_PATH")

EXPENSES_SHEET = "Expenses"
INCOMES_SHEET = "Incomes"
EXPENSES_CATEGORIES = [
    "Alimentación",
    "Vivienda",
    "Transporte",
    "Servicios",
    "Ocios / Salidas",
    "Compras personales",
    "Salud / Bienestar",
    "Viajes",
    "Otros",
]


def authenticate():
    """Authenticate to Google Sheets API using service account credentials.
    Returns:
    spreadsheet: The Google Sheets API spreadsheet object.
    """
    credentials = None
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    # Create a spreadsheet service
    service = build("sheets", "v4", credentials=credentials)
    spreadsheet = service.spreadsheets()
    return spreadsheet


def clear_tables(spreadsheet):
    """Clear the content of expenses and income tables."""
    # Clear the content of the expenses table
    spreadsheet.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range="Expenses!A2:D",
    ).execute()

    # Clear the content of the incomes table
    spreadsheet.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range="Incomes!A2:D",
    ).execute()


def add_row_to_sheet(spreadsheet, sheet, rows):
    body = {
        "values": rows,
    }
    spreadsheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        range=f"{sheet}!A1",
        body=body,
    ).execute()


def date_format(date):
    """Format the date from 'yyyymmdd' to 'dd/mm/yyyy'."""
    if len(date) == 8:
        return f"{date[6:8]}/{date[4:6]}/{date[0:4]}"
    else:
        logger.warning(f"Invalid date format: {date}. Expected 'yyyymmdd'.")
        raise ValueError("Invalid date format. Expected 'yyyymmdd'.")


def read_csv_data():
    expenses_rows = []
    incomes_rows = []

    # Check if file exists
    if not os.path.exists(CSV_FILE_PATH):
        logger.error(f"File not found: {CSV_FILE_PATH}")
        raise FileNotFoundError(f"File not found: {CSV_FILE_PATH}")

    # Read the CSV file
    logger.info(f"Reading CSV file: {CSV_FILE_PATH}")
    with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:
        csv_reader = csv.reader(f)
        data = list(csv_reader)

    # Read the rows skipping the header
    for date, description, amount, _, _, category, _ in data[1:]:
        # Format the row
        try:
            formatted_date = date_format(date)
            formatted_row = [formatted_date, category, description, float(amount)]
        except ValueError:
            logger.warning(
                f"Skipping invalid row: {date}, {category}, {description}, {amount}"
            )
            continue  # Skip invalid rows

        # Check if the row is an expense or income
        if category in EXPENSES_CATEGORIES:
            expenses_rows.append(formatted_row)
        else:
            # Incomes amount are negative
            incomes_rows.append(formatted_row)

    return expenses_rows, incomes_rows


def main():
    # Authenticate to Google Sheets API
    spreadsheet = authenticate()

    # Clear the content of the tables
    clear_tables(spreadsheet)

    # Read the CSV data
    expenses_rows, incomes_rows = read_csv_data()

    # Add the rows to the sheets
    add_row_to_sheet(spreadsheet, EXPENSES_SHEET, expenses_rows)
    add_row_to_sheet(spreadsheet, INCOMES_SHEET, incomes_rows)

    logger.info(
        f"{len(expenses_rows)} expenses and {len(incomes_rows)} income rows imported successfully!"
    )


if __name__ == "__main__":
    main()
