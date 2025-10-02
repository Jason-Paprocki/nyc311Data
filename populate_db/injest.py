import os
import json
import requests
import urllib.parse
import psycopg2
import psycopg2.extras
from datetime import datetime
import h3
import geopandas as gpd

# --- Configuration ---
HISTORICAL_START_DATE = "2025-08-01T00:00:00"
H3_RESOLUTION = 9
API_BATCH_SIZE = 50000

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


def get_latest_complaint_timestamp(conn):
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


def clean_complaint_record(record):
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


def process_complaint_batch(conn, batch):
    """Processes a batch of complaint records and inserts them into the database."""
    cleaned_data = [clean_complaint_record(rec) for rec in batch]
    insert_data = [rec for rec in cleaned_data if rec is not None]
    if not insert_data:
        return 0
    insert_query = """
        INSERT INTO complaints (unique_key, created_date, closed_date, agency, complaint_type, descriptor, location, h3_index)
        VALUES %s
        ON CONFLICT (unique_key) DO NOTHING;
    """
    with conn.cursor() as cursor:
        try:
            psycopg2.extras.execute_values(cursor, insert_query, insert_data)
            conn.commit()
            return len(insert_data)
        except Exception as e:
            print(f"❌ Error during complaint batch insert: {e}")
            conn.rollback()
            return 0


def ingest_complaints(conn):
    """Fetches new 311 complaints since the last recorded one."""
    print("\n--- Starting Complaint Ingestion (Incremental Update) ---")
    start_date = get_latest_complaint_timestamp(conn)
    total_records = 0
    offset = 0
    while True:
        soql = f'SELECT `unique_key`, `created_date`, `closed_date`, `agency`, `complaint_type`, `descriptor`, `latitude`, `longitude` WHERE `created_date` > "{start_date}" ORDER BY `created_date` LIMIT {API_BATCH_SIZE} OFFSET {offset}'
        url = f"https://data.cityofnewyork.us/resource/erm2-nwe9.json?$query={urllib.parse.quote(soql)}"
        print(f"Fetching complaint records from offset {offset}...")
        try:
            resp = requests.get(url, headers={"X-App-Token": APP_TOKEN}, timeout=120)
            resp.raise_for_status()
            batch = resp.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"❌ API Request failed: {e}")
            raise
        if not batch:
            break
        processed_count = process_complaint_batch(conn, batch)
        if processed_count > 0:
            print(
                f"✅ Successfully processed a batch of {processed_count} complaint records."
            )
        total_records += processed_count
        if len(batch) < API_BATCH_SIZE:
            break
        offset += API_BATCH_SIZE
    print(f"--- Complaint Ingestion Finished. Total new records: {total_records} ---")
    return total_records


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


def ingest_businesses(conn):
    """Performs a safe, full refresh of the businesses table with pagination."""
    print("\n--- Starting Business Ingestion (Full Refresh) ---")
    cursor = conn.cursor()
    temp_table_name = "businesses_new"
    try:
        print(f"Creating and clearing temporary table '{temp_table_name}'...")
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {temp_table_name} (LIKE businesses INCLUDING ALL);"
        )
        cursor.execute(f"TRUNCATE TABLE {temp_table_name};")
        conn.commit()
        total_records = 0
        offset = 0
        base_url = "https://data.cityofnewyork.us/resource/w7w3-xahh.json"
        while True:
            params = {
                "$select": "license_nbr,latitude,longitude",
                "$where": "license_type = 'Premises' AND license_status = 'Active'",
                "$limit": API_BATCH_SIZE,
                "$offset": offset,
            }
            print(f"Fetching business records from offset {offset}...")
            response = requests.get(
                base_url, headers={"X-App-Token": APP_TOKEN}, params=params, timeout=300
            )
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            cleaned_data = [clean_business_record(rec) for rec in batch]
            insert_data = [rec for rec in cleaned_data if rec is not None]
            if insert_data:
                insert_query = f"INSERT INTO {temp_table_name} (license_nbr, location, h3_index) VALUES %s ON CONFLICT (license_nbr) DO NOTHING;"
                psycopg2.extras.execute_values(
                    cursor, insert_query, insert_data, page_size=len(insert_data)
                )
                total_records += len(insert_data)
                print(f"✅ Inserted batch of {len(insert_data)} business records.")
            if len(batch) < API_BATCH_SIZE:
                break
            offset += API_BATCH_SIZE
        print(
            f"Ingestion complete. Total valid records: {total_records}. Swapping tables..."
        )
        cursor.execute(
            "ALTER TABLE businesses RENAME TO businesses_old; ALTER TABLE businesses_new RENAME TO businesses; DROP TABLE businesses_old;"
        )
        conn.commit()
        print("✅ Business data refresh complete.")
    except (
        requests.exceptions.RequestException,
        json.JSONDecodeError,
        psycopg2.Error,
    ) as e:
        print(f"❌ An error occurred during business ingestion. Rolling back changes.")
        conn.rollback()
        raise
    finally:
        cursor.close()


