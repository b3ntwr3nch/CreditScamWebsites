import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException,
)


def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run headless Chrome for performance
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

        # Debugging output (optional, can be commented out)
        # print(f"Number of rows found: {len(rows)}")

        company_data = {}
        for row in rows:
            header_cells = row.find_elements(By.TAG_NAME, "th")
            data_cells = row.find_elements(By.TAG_NAME, "td")
            if header_cells and data_cells:
                key = header_cells[0].text.strip()
                value = data_cells[0].text.strip()
                company_data[key] = value
                # Debugging output (optional)
                # print(f"Extracted data - {key}: {value}")
            else:
                # Debugging output (optional)
                # print("Row does not have expected structure, skipping.")
                pass

        # Debugging output (optional)
        # print(f"Company data collected: {company_data}")
        return company_data
    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error scraping company: {link}, Error: {e}")
        return None


def main():
    driver = setup_driver()

    csv_file = "scraped_data.csv"
    fieldnames = ['Name', 'Sitz', 'Adresse', 'Internet', 'Handelsregister (HR)', 'Bemerkungen']

    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        driver.get("https://www.finma.ch/de/finma-public/warnungen/warnliste/")

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
                print(f"Scraping company {index + 1}/{len(company_urls)}: {company_url}")
                company_data = scrape_company_data(driver, company_url)

                if company_data:
                    # Create a dictionary with all fieldnames to ensure all keys are present
                    row = {field: company_data.get(field, '') for field in fieldnames}
                    writer.writerow(row)
                else:
                    print(f"No data collected for {company_url}")
            except Exception as e:
                print(f"Error scraping company {index + 1}: {e}")
                continue

    driver.quit()
    print("Scraping complete! Data saved to", csv_file)


if __name__ == "__main__":
    main()