import os
from fastapi import APIRouter, HTTPException, Query
from psycopg2.extras import RealDictCursor
import psycopg2
from typing import Dict, Any

# --- Router Initialization ---
router = APIRouter()


# --- Database Connection ---
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
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")


# --- API Endpoint Definition ---
@router.get("", response_model=Dict[str, Any])
def get_points_data(
    category: str = Query(..., description="The complaint category to filter by."),
    bbox: str = Query(
        ..., description="Bounding box as min_lon,min_lat,max_lon,max_lat"
    ),
):
    """
    Retrieves individual 311 complaint locations as GeoJSON Points for a
    given bounding box and category. Used for higher zoom levels.
    """
    try:
        # Parse the bounding box string
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid bbox format. Use min_lon,min_lat,max_lon,max_lat.",
        )

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # This query fetches individual complaints within the specified
            # bounding box and for the given category.
            query = """
                SELECT
                    c.unique_key,
                    c.complaint_type,
                    c.latitude,
                    c.longitude
                FROM complaints c
                JOIN complaint_categories cc ON c.complaint_type = cc.complaint_type
                WHERE
                    cc.category = %s
                    AND c.longitude >= %s
                    AND c.longitude <= %s
                    AND c.latitude >= %s
                    AND c.latitude <= %s
                LIMIT 5000; -- Add a reasonable limit to prevent overload
            """
            cursor.execute(query, (category, min_lon, max_lon, min_lat, max_lat))
            results = cursor.fetchall()
    except Exception as e:
        print(f"An error occurred in get_points_data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve points data.")
    finally:
        if conn is not None:
            conn.close()

    # Convert the database rows into a list of GeoJSON features
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"]],
            },
            "properties": {
                "unique_key": row["unique_key"],
                "complaint_type": row["complaint_type"],
            },
        }
        for row in results
        # Ensure that we only include points that have valid coordinates
        if row["longitude"] is not None and row["latitude"] is not None
    ]

    return {"type": "FeatureCollection", "features": features}
