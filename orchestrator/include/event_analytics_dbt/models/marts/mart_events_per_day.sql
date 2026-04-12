{{
    config(
        order_by='(project_id, event_date)',
        engine='MergeTree()',
    )
}}

SELECT
    project_id,
    event_date,
    COUNT(event_id) AS events
FROM {{ref('stg_events')}}
GROUP BY project_id, event_date
