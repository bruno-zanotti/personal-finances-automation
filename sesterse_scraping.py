#!/usr/bin/env python3

import os
import time
import logging


from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)

logger = logging.getLogger()

# Load environment variables from .env file
load_dotenv()

SESTERCE_GROUP_ID = os.getenv("SESTERCE_GROUP_ID")
SESTERCE_GROUP_PASSWORD = os.getenv("SESTERCE_GROUP_PASSWORD")
GROUP_URL = "https://app.sesterce.io/groups/" + SESTERCE_GROUP_ID + "/share"

""" This script uses Selenium to automate the process of logging into a Sesterce group and downloading a CSV file."""


def main():
    # Set up the Chrome WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    # Initialize the WebDriver in headless mode
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open the Sesterce group URL
        driver.get(GROUP_URL)

        # Search for the password field
        password_field = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "password"))
        )

        # Introduce the password
        password_field.send_keys(SESTERCE_GROUP_PASSWORD)

        # Submit the first form
        password_field.send_keys(Keys.RETURN)

        # Search button "Exportar datos"
        buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "button.ses-button--full-width.ses-button-arrow")
            )
        )
        # There are two buttons, the first one is "Enviar un resumen" and the second one is "Exportar datos"
        if len(buttons) >= 2:
            export_button = buttons[1]
            export_button.click()
            time.sleep(1)
            logger.info("The CSV file has been successfully downloaded.")
        else:
            logger.error("Buttons not found or not enough buttons available.")

    except Exception as e:
        logger.error("Button not found or failed to click:\n", e)

    finally:
        # Close the WebDriver
        driver.quit()


if __name__ == "__main__":
    main()
