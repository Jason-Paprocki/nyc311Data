-- Enable PostGIS and H3 extensions for geospatial operations
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS h3_postgis;

--------------------------------------------------------------------------------
-- RAW DATA TABLES
-- These tables store the raw, unmodified data ingested from external APIs.
--------------------------------------------------------------------------------

-- Stores raw 311 complaint data, fetched incrementally.
CREATE TABLE IF NOT EXISTS complaints (
    unique_key VARCHAR(50) PRIMARY KEY,
    created_date TIMESTAMP WITH TIME ZONE,
    agency VARCHAR(50),
    complaint_type VARCHAR(255),
    location GEOGRAPHY(Point, 4326),
    h3_index BIGINT -- H3 index calculated on ingestion
);
CREATE INDEX IF NOT EXISTS complaints_created_date_idx ON complaints (created_date);
CREATE INDEX IF NOT EXISTS complaints_h3_idx ON complaints (h3_index);

-- NEW: Stores raw data for active, physical businesses.
CREATE TABLE IF NOT EXISTS businesses (
    license_nbr VARCHAR(50) PRIMARY KEY,
    location GEOGRAPHY(Point, 4326),
    h3_index BIGINT -- H3 index calculated on ingestion
);
CREATE INDEX IF NOT EXISTS businesses_location_idx ON businesses USING GIST (location);
CREATE INDEX IF NOT EXISTS businesses_h3_idx ON businesses (h3_index);


--------------------------------------------------------------------------------
-- DIMENSIONAL & AGGREGATE TABLES
-- These tables store processed, aggregated, and enriched data.
--------------------------------------------------------------------------------

-- UPGRADED: The central dimension table for hexagons.
-- This table describes the "static" properties of each geographic area.
CREATE TABLE IF NOT EXISTS h3_hex_data (
    h3_index BIGINT PRIMARY KEY,
    geometry GEOGRAPHY(Polygon, 4326) NOT NULL,
    -- Populated from Census data (e.g., from a shapefile)
    population INTEGER NOT NULL DEFAULT 0,
    -- NEW: Aggregated count from the `businesses` table
    business_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS h3_hex_data_geometry_idx ON h3_hex_data USING GIST (geometry);

-- UPGRADED: Stores the results of our daily calculations.
-- The final score is now broken into its components for better analysis.
CREATE TABLE IF NOT EXISTS h3_daily_stats (
    h3_index BIGINT NOT NULL,
    stats_date DATE NOT NULL,
    complaint_count INTEGER NOT NULL,
    -- Score based on residential population
    base_impact_score DOUBLE PRECISION,
    -- Score based on commercial activity
    activity_score DOUBLE PRECISION,
    -- The final, combined score for the heatmap
    final_impact_score DOUBLE PRECISION,
    PRIMARY KEY (h3_index, stats_date)
);

-- Maps specific complaint types to broader categories for filtering in the UI.
CREATE TABLE IF NOT EXISTS complaint_categories (
    complaint_type VARCHAR(255) PRIMARY KEY,
    category VARCHAR(255) NOT NULL,
    sort_order INTEGER DEFAULT 99
);
CREATE INDEX IF NOT EXISTS complaint_categories_category_idx ON complaint_categories(category);
