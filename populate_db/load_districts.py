import os
import json
import psycopg2
import psycopg2.extras

# --- Configuration ---
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db"
GEOJSON_FILE = "community_districts.geojson"

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

def main():
    """
    Reads the Community Districts GeoJSON file and loads it into the database.
    This is a one-time setup script.
    """
    print("Starting Community District loading process...")
    conn = get_db_connection()
    if not conn:
        return

    try:
        with open(GEOJSON_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {GEOJSON_FILE} not found. Make sure it's in the same directory.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode {GEOJSON_FILE}. Make sure it's a valid GeoJSON file.")
        return

    features = data.get("features", [])
    if not features:
        print("⚠️ No features found in the GeoJSON file.")
        return

    # Prepare data for insertion: (boro_cd, geometry_as_json_string)
    insert_data = []
    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry")
        boro_cd = properties.get("boro_cd")

        if boro_cd and geometry:
            # We pass the geometry as a JSON string; PostGIS will handle the conversion
            insert_data.append((boro_cd, json.dumps(geometry)))

    if not insert_data:
        print("⚠️ No valid district data to insert.")
        return

    # Use ON CONFLICT to prevent errors if the script is run more than once
    insert_query = """
        INSERT INTO community_districts (boro_cd, geometry)
        VALUES (%s, ST_GeomFromGeoJSON(%s))
        ON CONFLICT (boro_cd) DO NOTHING;
    """

    with conn.cursor() as cursor:
        try:
            cursor.executemany(insert_query, insert_data)
            conn.commit()
            print(f"✅ Successfully loaded or verified {cursor.rowcount} community districts.")
        except Exception as e:
            print(f"❌ Error during district insert: {e}")
            conn.rollback()

    conn.close()
    print("Community District loading finished.")


if __name__ == "__main__":
    main()
