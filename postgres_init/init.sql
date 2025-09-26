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

CREATE INDEX IF NOT EXISTS complaints_location_idx ON complaints USING GIST (location);
CREATE INDEX IF NOT EXISTS complaints_created_date_idx ON complaints (created_date);
CREATE INDEX IF NOT EXISTS complaints_complaint_type_idx ON complaints (complaint_type);

-- Create a table to store the NYC Community District boundaries
CREATE TABLE IF NOT EXISTS community_districts (
    boro_cd VARCHAR(3) PRIMARY KEY,
    geometry GEOGRAPHY(MultiPolygon, 4326)
);

CREATE INDEX IF NOT EXISTS community_districts_geometry_idx ON community_districts USING GIST (geometry);

-- --- NEW TABLE ---
-- This table will store the pre-calculated statistics for each district.
CREATE TABLE IF NOT EXISTS community_district_stats (
    boro_cd VARCHAR(3),
    complaint_type VARCHAR(255),
    complaint_count INTEGER,
    density_per_sq_km DOUBLE PRECISION,
    -- A composite primary key ensures each district/complaint_type pair is unique.
    PRIMARY KEY (boro_cd, complaint_type)
);
