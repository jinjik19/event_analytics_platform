-- Modify "event" table
ALTER TABLE "event"
ALTER COLUMN "user_id" TYPE text,
    ALTER COLUMN "session_id" TYPE text,
    ALTER COLUMN "event_type" TYPE text;
UPDATE "event"
SET properties = properties || COALESCE(user_properties, '{}'::jsonb) || COALESCE(device, '{}'::jsonb);
ALTER TABLE "event" DROP COLUMN "user_properties",
    DROP COLUMN "device";
-- Modify "project" table
ALTER TABLE "project"
ALTER COLUMN "name" TYPE text,
    ALTER COLUMN "plan" TYPE text,
    ALTER COLUMN "api_key" TYPE text;
