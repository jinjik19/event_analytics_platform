SELECT event_id
FROM {{ ref('stg_events') }}
WHERE event_type = 'purchase'
    AND (price IS NULL OR quantity IS NULL)
