CREATE TABLE IF NOT EXISTS event(
    event_id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    user_id UUID,
    session_id UUID,
    event_type VARCHAR(100),
    timestamp TIMESTAMPTZ NOT NULL,
    properties JSONB,
    user_properties JSONB,
    device JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (project_id) REFERENCES "public"."project"(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS project_idx ON event (project_id);
CREATE INDEX IF NOT EXISTS event_type_idx ON event (event_type);
CREATE INDEX IF NOT EXISTS timestamp_idx ON event (timestamp);
