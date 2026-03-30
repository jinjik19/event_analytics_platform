SELECT event_id,
    project_id,
    user_id,
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
    toInt32OrNull(JSONExtractString(properties, 'quantity')) AS quantity
FROM raw."event"
