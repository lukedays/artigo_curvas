import time
from io import StringIO

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from interpolation import linear_model, svensson_model
from utils import create_brazilian_business_days_schedule


def get_b3_reference_rates(start_date, end_date):
    """
    Scrape reference rates from B3 website using Selenium and pandas.
    Since it's a dynamic JS page we can't use HTTP requests.
    """

    # Open Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    # Navigate to B3 reference rates page
    driver.get(
        "http://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-taxas-referenciais-bmf-ptBR.asp"
    )

    schedule = create_brazilian_business_days_schedule(start_date, end_date)

    df_result = pd.DataFrame()

    for date in schedule:
        str_date = date.strftime("%d/%m/%Y")
        print(f"Downloading {str_date}")

        # Wait and input start date
        date_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "Data"))
        )
        date_field.clear()
        date_field.send_keys(str_date)

        # Submit form
        submit_button = driver.find_element(By.XPATH, './/button[text()="OK"]')
        submit_button.click()
        time.sleep(0.5)

        # Get page source
        page_source = StringIO(driver.page_source)

        # Use pandas to read HTML tables from source
        tables = pd.read_html(page_source, decimal=",", thousands=".")
        if len(tables) == 0:
            continue

        # Maturities and observed yields
        df = tables[0]
        t_new, y_new = linear_model(df)

        # Filter out errors
        if len(t_new) == 0:
            continue

        # Transform days into years
        df_new = pd.DataFrame({date.strftime("%d/%m/%Y"): y_new}, index=t_new / 365.0)

        df_result = pd.concat([df_result, df_new], join="outer", axis=1)

    # Close the browser
    driver.quit()

    return df_result.T
