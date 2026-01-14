-- Create "event" table
CREATE TABLE "event" (
  "event_id" uuid NOT NULL,
  "project_id" uuid NOT NULL,
  "user_id" uuid NULL,
  "session_id" uuid NULL,
  "event_type" character varying(100) NULL,
  "timestamp" timestamptz NOT NULL,
  "properties" jsonb NULL,
  "user_properties" jsonb NULL,
  "device" jsonb NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY ("event_id"),
  CONSTRAINT "event_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "project" ("project_id") ON UPDATE NO ACTION ON DELETE CASCADE
);
-- Create index "event_type_idx" to table: "event"
CREATE INDEX "event_type_idx" ON "event" ("event_type");
-- Create index "project_idx" to table: "event"
CREATE INDEX "project_idx" ON "event" ("project_id");
-- Create index "timestamp_idx" to table: "event"
CREATE INDEX "timestamp_idx" ON "event" ("timestamp");