def ensure_hexagons_exist(conn):
    """
    Calculates hexagon geometries in Python and inserts them into the database.
    This removes the dependency on the h3_postgis database extension.
    """
    print("\nEnsuring all hexagons exist in h3_hex_data...")
    with conn.cursor() as cursor:
        # Step 1: Get all unique H3 indexes from our raw data tables
        cursor.execute("""
            SELECT h3_index FROM complaints WHERE h3_index IS NOT NULL
            UNION
            SELECT h3_index FROM businesses WHERE h3_index IS NOT NULL
        """)
        # The fetchall() result is a list of tuples, e.g., [('892a100d6ffffff',), ...]
        all_hex_indexes = {row[0] for row in cursor.fetchall()}

        if not all_hex_indexes:
            print("ℹ️  No H3 indexes found to process.")
            return

        # Step 2: In Python, calculate the geometry for each H3 index
        insert_data = []
        for h3_index in all_hex_indexes:
            try:
                # h3.cell_to_boundary returns a list of (lat, lon) tuples
                boundary = h3.cell_to_boundary(h3_index)

                # FIX: Join with a comma and a space ", " to create a valid WKT string.
                # e.g., POLYGON((lon1 lat1, lon2 lat2, lon3 lat3, lon1 lat1))
                wkt_coords = ", ".join([f"{lon} {lat}" for lat, lon in boundary])

                # Close the polygon by adding the first point to the end
                first_point = f"{boundary[0][1]} {boundary[0][0]}"
                wkt_polygon = f"POLYGON(({wkt_coords}, {first_point}))"
                insert_data.append((h3_index, wkt_polygon))
            except Exception as e:
                print(f"⚠️  Could not generate geometry for H3 index {h3_index}: {e}")

        # Step 3: Bulk insert the hexagon data into the master table
        if not insert_data:
            print("ℹ️  No valid geometries to insert.")
            return

        insert_query = "INSERT INTO h3_hex_data (h3_index, geometry) VALUES %s ON CONFLICT (h3_index) DO NOTHING;"
        psycopg2.extras.execute_values(cursor, insert_query, insert_data)
        print(f"✅ Synced hexagon records. {cursor.rowcount} new hexagons added.")
        conn.commit()


import geopandas as gpd
import pandas as pd
import psycopg2.extras
import requests
import os
from shapely.geometry import Polygon, MultiPolygon
from shapely.errors import ShapelyError


