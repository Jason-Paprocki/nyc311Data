import os
import json
import requests
import urllib.parse
import psycopg2
import psycopg2.extras
from datetime import datetime
import h3

# --- Configuration ---
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db"
APP_TOKEN = os.getenv("NYC_OPEN_DATA_APP_TOKEN")
HISTORICAL_START_DATE = "2025-07-01T00:00:00"
H3_RESOLUTION = 9


# --- Database Functions ---
def get_db_connection():
    """Establishes a connection to the database and returns it."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to the database: {e}")
        return None


def get_latest_timestamp(conn):
    """Gets the timestamp of the latest record to enable incremental updates."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(created_date) FROM complaints;")
        result = cursor.fetchone()[0]
        if result:
            print(
                f"ℹ️  Latest record in DB is from: {result}. Fetching new data since then."
            )
            return result.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            print("ℹ️  No existing data found. Starting historical data import.")
            return HISTORICAL_START_DATE


def clean_record(record):
    """Validates, cleans, and calculates the H3 index for a single record."""
    try:
        if not record.get("unique_key"):
            return None

        location_wkt = None
        h3_index = None
        lat = record.get("latitude")
        lon = record.get("longitude")
        if lat and lon:
            latitude = float(lat)
            longitude = float(lon)
            location_wkt = f"POINT({longitude} {latitude})"
            hex_string = h3.latlng_to_cell(latitude, longitude, H3_RESOLUTION)
            h3_index = int(hex_string, 16)

        created_date = (
            datetime.fromisoformat(record["created_date"])
            if record.get("created_date")
            else None
        )
        closed_date = (
            datetime.fromisoformat(record["closed_date"])
            if record.get("closed_date")
            else None
        )

        return (
            record.get("unique_key"),
            created_date,
            closed_date,
            record.get("agency"),
            record.get("complaint_type"),
            record.get("descriptor"),
            location_wkt,
            h3_index,
        )
    except (ValueError, TypeError) as e:
        print(
            f"⚠️  Skipping record due to cleaning error (key: {record.get('unique_key')}): {e}"
        )
        return None


def process_batch(conn, batch):
    """Processes a batch of records and inserts them into the database."""
    if not batch:
        return
    cleaned_data = [clean_record(rec) for rec in batch]
    insert_data = [rec for rec in cleaned_data if rec is not None]
    if not insert_data:
        return
    insert_query = """
        INSERT INTO complaints (
            unique_key, created_date, closed_date, agency,
            complaint_type, descriptor, location, h3_index
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


def populate_categories(conn):
    """
    Populates the complaint_categories table from a JSON config file.
    """
    print("Populating complaint categories...")
    try:
        with open("category_config.json", "r") as f:
            config = json.load(f)
            category_mapping = config["category_mapping"]
            priority_order = config["priority_order"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"❌ Could not read, parse, or find keys in category_config.json: {e}")
        return

    category_data = []
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT DISTINCT complaint_type FROM complaints WHERE complaint_type IS NOT NULL;"
        )
        all_complaint_types = [row[0] for row in cursor.fetchall()]

    for complaint_type in all_complaint_types:
        category = category_mapping.get(complaint_type, "Other")
        sort_order = priority_order.get(category, 99)
        if category == "Other":
            sort_order = 100
        category_data.append((complaint_type, category, sort_order))

    if not category_data:
        print("ℹ️ No complaint types found to categorize.")
        return

    insert_query = """
        INSERT INTO complaint_categories (complaint_type, category, sort_order)
        VALUES %s
        ON CONFLICT (complaint_type) DO UPDATE SET
            category = EXCLUDED.category,
            sort_order = EXCLUDED.sort_order;
    """
    with conn.cursor() as cursor:
        try:
            psycopg2.extras.execute_values(
                cursor, insert_query, category_data, page_size=len(category_data)
            )
            conn.commit()
            print(
                f"✅ Successfully populated/updated {len(category_data)} category mappings."
            )
        except Exception as e:
            print(f"❌ Error during category insert: {e}")
            conn.rollback()


# --- Main Execution ---
def main():
    """Main function to run the data ingestion and categorization."""
    print("Starting data population process...")
    conn = get_db_connection()
    if not conn:
        return
    start_date_for_api = get_latest_timestamp(conn)
    BASE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
    LIMIT = 50000
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
            response = requests.get(full_url, headers=headers, timeout=60)
            response.raise_for_status()
            batch = response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request failed: {e}")
            break
        except json.JSONDecodeError:
            print("❌ Failed to decode JSON from response.")
            break
        if not isinstance(batch, list) or not batch:
            print("No new data to fetch. Exiting loop.")
            break
        process_batch(conn, batch)
        total_records_processed += len(batch)
        if len(batch) < LIMIT:
            print("Received last batch of new data.")
            break
        offset += LIMIT
    print(
        f"\nData population finished. Total new records processed: {total_records_processed}"
    )

    # After fetching data, populate the categories table
    populate_categories(conn)

    conn.close()


if __name__ == "__main__":
    main()
