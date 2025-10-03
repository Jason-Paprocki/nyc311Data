import os
import math
import psycopg2
import psycopg2.extras
from datetime import date, timedelta

# --- Configuration ---
DAYS_TO_INCLUDE = 30
# TODO: Adjust this weight to control how much business activity
# influences the final score. Higher value = more influence.
ACTIVITY_WEIGHT = 0.1

# --- Environment Variables ---
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db"


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


def calculate_scores(complaint_count, population, business_count):
    """Calculates all three components of the final impact score."""
    # 1. Calculate Base Score (per-capita resident impact)
    base_score = 0.0
    if population > 0:
        per_capita_rate = complaint_count / population
        weight = math.log(complaint_count + 1)
        base_score = per_capita_rate * weight

    # 2. Calculate Activity Score (commercial density multiplier)
    # The '1 +' ensures areas with no businesses have a neutral multiplier of 1.
    activity_score = 1 + (business_count * ACTIVITY_WEIGHT)

    # 3. Calculate Final Score
    final_score = base_score * activity_score

    return base_score, activity_score, final_score


def main():
    """Calculates and stores daily stats for all H3 hexagons."""
    print("--- Starting Daily Stats Calculation Process ---")
    conn = get_db_connection()
    if not conn:
        return

    today = date.today()
    start_date = today - timedelta(days=DAYS_TO_INCLUDE)

    # Query now joins h3_hex_data to get population and business_count
    query = """
        WITH recent_complaints AS (
            SELECT h3_index, COUNT(*) as complaint_count
            FROM complaints WHERE created_date >= %s GROUP BY h3_index
        )
        SELECT
            h.h3_index,
            h.population,
            h.business_count,
            COALESCE(rc.complaint_count, 0) as complaint_count
        FROM h3_hex_data h
        LEFT JOIN recent_complaints rc ON h.h3_index = rc.h3_index;
    """

    print(f"Fetching data for calculations (complaints since {start_date})...")
    with conn.cursor() as cursor:
        cursor.execute(query, (start_date,))
        rows = cursor.fetchall()

    print(f"Calculating new scores for {len(rows)} hexagons...")
    stats_data = []
    for h3_index, population, business_count, complaint_count in rows:
        base, activity, final = calculate_scores(
            complaint_count, population, business_count
        )
        stats_data.append((h3_index, today, complaint_count, base, activity, final))

    if not stats_data:
        print("ℹ️ No data to process.")
        conn.close()
        return

    # Insert query now populates all the new score columns
    insert_query = """
        INSERT INTO h3_daily_stats (
            h3_index, stats_date, complaint_count,
            base_impact_score, activity_score, final_impact_score
        ) VALUES %s
        ON CONFLICT (h3_index, stats_date) DO UPDATE SET
            complaint_count = EXCLUDED.complaint_count,
            base_impact_score = EXCLUDED.base_impact_score,
            activity_score = EXCLUDED.activity_score,
            final_impact_score = EXCLUDED.final_impact_score;
    """
    print(f"Saving {len(stats_data)} stat records for {today}...")
    with conn.cursor() as cursor:
        psycopg2.extras.execute_values(cursor, insert_query, stats_data)
        conn.commit()
        print("✅ Successfully saved daily stats.")

    conn.close()
    print("\n--- Daily Stats Calculation Finished ---")


if __name__ == "__main__":
    main()
