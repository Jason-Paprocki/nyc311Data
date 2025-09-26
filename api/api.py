import os
from fastapi import FastAPI, HTTPException, Query
from psycopg2.extras import RealDictCursor
import psycopg2
import h3
from typing import List

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
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# --- API Endpoints ---
@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the NYC 311 Data API"}

@app.get("/api/v1/heatmap")
def get_heatmap_data(
    complaint_type: str,
    bbox: str = Query(..., description="Bounding box as min_lon,min_lat,max_lon,max_lat")
):
    """
    Generates a GeoJSON FeatureCollection of H3 hexagons with complaint counts
    for a given bounding box and complaint type.
    """
    try:
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(','))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bbox format. Use min_lon,min_lat,max_lon,max_lat.")

    # --- REVISED SECTION START ---

    # 1. Create a valid GeoJSON Polygon dictionary.
    #    The coordinates must be in [lon, lat] order and the polygon must be "closed"
    #    (the first and last coordinates are the same).
    geojson_polygon = {
        'type': 'Polygon',
        'coordinates': [[
            [min_lon, min_lat],
            [min_lon, max_lat],
            [max_lon, max_lat],
            [max_lon, min_lat],
            [min_lon, min_lat]  # Closing the loop
        ]]
    }

    # 2. Use h3.polyfill to find all hexagons within the GeoJSON polygon.
    #    We use list() to convert the resulting set to a list for the database query.
    hexagons_in_view = list(h3.polyfill(geojson_polygon, H3_RESOLUTION))

    # --- REVISED SECTION END ---

    if not hexagons_in_view:
        return {"type": "FeatureCollection", "features": []}

    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        query = """
            SELECT h3_index, COUNT(unique_key) as count
            FROM complaints
            WHERE complaint_type = %s AND h3_index = ANY(%s)
            GROUP BY h3_index;
        """
        cursor.execute(query, (complaint_type, hexagons_in_view))
        results = cursor.fetchall()
    conn.close()

    counts_by_hex = {row['h3_index']: row['count'] for row in results}

    features = []
    for hex_index in hexagons_in_view:
        boundary = h3.cell_to_boundary(hex_index, geo_json=False)
        geojson_boundary = [[lon, lat] for lat, lon in boundary]
        geojson_boundary.append(geojson_boundary[0])

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [geojson_boundary]
            },
            "properties": {
                "h3_index": hex_index,
                "count": counts_by_hex.get(hex_index, 0)
            }
        })

    return {"type": "FeatureCollection", "features": features}
