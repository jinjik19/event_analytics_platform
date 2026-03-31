SELECT
    event_id,
    project_id,
    user_id,
    session_id,
    event_type,
    event_date,
    "timestamp",
    category,
    country,
    page_url,
    currency,
    product_id,
    product_name,
    price,
    quantity,
    created_at
FROM (
    SELECT event_id,
        project_id,
        user_id,
        session_id,
        event_type,
        toDate("timestamp") AS event_date,
        "timestamp",
        category,
        CASE
            WHEN country = '' THEN 'Unknown'
            ELSE country
        END AS country,
        page_url,
        currency,
        product_id,
        product_name,
        toFloat64OrNull(JSONExtractString(properties, 'price')) AS price,
        toInt32OrNull(JSONExtractString(properties, 'quantity')) AS quantity,
        created_at,
        ROW_NUMBER() OVER(PARTITION BY event_id ORDER BY created_at DESC) AS rn
    FROM {{ source('raw', 'event') }}
)
WHERE rn = 1