def update_population_data(conn):
    """
    Ingests and apportions NYC population data to H3 hexagons.

    This version includes more specific error handling and support for MultiPolygon geometries.

    Args:
        conn: A psycopg2 database connection object.
    """
    print("\n--- Starting Population Data Update ---")
    # Suggestion: Group configuration variables at the top or in a separate file.
    NTA_API_URL = "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/NTAData01/FeatureServer/0/query"
    TARGET_CRS = "EPSG:2263"  # NAD83 / New York Long Island (ftUS)
    SOURCE_CRS = "EPSG:4326"  # WGS 84
    with conn.cursor() as cursor:
        cursor.execute("SELECT SUM(population) FROM h3_hex_data;")
        # Good check for idempotency. No changes needed here.
        if (cursor.fetchone()[0] or 0) > 0:
            print("ℹ️  Population data already exists. Skipping.")
            return

    print("Population data is missing. Starting ingestion process...")

    # --- Data Fetching ---
    # This loop is well-structured for handling API pagination.
    all_features = []
    offset = 0
    while True:
        payload = f"where=1%3D1&outFields=*&returnGeometry=true&outSR={SOURCE_CRS.split(':')[1]}&f=json&resultOffset={offset}"
        try:
            response = requests.post(
                NTA_API_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=payload,
                timeout=30,  # Suggestion: Add a timeout to prevent indefinite hanging.
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch population data from API: {e}")
            raise

        features = data.get("features", [])
        if not features:
            break
        all_features.extend(features)
        if not data.get("exceededTransferLimit"):
            break
        offset += len(features)

    print(f"Successfully fetched {len(all_features)} NTA records.")

    # --- Data Parsing and GeoDataFrame Creation ---
    all_attributes = []
    all_geometries = []
    print("Parsing records to build GeoDataFrame...")
    for feature in all_features:
        props = feature.get("attributes")
        geom_dict = feature.get("geometry")

        if (
            not isinstance(props, dict)
            or not isinstance(geom_dict, dict)
            or "rings" not in geom_dict
        ):
            continue

        try:
            # Suggestion: The source data might contain MultiPolygons. It's safer to handle both.
            # We can create a helper function or a small loop to build the geometry.
            rings = geom_dict["rings"]
            if len(rings) == 1:
                geom = Polygon(rings[0])
            else:
                # This handles MultiPolygons by creating a list of Polygon objects.
                geom = MultiPolygon([Polygon(ring) for ring in rings])

            all_attributes.append(props)
            all_geometries.append(geom)
        except (ShapelyError, TypeError, IndexError) as e:
            # Suggestion: Catch more specific exceptions than the general `Exception`.
            # This helps in debugging and avoids accidentally catching unrelated errors.
            print(f"⚠️  Could not parse a geometry, skipping. Error: {e}")
            continue

    retained_count = len(all_attributes)
    print(f"Successfully parsed {retained_count} of {len(all_features)} records.")

    if not all_attributes:
        print(
            "❌ No valid population features found after parsing. Halting population update."
        )
        return

    df = pd.DataFrame(all_attributes)
    nta_gdf = gpd.GeoDataFrame(df, geometry=all_geometries, crs=SOURCE_CRS)

    nta_gdf.rename(columns={"Pop_20": "nta_population"}, inplace=True)
    nta_gdf["nta_population"] = pd.to_numeric(
        nta_gdf["nta_population"], errors="coerce"
    ).fillna(0)

    # The diagnostic block is excellent for data validation. No changes needed.
    zero_pop_ntas = nta_gdf[nta_gdf["nta_population"] == 0]
    if not zero_pop_ntas.empty:
        print("\n--- 🕵️‍♂️ Debugging: The following NTAs have a population of 0 ---")
        sorted_ntas = zero_pop_ntas.sort_values(by=["BoroName", "NTAName"])
        for index, row in sorted_ntas.iterrows():
            print(f"  - {row.get('BoroName', 'N/A')}: {row.get('NTAName', 'N/A')}")
        print("----------------------------------------------------------------\n")

    # --- Areal Interpolation ---
    print("Reading hexagon data from database...")
    try:
        hex_gdf = gpd.read_postgis(
            "SELECT h3_index, geometry FROM h3_hex_data",
            conn,
            geom_col="geometry",
            crs=SOURCE_CRS,
        )
    except Exception as e:
        print(f"❌ Failed to read h3_hex_data from the database: {e}")
        return

    print("Performing areal interpolation...")
    # Using a projected CRS for area calculations is the correct approach.
    nta_gdf_proj = nta_gdf.to_crs(TARGET_CRS)
    hex_gdf_proj = hex_gdf.to_crs(TARGET_CRS)

    nta_gdf_proj["nta_area"] = nta_gdf_proj.geometry.area

    # Avoid division by zero by replacing zero area with a very small number or NaN,
    # then filling NaN densities with 0.
    mask = nta_gdf_proj["nta_area"] > 0
    nta_gdf_proj["pop_density"] = 0.0
    nta_gdf_proj.loc[mask, "pop_density"] = (
        nta_gdf_proj.loc[mask, "nta_population"] / nta_gdf_proj.loc[mask, "nta_area"]
    )

    # The overlay operation is the core of the interpolation. This is correct.
    intersections = gpd.overlay(hex_gdf_proj, nta_gdf_proj, how="intersection")
    intersections["calculated_pop"] = (
        intersections.geometry.area * intersections["pop_density"]
    )

    # --- FIX: Custom rounding to prevent zero-population in populated areas ---
    # The original calculation could round small fractional populations (<0.5) down to 0,
    # causing hexagons on the edges of populated areas to be missed.

    # 1. Group by hexagon and sum the calculated float populations.
    hex_populations_float = intersections.groupby("h3_index")["calculated_pop"].sum()

    # 2. Apply custom rounding logic.
    #    - If calculated population is between 0 and 1, round it up to 1.
    #    - Otherwise, use standard rounding.
    #    This ensures that any hexagon with a fractional share of a populated
    #    area is assigned at least one person.
    hex_populations = hex_populations_float.apply(
        lambda pop: 1 if 0 < pop < 1 else round(pop)
    ).astype(int)

    # 3. Prepare data for the database update, filtering out any hexagons that
    #    still have a population of 0 (e.g., from unpopulated NTAs).
    update_data = [(pop, idx) for idx, pop in hex_populations.items() if pop > 0]

    if not update_data:
        print("ℹ️  No population data to update after interpolation.")
        return

    # --- Database Update ---
    print(f"Updating population for {len(update_data)} hexagons...")
    # Using execute_values is highly efficient for bulk updates. Great choice.
    update_query = "UPDATE h3_hex_data SET population = data.pop FROM (VALUES %s) AS data (pop, h3_index) WHERE h3_hex_data.h3_index = data.h3_index;"

    with conn.cursor() as cursor:
        try:
            psycopg2.extras.execute_values(
                cursor, update_query, update_data, page_size=len(update_data)
            )
            conn.commit()
            print(f"✅ Successfully updated {cursor.rowcount} records.")
        except psycopg2.Error as e:
            print(f"❌ Database update failed: {e}")
            conn.rollback()  # Rollback the transaction on error.


def update_business_counts(conn):
    """Aggregates and updates the business_count for each hexagon."""
    print("\nUpdating business counts per hexagon...")
    with conn.cursor() as cursor:
        cursor.execute("UPDATE h3_hex_data SET business_count = 0;")
        print(f"Reset business counts for {cursor.rowcount} hexagons.")
        cursor.execute("""
            WITH counts AS (
                SELECT h3_index, COUNT(*) as b_count FROM businesses GROUP BY h3_index
            )
            UPDATE h3_hex_data SET business_count = counts.b_count
            FROM counts WHERE h3_hex_data.h3_index = counts.h3_index;
        """)
        print(f"✅ Updated business counts for {cursor.rowcount} hexagons.")
        conn.commit()


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
    category_data = []
    for ctype in all_complaint_types:
        category = config["category_mapping"].get(ctype, "Miscellaneous")
        sort_order = config["priority_order"].get(category, 99)
        category_data.append((ctype, category, sort_order))
    insert_query = """
        INSERT INTO complaint_categories (complaint_type, category, sort_order) VALUES %s
        ON CONFLICT (complaint_type) DO UPDATE SET
            category = EXCLUDED.category,
            sort_order = EXCLUDED.sort_order;
    """
    with conn.cursor() as cursor:
        psycopg2.extras.execute_values(cursor, insert_query, category_data)
        conn.commit()
        print(
            f"✅ Successfully populated/updated {len(category_data)} category mappings."
        )


def main():
    """Main function to run the full data ingestion and aggregation pipeline."""
    print("🚀 --- Starting Full Data Ingestion Process --- 🚀")
    conn = get_db_connection()
    if not conn:
        return
    try:
        new_complaints = ingest_complaints(conn)
        ingest_businesses(conn)
        ensure_hexagons_exist(conn)
        update_population_data(conn)
        update_business_counts(conn)
        if new_complaints > 0:
            populate_categories(conn)
        else:
            print("\nℹ️  No new complaints, skipping category population.")
    except Exception as e:
        print(f"\n❌ A critical error occurred during data ingestion: {e}")
        print("--- Ingestion Process Halted ---")
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection closed.")
    print("\n🏁 --- Ingestion Process Finished --- 🏁")


if __name__ == "__main__":
    main()
