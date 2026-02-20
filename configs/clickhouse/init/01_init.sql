CREATE DATABASE IF NOT EXISTS analytics;
CREATE TABLE IF NOT EXISTS analytics.project (
    project_id UUID,
    name String,
    plan String,
    api_key String,
    created_at DateTime64(3, 'UTC'),
    _version UInt64
) ENGINE = ReplacingMergeTree(_version)
ORDER BY (project_id);
CREATE TABLE IF NOT EXISTS analytics.event (
    event_id UUID,
    project_id UUID,
    user_id String,
    session_id String,
    event_type String,
    timestamp DateTime64(3, 'UTC'),
    properties String,
    created_at DateTime64(3, 'UTC')
) ENGINE = MergeTree() PARTITION BY toYYYYMM(timestamp)
ORDER BY (project_id, event_type, timestamp);
