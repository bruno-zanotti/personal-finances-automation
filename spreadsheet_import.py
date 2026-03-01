#!/usr/bin/env python3

import os
import csv
import logging
import time
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)

logger = logging.getLogger(__name__)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

load_dotenv()

SPREADSHEET_ID = os.getenv("SPREADSHEET_2026_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"

EXPENSES_SHEET = "Expenses"
INCOMES_SHEET = "Incomes"

EXPENSES_CATEGORIES = {
    "Alimentación",
    "Vivienda",
    "Alquiler",
    "Transporte",
    "Servicios",
    "Cargos",
    "Ocios / Salidas",
    "Compras personales",
    "Compras",
    "Bienestar",
    "Salud / Bienestar",
    "Viajes",
    "Otros",
    "Diversos",
}


if not SPREADSHEET_ID:
    raise ValueError("Missing SPREADSHEET_2026_ID in .env")

if not SERVICE_ACCOUNT_FILE:
    raise ValueError("Missing SERVICE_ACCOUNT_FILE in .env")

SERVICE_ACCOUNT_FILE = Path(SERVICE_ACCOUNT_FILE)
if not SERVICE_ACCOUNT_FILE.exists():
    raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")


# -------------------------
# Retry wrapper
# -------------------------

def execute_with_retry(request, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return request.execute()
        except HttpError as e:
            if e.resp.status in (429, 500, 503):
                logger.warning(
                    f"Google API temporary error ({e.resp.status}). Retrying..."
                )
                time.sleep(delay * (attempt + 1))
            else:
                raise
    raise RuntimeError("Google API request failed after retries.")


# -------------------------
# Google Authentication
# -------------------------

def authenticate():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    service = build("sheets", "v4", credentials=credentials)
    return service.spreadsheets()


# -------------------------
# Sheets operations
# -------------------------

def replace_sheet_data(spreadsheet, sheet_name: str, rows: List[List]):
    logger.info(f"Replacing data in sheet {sheet_name}...")

    if not rows:
        logger.info(f"No rows to write in {sheet_name}.")
        return

    body = {"values": rows}

    execute_with_retry(
        spreadsheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A2",
            valueInputOption="USER_ENTERED",
            body=body,
        )
    )

    logger.info(f"{len(rows)} rows written to {sheet_name}.")
# -------------------------
# CSV Processing
# -------------------------

def get_latest_csv() -> Path:
    if not DOWNLOADS_DIR.exists():
        raise FileNotFoundError("Downloads directory does not exist.")

    csv_files = list(DOWNLOADS_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("No CSV files found in downloads folder.")

    latest = max(csv_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Using latest CSV file: {latest.name}")
    return latest


def format_date(date: str) -> str:
    if len(date) != 8:
        raise ValueError(f"Invalid date format: {date}")
    return f"{date[6:8]}/{date[4:6]}/{date[0:4]}"


def read_csv_data(csv_path: Path) -> Tuple[List[List], List[List]]:
    expenses_rows = []
    incomes_rows = []

    logger.info(f"Reading CSV: {csv_path}")

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header

        for row in reader:
            try:
                date, description, amount, _, _, category, _ = row
                is_expense = category in EXPENSES_CATEGORIES

                formatted_row = [
                    format_date(date),
                    category,
                    description,
                    float(amount) if is_expense else (-1) * float(amount),
                ]

            except Exception as e:
                logger.warning(f"Skipping invalid row {row}: {e}")
                continue

            if is_expense:
                expenses_rows.append(formatted_row)
            else:
                incomes_rows.append(formatted_row)

    return expenses_rows, incomes_rows


# -------------------------
# Main
# -------------------------

def run_import():
    spreadsheet = authenticate()

    latest_csv = get_latest_csv()
    expenses_rows, incomes_rows = read_csv_data(latest_csv)

    replace_sheet_data(spreadsheet, EXPENSES_SHEET, expenses_rows)
    replace_sheet_data(spreadsheet, INCOMES_SHEET, incomes_rows)

    logger.info(
        f"Import complete: {len(expenses_rows)} expenses, "
        f"{len(incomes_rows)} incomes."
    )


if __name__ == "__main__":
    run_import()
