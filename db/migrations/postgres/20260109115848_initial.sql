-- Create "project" table
CREATE TABLE "public"."project" (
  "project_id" uuid NOT NULL,
  "name" character varying(100) NOT NULL,
  "plan" character varying(10) NOT NULL,
  "api_key" character varying(50) NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY ("project_id"),
  CONSTRAINT "project_name_key" UNIQUE ("name")
);
-- Create index "api_key_idx" to table: "project"
CREATE INDEX "api_key_idx" ON "public"."project" ("api_key");
