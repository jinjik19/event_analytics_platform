-- CDC pipeline: Redpanda (Avro) -> cdc (Kafka engine + MV) -> raw (base tables)
--
-- Topics produced by Debezium:
--   event_analytics.public.project
--   event_analytics.public.event
--
-- Actual Avro types emitted by Debezium AvroConverter + ExtractNewRecordState:
--   ZonedTimestamp -> Avro string  (ISO-8601, e.g. "2026-02-18T04:55:47.207050Z")
--   __deleted      -> ["null","string"]  ("true"/"false", NOT boolean)
--   __op           -> ["null","string"]
--   __ts_ms        -> ["null","long"]
-- Project
DROP TABLE IF EXISTS cdc.mv_cdc_project;
DROP TABLE IF EXISTS cdc.kafka_cdc_project;
CREATE TABLE cdc.kafka_cdc_project (
    project_id String,
    name Nullable(String),
    plan Nullable(String),
    api_key Nullable(String),
    created_at String,
    -- ZonedTimestamp -> Avro string (ISO-8601)
    __op Nullable(String),
    __ts_ms Nullable(Int64),
    __deleted Nullable(String) -- "true" | "false" | null
) ENGINE = Kafka SETTINGS kafka_broker_list = 'redpanda:9092',
kafka_topic_list = 'event_analytics.public.project',
kafka_group_name = 'clickhouse_cdc_project_v2',
kafka_format = 'AvroConfluent',
kafka_num_consumers = 1,
kafka_skip_broken_messages = 0,
format_avro_schema_registry_url = 'http://redpanda:8081';
CREATE MATERIALIZED VIEW cdc.mv_cdc_project TO raw.project AS
SELECT toUUID(project_id) AS project_id,
    coalesce(name, '') AS name,
    coalesce(plan, '') AS plan,
    coalesce(api_key, '') AS api_key,
    toDateTime64(parseDateTime64BestEffort(created_at), 3, 'UTC') AS created_at,
    toUInt64(coalesce(__ts_ms, 0)) AS _version
FROM cdc.kafka_cdc_project
WHERE ifNull(__deleted, 'false') != 'true';
-- Event
DROP TABLE IF EXISTS cdc.mv_cdc_event;
DROP TABLE IF EXISTS cdc.kafka_cdc_event;
CREATE TABLE cdc.kafka_cdc_event (
    event_id String,
    project_id String,
    user_id Nullable(String),
    session_id Nullable(String),
    event_type Nullable(String),
    timestamp String,
    -- ZonedTimestamp -> Avro string (ISO-8601)
    properties Nullable(String),
    created_at String,
    -- ZonedTimestamp -> Avro string (ISO-8601)
    __op Nullable(String),
    __ts_ms Nullable(Int64),
    __deleted Nullable(String) -- "true" | "false" | null
) ENGINE = Kafka SETTINGS kafka_broker_list = 'redpanda:9092',
kafka_topic_list = 'event_analytics.public.event',
kafka_group_name = 'clickhouse_cdc_event_v2',
kafka_format = 'AvroConfluent',
kafka_num_consumers = 1,
kafka_skip_broken_messages = 0,
format_avro_schema_registry_url = 'http://redpanda:8081';
CREATE MATERIALIZED VIEW cdc.mv_cdc_event TO raw.event AS
SELECT toUUID(event_id) AS event_id,
    toUUID(project_id) AS project_id,
    coalesce(user_id, '') AS user_id,
    coalesce(session_id, '') AS session_id,
    coalesce(event_type, '') AS event_type,
    toDateTime64(parseDateTime64BestEffort(timestamp), 3, 'UTC') AS timestamp,
    coalesce(properties, '{}') AS properties,
    JSONExtractString(coalesce(properties, '{}'), 'country') AS country,
    JSONExtractString(coalesce(properties, '{}'), 'page_url') AS page_url,
    JSONExtractString(coalesce(properties, '{}'), 'currency') AS currency,
    JSONExtractString(coalesce(properties, '{}'), 'category') AS category,
    JSONExtractString(coalesce(properties, '{}'), 'product_id') AS product_id,
    JSONExtractString(coalesce(properties, '{}'), 'product_name') AS product_name,
    toDateTime64(parseDateTime64BestEffort(created_at), 3, 'UTC') AS created_at
FROM cdc.kafka_cdc_event
WHERE ifNull(__deleted, 'false') != 'true';
