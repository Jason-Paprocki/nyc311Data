-- init.sql

-- Enable PostGIS extension, which is required for location/geometry functions.
CREATE EXTENSION IF NOT EXISTS postgis;

-- Stores raw 311 complaint data.
CREATE TABLE IF NOT EXISTS complaints (
    unique_key TEXT PRIMARY KEY,
    created_date TIMESTAMP,
    closed_date TIMESTAMP,
    agency TEXT,
    complaint_type TEXT,
    descriptor TEXT,
    location GEOMETRY(Point, 4326),
    h3_index TEXT
);

-- Stores business license data.
CREATE TABLE IF NOT EXISTS businesses (
    license_nbr TEXT PRIMARY KEY,
    location GEOMETRY(Point, 4326),
    h3_index TEXT
);

-- Master table for H3 hexagons, containing aggregated and static data.
CREATE TABLE IF NOT EXISTS h3_hex_data (
    h3_index TEXT PRIMARY KEY,
    population INTEGER DEFAULT 0,
    business_count INTEGER DEFAULT 0,
    geometry GEOMETRY(Polygon, 4326)
);

-- Stores the daily calculated scores for the heatmap.
CREATE TABLE IF NOT EXISTS h3_daily_stats (
    h3_index TEXT,
    stats_date DATE,
    complaint_count INTEGER,
    base_impact_score DOUBLE PRECISION,
    activity_score DOUBLE PRECISION,
    final_impact_score DOUBLE PRECISION,
    PRIMARY KEY (h3_index, stats_date)
);

-- Maps raw complaint types to broader categories for filtering.
CREATE TABLE IF NOT EXISTS complaint_categories (
    complaint_type TEXT PRIMARY KEY,
    category TEXT,
    sort_order INTEGER
);

-- Create indexes to speed up common queries.
CREATE INDEX IF NOT EXISTS idx_complaints_created_date ON complaints (created_date);
CREATE INDEX IF NOT EXISTS idx_complaints_h3_index ON complaints (h3_index);
CREATE INDEX IF NOT EXISTS idx_businesses_h3_index ON businesses (h3_index);
