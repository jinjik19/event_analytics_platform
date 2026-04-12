{{
    config(
        order_by='(project_id, event_date, product_id)',
        engine='MergeTree()',
    )
}}

SELECT
    project_id,
    product_id,
    argMax(category, timestamp) AS category,
    argMax(product_name, timestamp) AS product_name,
    countIf(event_type = 'add_to_cart') AS add_to_cart_count,
    countIf(event_type = 'purchase') AS purchase_count,
    sumIf(
        price * quantity,
        event_type = 'purchase'
    ) AS revenue,
    event_date
FROM {{ ref('stg_events') }}
WHERE product_id != '' AND event_type IN ('add_to_cart', 'purchase')
GROUP BY project_id, product_id, event_date
