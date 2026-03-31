SELECT event_id
FROM {{ ref('stg_events') }}
WHERE quantity IS NOT NULL
    AND quantity <= 0
