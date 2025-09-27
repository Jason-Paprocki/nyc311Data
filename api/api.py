import os
from fastapi import FastAPI, HTTPException, Query
from psycopg2.extras import RealDictCursor
import psycopg2
import h3
from typing import List, Dict, Any

# --- Configuration ---
H3_RESOLUTION = 9

# --- FastAPI App Initialization ---
app = FastAPI(
    title="NYC 311 Data API",
    description="An API to query NYC 311 complaint data aggregated into H3 hexagons.",
    version="1.0.0",
)


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
        # This will be caught by FastAPI and returned as a 500 error
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")


# --- API Endpoints ---
@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the NYC 311 Data API"}


@app.get("/api/v1/categories", response_model=List[Dict[str, Any]])
def get_complaint_categories():
    """
    Retrieves a list of all complaint categories, pre-sorted for display.
    Filters out any null or empty complaint_type AND category values.
    """
    query = """
        SELECT
            category,
            array_agg(complaint_type ORDER BY complaint_type) as complaint_types
        FROM complaint_categories
        WHERE complaint_type IS NOT NULL AND complaint_type <> ''
          AND category IS NOT NULL AND category <> ''
        GROUP BY category
        ORDER BY MIN(sort_order), category;
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
    except Exception as e:
        print(f"Database query failed in get_complaint_categories: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
    finally:
        conn.close()

    return results if results is not None else []


@app.get("/api/v1/heatmap", response_model=Dict[str, Any])
def get_heatmap_data(
    category: str,
    bbox: str = Query(
        ..., description="Bounding box as min_lon,min_lat,max_lon,max_lat"
    ),
):
    """
    Generates a GeoJSON FeatureCollection of H3 hexagons with complaint counts
    for a given bounding box and complaint category.
    """
    try:
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid bbox format. Use min_lon,min_lat,max_lon,max_lat.",
        )

    geojson_dict = {
        "type": "Polygon",
        "coordinates": [
            [
                (min_lon, min_lat),
                (min_lon, max_lat),
                (max_lon, max_lat),
                (max_lon, min_lat),
                (min_lon, min_lat),
            ]
        ],
    }

    hex_strings_in_view = h3.geo_to_cells(geojson_dict, H3_RESOLUTION)

    if not hex_strings_in_view:
        return {"type": "FeatureCollection", "features": []}

    hex_ints_for_query = [h3.str_to_int(h) for h in hex_strings_in_view]

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT c.h3_index, COUNT(c.unique_key) as count
                FROM complaints c
                JOIN complaint_categories cc ON c.complaint_type = cc.complaint_type
                WHERE c.h3_index = ANY(%s)
                  AND cc.category = %s
                GROUP BY c.h3_index;
            """
            cursor.execute(query, (hex_ints_for_query, category))
            results = cursor.fetchall()
    except Exception as e:
        print(f"An error occurred in get_heatmap_data: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching heatmap data."
        )
    finally:
        if conn is not None:
            conn.close()

    counts_by_hex = {h3.int_to_str(row["h3_index"]): row["count"] for row in results}

    features = []
    for hex_index_str in hex_strings_in_view:
        # --- THE FIX ---
        # 1. Call cell_to_boundary with only ONE argument, as your documentation shows.
        # This returns coordinates as (lat, lon).
        boundary_lat_lon = h3.cell_to_boundary(hex_index_str)

        # 2. Manually swap the coordinates to (lon, lat) for GeoJSON compatibility.
        geojson_boundary = [(lon, lat) for lat, lon in boundary_lat_lon]
        # --- END FIX ---

        geojson_boundary.append(geojson_boundary[0])  # Close the loop

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [geojson_boundary]},
                "properties": {
                    "h3_index": hex_index_str,
                    "count": counts_by_hex.get(hex_index_str, 0),
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}
