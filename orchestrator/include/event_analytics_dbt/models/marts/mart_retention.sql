{{
    config(
        order_by='(project_id, cohort_date, day_number)',
        engine='MergeTree()',
    )
}}

WItH cohorts AS (
    SELECT
        project_id,
        user_id,
        MIN(event_date) AS cohort_date
    FROM {{ ref('stg_events') }}
    GROUP BY project_id, user_id
), activity AS (
    SELECT
        c.project_id AS project_id,
        c.cohort_date,
        e.user_id,
        dateDiff('day', c.cohort_date, e.event_date) AS day_number
    FROM {{ ref('stg_events') }} e
    INNER JOIN cohorts c
    ON c.project_id = e.project_id AND c.user_id = e.user_id
), cohort_size AS (
    SELECT
        project_id,
        cohort_date,
        COUNT(DISTINCT user_id) AS cohort_size
    FROM cohorts
    GROUP BY project_id, cohort_date
), retention AS (
    SELECT
        project_id,
        cohort_date,
        day_number,
        COUNT(DISTINCT user_id) AS retained_users
    FROM activity
    WHERE day_number >= 0
    GROUP BY project_id, cohort_date, day_number
)
SELECT
    r.project_id,
    r.cohort_date,
    r.day_number,
    r.retained_users,
    cs.cohort_size,
    ROUND(r.retained_users / cs.cohort_size * 100, 1) AS retention_pct
FROM "retention" r
INNER JOIN cohort_size cs
ON cs.project_id = r.project_id AND cs.cohort_date = r.cohort_date
