import os
from fastapi import APIRouter, HTTPException, Query
from psycopg2.extras import RealDictCursor
import psycopg2
import h3
from typing import Dict, Any

# --- Router Initialization ---
router = APIRouter()

# --- Configuration ---
H3_RESOLUTION = 9  # Defines the precision of the hexagons


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
@router.get("/", response_model=Dict[str, Any])
def get_heatmap_data(
    category: str = Query(..., description="The complaint category to filter by."),
    bbox: str = Query(
        ..., description="Bounding box as min_lon,min_lat,max_lon,max_lat"
    ),
):
    """
    Generates a GeoJSON FeatureCollection of H3 hexagons with a calculated
    impact score for a given bounding box and complaint category.
    """
    try:
        # Parse the bounding box string into four float values
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid bbox format. Use min_lon,min_lat,max_lon,max_lat.",
        )

    # Create a GeoJSON-like dictionary for the h3 library
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

    # Get a set of all H3 hexagons within the bounding box
    hex_strings_in_view = h3.geo_to_cells(geojson_dict, H3_RESOLUTION)

    if not hex_strings_in_view:
        return {"type": "FeatureCollection", "features": []}

    # CORRECTED: Keep the hex indexes as a list of strings for the query
    hex_strings_for_query = list(hex_strings_in_view)

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # CORRECTED: The SQL query no longer casts the parameter to bigint[]
            query = """
                SELECT
                    c.h3_index,
                    COUNT(c.unique_key) as final_impact_score
                FROM complaints c
                JOIN complaint_categories cc ON c.complaint_type = cc.complaint_type
                WHERE c.h3_index = ANY(%s)
                  AND cc.category = %s
                GROUP BY c.h3_index;
            """
            # CORRECTED: Pass the list of strings to the query
            cursor.execute(query, (hex_strings_for_query, category))
            results = cursor.fetchall()
    except Exception as e:
        print(f"An error occurred in get_heatmap_data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve heatmap data.")
    finally:
        if conn is not None:
            conn.close()

    # CORRECTED: The h3_index from the database is now a string, so no conversion is needed
    scores_by_hex = {row["h3_index"]: row["final_impact_score"] for row in results}

    features = []
    # Loop through all hexagons in view to build the GeoJSON response
    for hex_str in hex_strings_in_view:
        # Get the geographic boundary of the hexagon
        boundary_lat_lon = h3.cell_to_boundary(hex_str)
        # Convert (lat, lon) to (lon, lat) for GeoJSON compliance
        geojson_boundary = [(lon, lat) for lat, lon in boundary_lat_lon]
        geojson_boundary.append(geojson_boundary[0])  # Close the polygon loop

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [geojson_boundary]},
                "properties": {
                    "h3_index": hex_str,
                    # Get the score, defaulting to 0 if no complaints were found
                    "final_impact_score": scores_by_hex.get(hex_str, 0),
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}
