{{
    config(
        order_by='(project_id, event_date)',
        engine='AggregatingMergeTree()',
    )
}}

SELECT
    project_id,
    country,
    event_date,
    uniqState(user_id) AS unique_users_state,
    countState(*) AS event_count,
    sumIfState(
        price * quantity,
        event_type = 'purchase'
    ) AS revenue
FROM {{ ref('stg_events') }}
GROUP BY project_id, country, event_date
