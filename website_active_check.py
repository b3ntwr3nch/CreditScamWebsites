import csv
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, SSLError
import time


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
    input_csv = 'scraped_data.csv'
    output_csv = 'scraped_data_with_status.csv'
    fieldnames = ['Name', 'Sitz', 'Adresse', 'Internet', 'Handelsregister (HR)', 'Bemerkungen', 'Website Status']

    with open(input_csv, mode='r', encoding='utf-8') as infile, \
            open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for index, row in enumerate(reader):
            url = row.get('Internet', '').strip()
            print(f"Checking website {index + 1}: {url}")

            if url:
                if not url.startswith(('http://', 'https://')):
                    url = 'http://' + url  # Default to http

                status = check_website_status(url)
            else:
                status = 'No URL Provided'

            print(f"Website Status: {status}")


            row['Website Status'] = status
            writer.writerow(row)

            time.sleep(0.5)

    print("Website status check complete! Results saved to", output_csv)


if __name__ == "__main__":
    main()