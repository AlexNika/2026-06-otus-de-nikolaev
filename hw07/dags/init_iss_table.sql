CREATE TABLE IF NOT EXISTS iss_position (
    id SERIAL PRIMARY KEY,
    data_interval_start TIMESTAMPTZ UNIQUE NOT NULL,
    timestamp BIGINT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);