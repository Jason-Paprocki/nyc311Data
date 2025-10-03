import os
from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor
import psycopg2
from typing import List, Dict, Any

# --- Router Initialization ---
# This creates a new 'router' which will be imported and included by the main api.py
router = APIRouter()


# --- Database Connection ---
# In a larger app, this might be in a shared 'database.py' or 'utils.py' file.
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
        # Let FastAPI handle this as a generic server error.
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")


# --- API Endpoint Definition ---
@router.get("/", response_model=List[Dict[str, Any]])
def get_complaint_categories():
    """
    Retrieves a list of all complaint categories, sorted for display.
    This endpoint now aligns with the project requirements by returning
    both the category name and its sort order.
    """
    # This SQL query is updated to fetch the 'sort_order' and group by it,
    # which matches the format required by the frontend.
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
        # Use a RealDictCursor to get results as a list of dictionaries
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
    except Exception as e:
        print(f"Database query failed in get_complaint_categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories.")
    finally:
        if conn is not None:
            conn.close()

    # If no results are found, return an empty list as per the response model.
    return results if results is not None else []
