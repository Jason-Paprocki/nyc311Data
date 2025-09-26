import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, ConfigDict

# --- Pydantic Models ---
# This defines the shape of the data our API will return.
# FastAPI uses this for validation and automatic documentation.
class Complaint(BaseModel):
    # This tells Pydantic it's okay to read data from non-dict objects (like database records)
    model_config = ConfigDict(from_attributes=True)

    unique_key: str
    complaint_type: str
    created_date: datetime

# --- FastAPI App Initialization ---
app = FastAPI(
    title="NYC 311 Data API",
    description="An API to query NYC 311 complaint data.",
    version="0.1.0",
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
        # This will help us debug connection issues from the API
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# --- API Endpoints ---
@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the NYC 311 Data API"}

@app.get("/api/v1/complaints/latest", response_model=list[Complaint])
def get_latest_complaints():
    """
    Retrieves the 10 most recent complaints from the database.
    This endpoint confirms the API can successfully connect to and query the DB.
    """
    conn = get_db_connection()
    # RealDictCursor makes the database return dictionaries instead of tuples
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT unique_key, complaint_type, created_date
            FROM complaints
            ORDER BY created_date DESC
            LIMIT 10;
            """
        )
        latest_complaints = cursor.fetchall()
    conn.close()
    return latest_complaints
