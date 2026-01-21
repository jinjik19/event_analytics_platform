CREATE TABLE IF NOT EXISTS project(
    project_id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL,
    api_key TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS api_key_idx ON project (api_key);
