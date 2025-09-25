import requests
import json
from urllib.parse import quote
import sys
def process_batch(records):
    """
    Placeholder function to process a batch of records.
    In the future, this is where the database insertion logic will go.
    """
    # For now, we'll just confirm we received the records.
    print(f"  > Processing {len(records)} records in this batch...")
    print(json.dumps(records[0], indent=4))

    pass

def populate_data():
    """
    Fetches the entire NYC 311 dataset in pages and processes each page
    without storing the full dataset in memory.
    """
    print("Starting historical data fetch...")

    # --- Configuration ---
    BASE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
    PAGE_SIZE = 1000
    offset = 230000
    START_DATE = "2025-09-01T00:00:00"

    # --- Pagination & Processing Loop ---
    while True:
        print(f"Fetching records from offset {offset}...")

        # --- Dynamic Query Generation (inside the loop) ---
        # The entire SoQL query, including pagination, must be constructed on each iteration.
        soql_query = (
            "SELECT "
            "`unique_key`, `created_date`, `closed_date`, `agency`, "
            "`complaint_type`, `descriptor`, `latitude`, `longitude` "
            f"WHERE `created_date` >= '{START_DATE}' "
            "ORDER BY `created_date` ASC " # Order ascending to process oldest first
            f"LIMIT {PAGE_SIZE} "
            f"OFFSET {offset}"
        )
        encoded_query = quote(soql_query)
        full_url = f"{BASE_URL}?$query={encoded_query}"

        try:
            response = requests.get(full_url)
            response.raise_for_status()
            batch = response.json()
            if not batch:
                print("No more data to fetch. Exiting loop.")
                break

            # --- Process the current batch immediately ---
            process_batch(batch)

            offset += PAGE_SIZE

        except requests.exceptions.RequestException as e:
            print(f"An error occurred with the API request: {e}")
            break
        except json.JSONDecodeError:
            print("Failed to decode JSON from the response.")
            break

if __name__ == "__main__":
    populate_data()
