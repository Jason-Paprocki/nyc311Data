import os
import requests
import urllib.parse
import psycopg2
import psycopg2.extras  # We need this for efficient batch inserting

# --- Configuration ---
# Load credentials and app token from environment variables
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db"  # Use the service name from docker-compose
APP_TOKEN = os.getenv("NYC_OPEN_DATA_APP_TOKEN")

# --- Database Functions ---
def get_db_connection():
    """Establishes and returns a connection to the database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to the database: {e}")
        return None

def process_batch(conn, batch):
    """
    Processes a batch of records and inserts them into the database efficiently
    using a single, idempotent query.
    """
    if not batch:
        print("Batch is empty, nothing to process.")
        return

    # Prepare the data for insertion into a list of tuples.
    # Using .get() is safer than direct access, as it returns None if a key is missing.
    insert_data = [
        (
            record.get("unique_key"),
            record.get("created_date"),
            record.get("closed_date"),
            record.get("agency"),
            record.get("complaint_type"),
            record.get("descriptor"),
            record.get("latitude"),
            record.get("longitude"),
        )
        for record in batch if record.get("unique_key") # Ensure primary key exists
    ]

    # This is the core of the efficient batch insert.
    # "ON CONFLICT (unique_key) DO NOTHING" makes the script safe to re-run.
    insert_query = """
        INSERT INTO complaints (
            unique_key, created_date, closed_date, agency,
            complaint_type, descriptor, latitude, longitude
        ) VALUES %s
        ON CONFLICT (unique_key) DO NOTHING;
    """

    with conn.cursor() as cursor:
        try:
            # Use execute_values for a highly efficient batch operation
            psycopg2.extras.execute_values(
                cursor, insert_query, insert_data, page_size=len(insert_data)
            )
            conn.commit()
            print(f"✅ Successfully processed a batch of {len(insert_data)} records.")
        except Exception as e:
            print(f"❌ Error during batch insert: {e}")
            conn.rollback()  # Rollback the transaction on error


# --- Main Execution ---
def main():
    """Main function to fetch data from the API and load it into the database."""
    print("Starting data population process...")
    conn = get_db_connection()
    if not conn:
        return

    BASE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
    START_DATE = "2025-09-01T00:00:00" # Hardcoded start for historical data
    LIMIT = 1000
    offset = 0
    total_records_processed = 0

    while True:
        # 1. Craft the SoQL query for the current batch
        soql_query = f"""
            SELECT
              `unique_key`, `created_date`, `closed_date`, `agency`,
              `complaint_type`, `descriptor`, `latitude`, `longitude`
            WHERE `created_date` >= "{START_DATE}"
            ORDER BY `created_date`
            LIMIT {LIMIT}
            OFFSET {offset}
        """
        encoded_query = urllib.parse.quote(soql_query)
        full_url = f"{BASE_URL}?$query={encoded_query}"

        # 2. Fetch the data from the API
        print(f"Fetching records {offset} to {offset + LIMIT}...")
        headers = {"X-App-Token": APP_TOKEN}

        try:
            response = requests.get(full_url, headers=headers)
            response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
            batch = response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request failed: {e}")
            break
        except ValueError: # Catches JSON decoding errors
            print("❌ Failed to decode JSON from response. The API might be down or returned an error page.")
            break

        # 3. Check the exit condition
        if not isinstance(batch, list) or not batch:
            print("No more data to fetch or received an invalid response. Exiting loop.")
            break

        # 4. Process the batch
        process_batch(conn, batch)

        # 5. Prepare for the next iteration
        total_records_processed += len(batch)
        offset += LIMIT

    print(f"\nData population finished. Total records processed: {total_records_processed}")
    conn.close()


if __name__ == "__main__":
    main()
