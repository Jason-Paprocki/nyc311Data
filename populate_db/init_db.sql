-- This script will be executed automatically when the container is first created.

-- We use CREATE TABLE IF NOT EXISTS to make the script safe to re-run
-- in case of any issues, although Docker's init mechanism won't run it twice.
CREATE TABLE IF NOT EXISTS complaints (
    unique_key VARCHAR(50) PRIMARY KEY,
    created_date TIMESTAMP WITH TIME ZONE,
    closed_date TIMESTAMP WITH TIME ZONE,
    agency VARCHAR(100),
    complaint_type VARCHAR(255),
    descriptor TEXT,
    -- Increased precision and scale to handle high-resolution GPS data from the API
    latitude DECIMAL(18, 15),
    longitude DECIMAL(18, 15)
);

-- Optional: Add an index for faster geospatial queries later on
-- CREATE INDEX IF NOT EXISTS idx_complaints_location ON complaints (latitude, longitude);

-- Set the owner of the table to our application user
ALTER TABLE complaints OWNER TO postgres;

