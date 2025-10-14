CREATE TABLE IF NOT EXISTS tags_series (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    tags JSONB
);
CREATE INDEX IF NOT EXISTS idx_tags_device_time ON tags_series(device_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS top_tracks (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    tag TEXT,
    detections INTEGER,
    length DOUBLE PRECISION,
    track_confidence_average DOUBLE PRECISION,
    thumbnail_url TEXT,
    zones JSONB
);
CREATE INDEX IF NOT EXISTS idx_tracks_device_time ON tags_series(device_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS zones (
    device_id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT now(),
    zones JSONB
);
CREATE INDEX IF NOT EXISTS idx_tracks_zones_time ON tags_series(device_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    event_producer_id TEXT NOT NULL,
    type TEXT NOT NULL,
    sub_type TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    draft BOOLEAN NOT NULL,
    priority TEXT NOT NULL,
    metadata JSONB
);

CREATE TABLE detection_events (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    timestamp           TIMESTAMPTZ NOT NULL,
    source_id           TEXT        NOT NULL,
    source_name         TEXT        NOT NULL,
    tag                 TEXT,
    event_count         SMALLINT    DEFAULT 1
);
CREATE EXTENSION IF NOT EXISTS timescaledb;
SELECT create_hypertable('detection_events', 'timestamp');
CREATE INDEX idx_source_id_time ON detection_events (source_id, timestamp DESC);
SELECT add_retention_policy('detection_events', INTERVAL '1 days');