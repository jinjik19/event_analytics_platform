SELECT event_id
FROM {{ ref('stg_events') }}
WHERE event_date IS NOT NULL
    AND event_date > toDate(NOW())
