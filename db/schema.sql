CREATE TABLE IF NOT EXISTS tags_series (
    id TEXT PRIMARY KEY,
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
    zones TEXT[],
);
CREATE INDEX IF NOT EXISTS idx_tracks_device_time ON tags_series(device_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS zones (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    zones JSONB
);
CREATE INDEX IF NOT EXISTS idx_tracks_zones_time ON tags_series(device_id, timestamp DESC);

/*
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    tag TEXT,
    detection JSONB
);
*/