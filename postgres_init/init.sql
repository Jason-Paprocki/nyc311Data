-- Enable the PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create the complaints table (RESTORED TO ORIGINAL STRUCTURE)
CREATE TABLE IF NOT EXISTS complaints (
    unique_key VARCHAR(50) PRIMARY KEY,
    created_date TIMESTAMP WITH TIME ZONE,
    closed_date TIMESTAMP WITH TIME ZONE,
    agency VARCHAR(50),
    complaint_type VARCHAR(255),
    descriptor TEXT,
    location GEOGRAPHY(Point, 4326),
    h3_index BIGINT
);

-- Create indexes for complaints table
CREATE INDEX IF NOT EXISTS complaints_location_idx ON complaints USING GIST (location);
CREATE INDEX IF NOT EXISTS complaints_created_date_idx ON complaints (created_date);
CREATE INDEX IF NOT EXISTS complaints_complaint_type_idx ON complaints (complaint_type);
CREATE INDEX IF NOT EXISTS complaints_h3_idx ON complaints (h3_index);


-- Create the community_districts table
CREATE TABLE IF NOT EXISTS community_districts (
    boro_cd VARCHAR(3) PRIMARY KEY,
    geometry GEOGRAPHY(MultiPolygon, 4326)
);

CREATE INDEX IF NOT EXISTS community_districts_geometry_idx ON community_districts USING GIST (geometry);

-- Create the community_district_stats table
CREATE TABLE IF NOT EXISTS community_district_stats (
    boro_cd VARCHAR(3),
    complaint_type VARCHAR(255),
    complaint_count INTEGER,
    density_per_sq_km DOUBLE PRECISION,
    PRIMARY KEY (boro_cd, complaint_type)
);

-- Create the NEW table for defining categories
CREATE TABLE IF NOT EXISTS complaint_categories (
    complaint_type VARCHAR(255) PRIMARY KEY,
    category VARCHAR(255) NOT NULL
);

CREATE INDEX IF NOT EXISTS complaint_categories_category_idx ON complaint_categories(category);
