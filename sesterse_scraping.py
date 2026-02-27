#!/usr/bin/env python3

import os
import sys
import time
import logging
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)

logger = logging.getLogger(__name__)

load_dotenv()

SESTERCE_GROUP_ID = os.getenv("SESTERCE_2026_GROUP_ID")
SESTERCE_GROUP_PASSWORD = os.getenv("SESTERCE_GROUP_PASSWORD")

if not SESTERCE_GROUP_ID or not SESTERCE_GROUP_PASSWORD:
    logger.error("Missing environment variables. Check your .env file.")
    sys.exit(1)

GROUP_URL = f"https://app.sesterce.io/groups/{SESTERCE_GROUP_ID}/share"


def create_driver(download_dir: Path) -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")

    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }

    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Required to allow downloads in headless mode
    driver.execute_cdp_cmd(
        "Page.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": str(download_dir)},
    )

    return driver


def main():
    download_dir = Path(__file__).resolve().parent / "downloads"
    download_dir.mkdir(exist_ok=True)

    driver = create_driver(download_dir)

    try:
        logger.info("Opening Sesterce group page...")
        driver.get(GROUP_URL)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )

        password_field.send_keys(SESTERCE_GROUP_PASSWORD)
        password_field.send_keys(Keys.RETURN)

        buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "button.ses-button--full-width.ses-button-arrow")
            )
        )

        if len(buttons) >= 2:
            logger.info("Clicking export button...")
            buttons[1].click()

            time.sleep(5)  # Wait for download to complete
            logger.info("CSV download triggered.")
        else:
            logger.error("Export button not found.")

    except Exception as e:
        logger.exception(f"Scraping failed: {e}")

    finally:
        driver.quit()
        logger.info("Driver closed.")


if __name__ == "__main__":
    main()
