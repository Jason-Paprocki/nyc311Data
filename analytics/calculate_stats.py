import os
import psycopg2

# --- Configuration ---
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db"

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
    Calculates complaint density per type for each community district and
    saves the results to the community_district_stats table.
    """
    print("Starting district statistics calculation...")
    conn = get_db_connection()
    if not conn:
        return

    # This is the main geospatial query that performs the analysis.
    # It joins complaints to districts, groups them by complaint type,
    # and calculates the number of complaints per square kilometer.
    query = """
        -- Step 1: Clear out any old data to ensure our stats are fresh.
        TRUNCATE TABLE community_district_stats;

        -- Step 2: Calculate and insert the new stats.
        INSERT INTO community_district_stats (boro_cd, complaint_type, complaint_count, density_per_sq_km)
        SELECT
            d.boro_cd,
            c.complaint_type,
            COUNT(c.unique_key) AS complaint_count,
            -- Calculate density: total complaints divided by the district's area in sq km.
            -- ST_Area returns area in square meters, so we divide by 1,000,000.
            (COUNT(c.unique_key) / (ST_Area(d.geometry) / 1000000.0)) AS density_per_sq_km
        FROM
            community_districts AS d
        JOIN
            complaints AS c ON ST_Contains(d.geometry, c.location)
        WHERE
            c.complaint_type IS NOT NULL
        GROUP BY
            d.boro_cd, c.complaint_type, d.geometry;
    """

    with conn.cursor() as cursor:
        try:
            print("Running geospatial analysis query...")
            cursor.execute(query)
            conn.commit()
            print(f"✅ Successfully calculated and inserted stats for {cursor.rowcount} district/complaint pairs.")
        except Exception as e:
            print(f"❌ Error during statistics calculation: {e}")
            conn.rollback()
    
    conn.close()
    print("District statistics calculation finished.")


if __name__ == "__main__":
    main()
