import time
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def scrape_company_page(company_url):
    try:
        driver.get(company_url)
        time.sleep(5)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//td[text()='Name']/following-sibling::td"))
        )
        print(f"Accessing {company_url}")

        name = driver.find_element(By.XPATH, "//td[text()='Name']/following-sibling::td").text.strip()
        address = driver.find_element(By.XPATH, "//td[text()='Adresse']/following-sibling::td").text.strip()
        website = driver.find_element(By.XPATH, "//td[text()='Internet']/following-sibling::td").text.strip()
        handelsregister = driver.find_element(By.XPATH,
                                              "//td[text()='Handelsregister (HR)']/following-sibling::td").text.strip()

        return {
            "Name": name,
            "Address": address,
            "Website": website,
            "Handelsregister": handelsregister
        }

    except TimeoutException:
        print(f"Timeout while waiting for elements on {company_url}")
        return {
            "Name": None,
            "Address": None,
            "Website": None,
            "Handelsregister": None
        }
    except NoSuchElementException as e:
        print(f"Error extracting data for {company_url}: {e}")
        return {
            "Name": None,
            "Address": None,
            "Website": None,
            "Handelsregister": None
        }


def scrape_all_companies(base_url):
    driver.get(base_url)
    print("Waiting for company links to load...")

    time.sleep(10)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/finma-public/warnungen/warnliste/')]"))
        )
        company_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/finma-public/warnungen/warnliste/')]")
        print(f"Found {len(company_links)} companies.")
        return [link.get_attribute('href') for link in company_links]
    except TimeoutException:
        print("Timeout while loading company links.")
        return []


base_url = "https://www.finma.ch/de/finma-public/warnungen/warnliste/"

company_urls = scrape_all_companies(base_url)

all_company_data = []

for company_url in company_urls:
    print(f"Scraping company: {company_url}")
    company_details = scrape_company_page(company_url)
    if company_details:
        all_company_data.append(company_details)

df = pd.DataFrame(all_company_data)

df.to_csv('scraped_data.csv', index=False)

driver.quit()

print("Scraping complete! Data saved to scraped_data.csv")