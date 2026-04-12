SELECT 1
FROM {{ ref('mart_top_products') }}
WHERE purchase_count > 0
    AND revenue IS NULL
