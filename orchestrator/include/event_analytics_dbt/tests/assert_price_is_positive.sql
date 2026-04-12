SELECT event_id
FROM {{ ref('stg_events') }}
WHERE price IS NOT NULL
    AND price <= 0
