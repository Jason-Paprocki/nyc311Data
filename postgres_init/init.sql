-- Enable the PostGIS extension to add support for geographic objects
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create the main table to store 311 service complaints
CREATE TABLE IF NOT EXISTS complaints (
    unique_key VARCHAR(50) PRIMARY KEY,
    created_date TIMESTAMP WITH TIME ZONE,
    closed_date TIMESTAMP WITH TIME ZONE,
    agency VARCHAR(50),
    complaint_type VARCHAR(255),
    descriptor TEXT,
    -- A single column to store the location as a geographic point.
    -- SRID 4326 is the standard for GPS coordinates (WGS 84).
    location GEOGRAPHY(Point, 4326)
);

-- Create a spatial index on the location column.
-- This is CRITICAL for fast location-based queries (e.g., "find all points within a radius").
-- The GIST index type is specifically designed for this kind of data.
CREATE INDEX IF NOT EXISTS complaints_location_idx ON complaints USING GIST (location);

-- Optional: Add indexes on other commonly queried columns
CREATE INDEX IF NOT EXISTS complaints_created_date_idx ON complaints (created_date);
CREATE INDEX IF NOT EXISTS complaints_complaint_type_idx ON complaints (complaint_type);
