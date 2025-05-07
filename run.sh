#!/bin/bash

log() {
  local level=$1
  local message=$2
  local timestamp
  timestamp=$(date '+%d/%m/%Y %H:%M:%S')
  echo "[$timestamp] $level: $message"
}


# Load environment variables from .env file
source .env

if [[ "$CRON" == "1" ]]; then
  echo "----------------------------- $(date '+%d/%m/%Y') -----------------------------"
  log 'INFO' "Personal finances automation cron started"
fi

# Run the Sesterce Scraping script
log 'INFO' "Running sesterse_scraping.py..."
python3 $SCRIPT_DIR/sesterse_scraping.py

# Check if the first script succeeded
if [ $? -ne 0 ]; then
  log 'ERROR' "sesterse_scraping.py failed. Exiting."
  exit 1
fi

# Run the second Python script
log 'INFO' "Running spreadsheet_import.py..."
python3 $SCRIPT_DIR/spreadsheet_import.py

# Check if the second script succeeded
if [ $? -ne 0 ]; then
  log 'ERROR' "spreadsheet_import.py failed. Exiting."
  exit 1
fi

# Remove the file
if [ -f "$CSV_FILE_PATH" ]; then
  rm "$CSV_FILE_PATH"
  log 'INFO' "Removed $CSV_FILE_PATH"
else
  log 'ERROR' "File $CSV_FILE_PATH does not exist."
fi
