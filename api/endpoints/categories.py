import os
from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor
import psycopg2
from typing import List, Dict, Any

router = APIRouter()


def get_db_connection():
    """Establishes a connection to the database and returns it."""
    try:
        conn = psycopg2.connect(
            host="db",
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
        return conn
    except psycopg2.OperationalError as e:
        # This error happens if the API container cannot reach the DB container.
        print(f"🔴 DATABASE CONNECTION FAILED: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")


@router.get("", response_model=List[Dict[str, Any]])
def get_complaint_categories():
    """
    Retrieves a list of all complaint categories, sorted for display.
    """
    # --- ADDED FOR DEBUGGING ---
    print("✅ Request received for /categories endpoint.")
    # --- END DEBUGGING ADD ---

    query = """
        SELECT
            category,
            sort_order
        FROM complaint_categories
        WHERE category IS NOT NULL AND category <> ''
        GROUP BY category, sort_order
        ORDER BY sort_order;
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            # --- ADDED FOR DEBUGGING ---
            print(f"✅ Query successful, found {len(results)} categories.")
            # --- END DEBUGGING ADD ---
    except Exception as e:
        # --- MODIFIED FOR DEBUGGING ---
        # This will now print the *exact* SQL error to the logs.
        print(f"❌ DATABASE QUERY FAILED: {e}")
        # --- END DEBUGGING MODIFICATION ---
        raise HTTPException(status_code=500, detail="Failed to retrieve categories.")
    finally:
        if conn is not None:
            conn.close()

    return results if results is not None else []
