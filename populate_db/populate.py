import os
import requests
import urllib.parse
import psycopg2
import psycopg2.extras
from datetime import datetime

# --- Configuration ---
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db"
APP_TOKEN = os.getenv("NYC_OPEN_DATA_APP_TOKEN")
HISTORICAL_START_DATE = "2025-09-01T00:00:00" # Fallback for the very first run

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

def get_latest_timestamp(conn):
    """
    Queries our own database to find the most recent complaint's creation date.
    """
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(created_date) FROM complaints;")
        result = cursor.fetchone()[0]
        if result:
            print(f"ℹ️  Latest record in DB is from: {result}. Fetching new data since then.")
            # Format to ISO 8601 but without microseconds, which can cause issues.
            return result.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            print("ℹ️  No existing data found. Starting historical data import.")
            return HISTORICAL_START_DATE

def clean_record(record):
    """
    Validates and cleans a single record, converting types and handling nulls.
    Returns a tuple of cleaned data, or None if the record is invalid.
    """
    try:
        if not record.get("unique_key"): return None
        latitude = float(record["latitude"]) if record.get("latitude") else None
        longitude = float(record["longitude"]) if record.get("longitude") else None
        created_date = datetime.fromisoformat(record["created_date"]) if record.get("created_date") else None
        closed_date = datetime.fromisoformat(record["closed_date"]) if record.get("closed_date") else None
        return (
            record.get("unique_key"), created_date, closed_date, record.get("agency"),
            record.get("complaint_type"), record.get("descriptor"), latitude, longitude,
        )
    except (ValueError, TypeError) as e:
        print(f"⚠️  Skipping record due to cleaning error (key: {record.get('unique_key')}): {e}")
        return None

def process_batch(conn, batch):
    """
    Processes a batch of records and inserts them into the database efficiently.
    """
    if not batch: return
    cleaned_data = [clean_record(rec) for rec in batch]
    insert_data = [rec for rec in cleaned_data if rec is not None]
    if not insert_data: return

    insert_query = """
        INSERT INTO complaints (
            unique_key, created_date, closed_date, agency,
            complaint_type, descriptor, latitude, longitude
        ) VALUES %s ON CONFLICT (unique_key) DO NOTHING;
    """
    with conn.cursor() as cursor:
        try:
            psycopg2.extras.execute_values(
                cursor, insert_query, insert_data, page_size=len(insert_data)
            )
            conn.commit()
            print(f"✅ Successfully processed a batch of {len(insert_data)} records.")
        except Exception as e:
            print(f"❌ Error during batch insert: {e}")
            conn.rollback()

# --- Main Execution ---
def main():
    """Main function to fetch data incrementally and load it into the database."""
    print("Starting data population process...")
    conn = get_db_connection()
    if not conn: return

    start_date_for_api = get_latest_timestamp(conn)

    BASE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
    LIMIT = 1000
    offset = 0
    total_records_processed = 0

    while True:
        soql_query = f"""
            SELECT
              `unique_key`, `created_date`, `closed_date`, `agency`,
              `complaint_type`, `descriptor`, `latitude`, `longitude`
            WHERE `created_date` > "{start_date_for_api}"
            ORDER BY `created_date`
            LIMIT {LIMIT} OFFSET {offset}
        """
        encoded_query = urllib.parse.quote(soql_query)
        full_url = f"{BASE_URL}?$query={encoded_query}"

        print(f"Fetching records starting from offset {offset}...")
        headers = {"X-App-Token": APP_TOKEN}
        try:
            response = requests.get(full_url, headers=headers, timeout=30)
            response.raise_for_status()
            batch = response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request failed: {e}"); break
        except ValueError:
            print("❌ Failed to decode JSON from response."); break

        if not isinstance(batch, list) or not batch:
            print("No new data to fetch. Exiting loop.")
            break

        process_batch(conn, batch)

        total_records_processed += len(batch)
        if len(batch) < LIMIT:
            print("Received last batch of new data.")
            break
        offset += LIMIT

    print(f"\nData population finished. Total new records processed: {total_records_processed}")
    conn.close()

if __name__ == "__main__":
    main()
