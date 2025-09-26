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
    location GEOGRAPHY(Point, 4326)
);

-- Create a spatial index on the location column for fast location-based queries
CREATE INDEX IF NOT EXISTS complaints_location_idx ON complaints USING GIST (location);

-- Optional: Add indexes on other commonly queried columns
CREATE INDEX IF NOT EXISTS complaints_created_date_idx ON complaints (created_date);
CREATE INDEX IF NOT EXISTS complaints_complaint_type_idx ON complaints (complaint_type);


-- --- NEW SECTION ---
-- Create a table to store the NYC Community District boundaries

CREATE TABLE IF NOT EXISTS community_districts (
    -- boro_cd is a unique identifier for each district (e.g., '101' for Manhattan CD 1)
    boro_cd VARCHAR(3) PRIMARY KEY,
    -- A single column to store the district's shape as a geographic polygon.
    -- SRID 4326 is the standard for GPS coordinates (WGS 84).
    geometry GEOGRAPHY(MultiPolygon, 4326)
);

-- Create a spatial index on the geometry column.
-- This is CRITICAL for fast "point-in-polygon" queries (e.g., "find which district contains this complaint").
CREATE INDEX IF NOT EXISTS community_districts_geometry_idx ON community_districts USING GIST (geometry);
