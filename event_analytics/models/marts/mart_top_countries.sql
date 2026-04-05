{{
    config(
        order_by='(project_id, event_date)',
        engine='MergeTree()',
    )
}}

SELECT
    project_id,
    country,
    event_date,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(*) AS event_count,
    sumIf(
        price * quantity,
        event_type = 'purchase'
    ) AS revenue
FROM {{ ref('stg_events') }}
GROUP BY project_id, country, event_date
