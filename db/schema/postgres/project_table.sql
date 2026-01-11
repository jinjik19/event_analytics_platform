CREATE TABLE IF NOT EXISTS project(
    project_id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    plan VARCHAR(10) NOT NULL,
    api_key VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS api_key_idx ON project (api_key);
