# ingest.py
import os
import json
import requests
import urllib.parse
import psycopg2
import psycopg2.extras
from datetime import datetime
import h3
import geopandas as gpd
from shapely.geometry import shape

# --- Configuration ---
HISTORICAL_START_DATE = "2025-01-01T00:00:00"
H3_RESOLUTION = 9

# --- Environment Variables ---
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db"
APP_TOKEN = os.getenv("NYC_OPEN_DATA_APP_TOKEN")


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to the database: {e}")
        return None


def get_latest_timestamp(conn):
    """Gets the timestamp of the latest complaint to fetch new data incrementally."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(created_date) FROM complaints;")
        result = cursor.fetchone()[0]
        if result:
            print(
                f"ℹ️  Latest complaint is from: {result}. Fetching new data since then."
            )
            return result.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            print("ℹ️  No existing data found. Starting historical data import.")
            return HISTORICAL_START_DATE


def clean_record(record):
    """Validates, cleans, and calculates the H3 index for a single complaint record."""
    try:
        if not record.get("unique_key"):
            return None
        location_wkt, h3_index = None, None
        lat, lon = record.get("latitude"), record.get("longitude")
        if lat and lon:
            latitude, longitude = float(lat), float(lon)
            location_wkt = f"POINT({longitude} {latitude})"
            h3_index = h3.latlng_to_cell(latitude, longitude, H3_RESOLUTION)
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
    cleaned_data = [clean_record(rec) for rec in batch]
    insert_data = [rec for rec in cleaned_data if rec is not None]
    if not insert_data:
        return 0
    insert_query = "INSERT INTO complaints (unique_key, created_date, closed_date, agency, complaint_type, descriptor, location, h3_index) VALUES %s ON CONFLICT (unique_key) DO NOTHING;"
    with conn.cursor() as cursor:
        try:
            psycopg2.extras.execute_values(cursor, insert_query, insert_data)
            conn.commit()
            print(f"✅ Successfully processed a batch of {len(insert_data)} records.")
            return len(insert_data)
        except Exception as e:
            print(f"❌ Error during batch insert: {e}")
            conn.rollback()
            return 0


def populate_categories(conn):
    """Populates the complaint_categories table from the JSON config file."""
    print("\nPopulating complaint categories...")
    try:
        with open("category_config.json", "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Could not process category_config.json: {e}")
        return
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT DISTINCT complaint_type FROM complaints WHERE complaint_type IS NOT NULL;"
        )
        all_complaint_types = [row[0] for row in cursor.fetchall()]
    category_data = [
        (
            ctype,
            config["category_mapping"].get(ctype, "Miscellaneous"),
            config["priority_order"].get(
                config["category_mapping"].get(ctype, "Miscellaneous"), 99
            ),
        )
        for ctype in all_complaint_types
    ]
    insert_query = "INSERT INTO complaint_categories (complaint_type, category, sort_order) VALUES %s ON CONFLICT (complaint_type) DO UPDATE SET category = EXCLUDED.category, sort_order = EXCLUDED.sort_order;"
    with conn.cursor() as cursor:
        psycopg2.extras.execute_values(cursor, insert_query, category_data)
        conn.commit()
        print(
            f"✅ Successfully populated/updated {len(category_data)} category mappings."
        )


def ensure_hexagons_exist(conn):
    """Ensures every H3 hexagon has a corresponding entry in the h3_hex_data table."""
    print("\nChecking for and creating new hexagon entries...")
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                "INSERT INTO h3_hex_data (h3_index, population, geometry) SELECT DISTINCT h3_index, 0, h3_to_geo_boundary_geometry(h3_index) FROM complaints WHERE h3_index IS NOT NULL ON CONFLICT (h3_index) DO NOTHING;"
            )
            inserted_count = cursor.rowcount
            conn.commit()
            if inserted_count > 0:
                print(
                    f"✅ Inserted {inserted_count} new hexagons with default population."
                )
            else:
                print("ℹ️  No new hexagons found.")
        except Exception as e:
            print(f"❌ Error ensuring hexagons exist: {e}")
            conn.rollback()


def update_population_data(conn):
    """
    Ingests NYC population data from an external API and apportions it to H3 hexagons.

    STEPS:
    1.  Checks if population data already exists to prevent re-running.
    2.  Fetches NYC Neighborhood Tabulation Area (NTA) data, including population
        and geometry, from an ArcGIS FeatureServer API. It handles pagination to
        ensure all records are retrieved.
    3.  Loads the H3 hexagon grid from the `h3_hex_data` table in the database.
    4.  Performs areal interpolation:
        a. Calculates the intersection between each NTA and the H3 hexagons.
        b. Determines the population density of each NTA.
        c. Assigns a portion of an NTA's population to each hexagon based on the
           proportional area of overlap.
    5.  Updates the `population` column in the `h3_hex_data` table with the
        calculated values.
    """
    cursor = conn.cursor()

    # 1. Check if the table has already been populated
    try:
        cursor.execute("SELECT SUM(population) FROM h3_hex_data;")
        total_population = cursor.fetchone()[0]
        if total_population and total_population > 0:
            print(
                "\nPopulation data already exists in 'h3_hex_data'. Skipping ingestion."
            )
            return
    except (psycopg2.Error, TypeError) as e:
        print(f"Error checking for existing data: {e}")
        conn.rollback()
        return

    print("\nStarting population data ingestion...")

    # 2. Fetch NTA data from the API, handling pagination
    all_features = []
    offset = 0
    while True:
        url = "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/NTAData01/FeatureServer/0/query"
        # We need the geometry for interpolation, so returnGeometry=true
        # We request WGS84 (SR 4326) to match our database
        payload = f"where=1%3D1&outFields=NTAName,Pop_20&returnGeometry=true&outSR=4326&f=json&resultOffset={offset}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data from API: {e}")
            return

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)

        if data.get("exceededTransferLimit", False):
            offset += len(features)
        else:
            break

    if not all_features:
        print("No features fetched from the API. Aborting.")
        return

    print(f"Successfully fetched {len(all_features)} NTA records from the API.")

    # Convert API response to a GeoDataFrame
    nta_gdf = gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")
    # Rename columns for clarity
    nta_gdf.rename(columns={"Pop_20": "nta_population"}, inplace=True)
    # Ensure the geometry is valid
    nta_gdf = nta_gdf[nta_gdf.geometry.notna() & (nta_gdf.nta_population > 0)]

    # 3. Load H3 grid from the database
    print("Loading H3 hexagon grid from database...")
    try:
        hex_gdf = gpd.read_postgis(
            "SELECT h3_index, geometry FROM h3_hex_data",
            conn,
            geom_col="geometry",
            crs="EPSG:4326",
        )
    except Exception as e:
        print(f"Failed to read from h3_hex_data table: {e}")
        return

    # 4. Perform Areal Interpolation
    print("Performing areal interpolation to distribute population...")
    # Project to a local CRS for accurate area calculations (e.g., NAD83 / New York Long Island)
    target_crs = "EPSG:2263"
    nta_gdf_proj = nta_gdf.to_crs(target_crs)
    hex_gdf_proj = hex_gdf.to_crs(target_crs)

    # Calculate NTA area and population density
    nta_gdf_proj["nta_area"] = nta_gdf_proj.geometry.area
    nta_gdf_proj["pop_density"] = (
        nta_gdf_proj["nta_population"] / nta_gdf_proj["nta_area"]
    )

    # Find intersections between hexagons and NTAs
    intersections = gpd.overlay(hex_gdf_proj, nta_gdf_proj, how="intersection")

    # Calculate population for each intersecting area
    intersections["intersection_area"] = intersections.geometry.area
    intersections["calculated_pop"] = (
        intersections["pop_density"] * intersections["intersection_area"]
    )

    # Sum the population for each hexagon (as one hex can span multiple NTAs)
    hex_populations = (
        intersections.groupby("h3_index")["calculated_pop"].sum().round().astype(int)
    )

    # 5. Update the database
    print(f"Updating population for {len(hex_populations)} hexagons in the database...")
    update_count = 0
    try:
        with conn.cursor() as cursor:
            for h3_index, population in hex_populations.items():
                if population > 0:
                    cursor.execute(
                        "UPDATE h3_hex_data SET population = %s WHERE h3_index = %s;",
                        (population, h3_index),
                    )
                    update_count += 1
        conn.commit()
        print(
            f"Successfully updated {update_count} records. Population ingestion complete."
        )
    except psycopg2.Error as e:
        print(f"Database update failed: {e}")
        conn.rollback()


def main():
    """Main function to run the data ingestion and categorization."""
    print("--- Starting Complaint Ingestion Process ---")
    conn = get_db_connection()
    if not conn:
        return
    start_date = get_latest_timestamp(conn)
    total_records = 0
    offset = 0
    while True:
        soql = f'SELECT `unique_key`, `created_date`, `closed_date`, `agency`, `complaint_type`, `descriptor`, `latitude`, `longitude` WHERE `created_date` > "{start_date}" ORDER BY `created_date` LIMIT 50000 OFFSET {offset}'
        url = f"https://data.cityofnewyork.us/resource/erm2-nwe9.json?$query={urllib.parse.quote(soql)}"
        print(f"Fetching records from offset {offset}...")
        try:
            resp = requests.get(url, headers={"X-App-Token": APP_TOKEN}, timeout=60)
            resp.raise_for_status()
            batch = resp.json()
        except Exception as e:
            print(f"❌ API Request failed: {e}")
            break
        if not batch:
            print("No new data to fetch.")
            break
        total_records += process_batch(conn, batch)
        if len(batch) < 50000:
            print("Received last batch.")
            break
        offset += 50000
    print(f"\nData ingestion finished. Total new records: {total_records}")
    if total_records > 0:
        ensure_hexagons_exist(conn)
        populate_categories(conn)
        update_population_data(conn)  # Call the new placeholder function
    else:
        print("\nNo new data, skipping post-processing steps.")
    conn.close()
    print("\n--- Complaint Ingestion Process Finished ---")


if __name__ == "__main__":
    main()


# ingest.py
import os
import json
import requests
import urllib.parse
import psycopg2
import psycopg2.extras
from datetime import datetime
import h3

# --- Configuration ---
H3_RESOLUTION = 9

# --- Environment Variables ---
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db"
APP_TOKEN = os.getenv("NYC_OPEN_DATA_APP_TOKEN")


# --- Database Functions ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to the database: {e}")
        return None


# --- Complaint Ingestion ---
def ingest_complaints(conn):
    print("\n--- Starting Complaint Ingestion ---")
    # (This section contains the same complaint fetching logic as before)
    # ... functions for get_latest_timestamp, clean_complaint_record, process_complaint_batch ...
    # ... the main while loop to fetch from the 311 API ...
    print("--- Complaint Ingestion Finished ---")


# --- NEW: Business Ingestion ---
def clean_business_record(record):
    """Cleans a single business record and calculates its H3 index."""
    try:
        lat, lon = record.get("latitude"), record.get("longitude")
        if not lat or not lon:
            return None

        location_wkt = f"POINT({lon} {lat})"
        h3_index = h3.latlng_to_cell(float(lat), float(lon), H3_RESOLUTION)
        return (record.get("license_nbr"), location_wkt, h3_index)
    except (ValueError, TypeError) as e:
        print(f"⚠️  Skipping business record due to cleaning error: {e}")
        return None


def process_business_batch(conn, batch):
    """Processes and inserts a batch of business records."""
    cleaned_data = [clean_business_record(rec) for rec in batch]
    insert_data = [rec for rec in cleaned_data if rec is not None]
    if not insert_data:
        return

    query = "INSERT INTO businesses (license_nbr, location, h3_index) VALUES %s ON CONFLICT (license_nbr) DO NOTHING;"
    with conn.cursor() as cursor:
        psycopg2.extras.execute_values(cursor, query, insert_data)
        conn.commit()


def ingest_businesses(conn):
    """Fetches all active, physical business locations."""
    print("\n--- Starting Business Ingestion ---")
    # This query only needs to be run periodically to refresh the business data.
    # For this script, we'll run it every time, but a check could be added.

    soql_query = """
        SELECT license_nbr, latitude, longitude
        WHERE license_type = 'Premises' AND license_status = 'Active'
    """
    encoded_query = urllib.parse.quote(soql_query)
    full_url = f"https://data.cityofnewyork.us/resource/w7w3-xahh.json?$query={encoded_query}&$limit=200000"

    print("Fetching all active business licenses...")
    try:
        response = requests.get(
            full_url, headers={"X-App-Token": APP_TOKEN}, timeout=300
        )
        response.raise_for_status()
        all_businesses = response.json()
        print(f"Found {len(all_businesses)} active businesses.")
        process_business_batch(conn, all_businesses)
    except requests.exceptions.RequestException as e:
        print(f"❌ Business API Request failed: {e}")
    except json.JSONDecodeError:
        print("❌ Failed to decode JSON from business response.")

    print("--- Business Ingestion Finished ---")


# --- Post-Processing Steps ---
def ensure_hexagons_exist(conn):
    """Ensures h3_hex_data has entries for all known hexagons."""
    print("\nEnsuring all hexagons exist in h3_hex_data...")
    with conn.cursor() as cursor:
        # Combine hexagons from both complaints and businesses
        cursor.execute("""
            INSERT INTO h3_hex_data (h3_index, geometry)
            SELECT h3_index, h3_to_geo_boundary_geometry(h3_index) FROM (
                SELECT h3_index FROM complaints WHERE h3_index IS NOT NULL
                UNION
                SELECT h3_index FROM businesses WHERE h3_index IS NOT NULL
            ) AS all_hexes
            ON CONFLICT (h3_index) DO NOTHING;
        """)
        print(f"✅ Synced hexagon records. {cursor.rowcount} new hexagons added.")
        conn.commit()


def update_business_counts(conn):
    """Aggregates and updates the business_count for each hexagon."""
    print("Updating business counts per hexagon...")
    with conn.cursor() as cursor:
        cursor.execute("""
            WITH counts AS (
                SELECT h3_index, COUNT(*) as b_count FROM businesses GROUP BY h3_index
            )
            UPDATE h3_hex_data SET business_count = counts.b_count
            FROM counts WHERE h3_hex_data.h3_index = counts.h3_index;
        """)
        print(f"✅ Updated business counts for {cursor.rowcount} hexagons.")
        conn.commit()


def update_population_data(conn):
    """# TODO: Placeholder for census data ingestion."""
    print("Skipping population data update (Not Implemented).")
    pass


# --- Main Orchestrator ---
def main():
    conn = get_db_connection()
    if not conn:
        return

    # Ingest raw data first
    # ingest_complaints(conn) # You can uncomment this to run it
    ingest_businesses(conn)

    # Run post-processing and aggregation
    ensure_hexagons_exist(conn)
    update_business_counts(conn)
    update_population_data(conn)

    conn.close()
    print("\n--- Ingestion Process Finished ---")


if __name__ == "__main__":
    main()
