# main.py

import time
import os
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, SSLError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # Install if necessary
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException,
)
from config import BASE_URL
from data_storage import save_to_csv


def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Optional: Run in headless mode
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def retry_on_stale_element(retries=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException:
                    attempts += 1
                    print(f"Stale element encountered. Retrying... (Attempt {attempts})")
                    time.sleep(delay)
            print(f"Failed to retrieve element after {retries} retries.")
            return None

        return wrapper

    return decorator


@retry_on_stale_element()
def scrape_company_data(driver, link):
    try:
        driver.get(link)
        time.sleep(3)  # Wait for page to load
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "e-table"))
        )
        rows = table.find_elements(By.TAG_NAME, "tr")

        company_data = {}
        for row in rows:
            header_cells = row.find_elements(By.TAG_NAME, "th")
            data_cells = row.find_elements(By.TAG_NAME, "td")
            if header_cells and data_cells:
                key = header_cells[0].text.strip()
                value = data_cells[0].text.strip()
                company_data[key] = value
        return company_data
    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error scraping company: {link}, Error: {e}")
        return None


def check_website_status(url, timeout=10):
    try:
        response = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            return 'Active'
        else:
            return f'Inactive (Status Code: {response.status_code})'
    except (Timeout, ConnectionError):
        return 'Inactive (Connection Error or Timeout)'
    except SSLError:
        return 'Inactive (SSL Error)'
    except RequestException as e:
        return f'Inactive (Error: {e})'


def main():
    print("Current working directory:", os.getcwd())
    driver = setup_driver()
    data = []

    fieldnames = ['Name', 'Sitz', 'Adresse', 'Internet', 'Handelsregister (HR)', 'Bemerkungen', 'Website Status']

    driver.get(BASE_URL)

    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "e-table"))
        )
    except TimeoutException:
        print("Failed to load the table in time.")
        driver.quit()
        return

    links = table.find_elements(By.TAG_NAME, "a")
    print(f"Found {len(links)} companies.")

    company_urls = [link.get_attribute('href') for link in links]

    for index, company_url in enumerate(company_urls):
        try:
            print(f"\nScraping company {index + 1}/{len(company_urls)}: {company_url}")
            company_data = scrape_company_data(driver, company_url)

            if company_data:

                row = {field: company_data.get(field, '') for field in fieldnames}

                website_url = row.get('Internet', '').strip()
                if website_url:
                    if not website_url.startswith(('http://', 'https://')):
                        website_url = 'http://' + website_url
                    status = check_website_status(website_url)
                else:
                    status = 'No URL Provided'
                row['Website Status'] = status

                data.append(row)
                print(f"Scraped data: {row}")
                print(f"Total companies collected so far: {len(data)}")
            else:
                print(f"No data collected for {company_url}")
        except Exception as e:
            print(f"Error scraping company {index + 1}: {e}")
            continue
        finally:
            time.sleep(1)

    driver.quit()

    print(f"Total companies scraped: {len(data)}")
    print("Attempting to save data to CSV...")
    save_to_csv(data)
    print("Data has been saved to CSV.")
    print("Scraping complete! Data saved to scraped_data.csv")


if __name__ == "__main__":
    main()