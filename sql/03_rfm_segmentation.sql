
-- =====================================================
-- RFM SEGMENTATION
-- Analysis 01: Calculate Raw RFM Metrics
-- =====================================================

WITH rfm_snapshot AS (
    SELECT
        DATE_ADD(
            DATE(MAX(order_purchase_timestamp)),
            INTERVAL 1 DAY
        ) AS snapshot_date
    FROM orders
    WHERE order_status = 'delivered'
),

order_payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS order_payment
    FROM payments
    GROUP BY order_id
),

customer_rfm AS (
    SELECT
        c.customer_unique_id,

        DATEDIFF(
            s.snapshot_date,
            DATE(MAX(o.order_purchase_timestamp))
        ) AS recency,

        COUNT(DISTINCT o.order_id) AS frequency,

        SUM(
            COALESCE(p.order_payment, 0)
        ) AS monetary

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    CROSS JOIN rfm_snapshot s

    LEFT JOIN order_payment_totals p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY
        c.customer_unique_id,
        s.snapshot_date
)

SELECT
    customer_unique_id,
    recency,
    frequency,
    ROUND(monetary, 2) AS monetary

FROM customer_rfm

ORDER BY recency ASC

LIMIT 20;




-- =====================================================
-- Analysis 02: RFM Distribution Summary
-- =====================================================

WITH rfm_snapshot AS (
    SELECT
        DATE_ADD(
            DATE(MAX(order_purchase_timestamp)),
            INTERVAL 1 DAY
        ) AS snapshot_date
    FROM orders
    WHERE order_status = 'delivered'
),

order_payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS order_payment
    FROM payments
    GROUP BY order_id
),

customer_rfm AS (
    SELECT
        c.customer_unique_id,

        DATEDIFF(
            s.snapshot_date,
            DATE(MAX(o.order_purchase_timestamp))
        ) AS recency,

        COUNT(DISTINCT o.order_id) AS frequency,

        SUM(
            COALESCE(p.order_payment, 0)
        ) AS monetary

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    CROSS JOIN rfm_snapshot s

    LEFT JOIN order_payment_totals p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY
        c.customer_unique_id,
        s.snapshot_date
)

SELECT
    COUNT(*) AS total_customers,

    MIN(recency) AS min_recency,
    MAX(recency) AS max_recency,
    ROUND(AVG(recency), 2) AS avg_recency,

    MIN(frequency) AS min_frequency,
    MAX(frequency) AS max_frequency,
    ROUND(AVG(frequency), 2) AS avg_frequency,

    ROUND(MIN(monetary), 2) AS min_monetary,
    ROUND(MAX(monetary), 2) AS max_monetary,
    ROUND(AVG(monetary), 2) AS avg_monetary,

    SUM(monetary = 0) AS customers_with_zero_payment

FROM customer_rfm;




-- =====================================================
-- Analysis 03: Calculate RFM Scores
-- Recency: Recent customers receive higher scores.
-- Frequency: Business-defined frequency thresholds.
-- Monetary: Higher spending receives higher scores.
-- =====================================================

WITH rfm_snapshot AS (
    SELECT
        DATE_ADD(
            DATE(MAX(order_purchase_timestamp)),
            INTERVAL 1 DAY
        ) AS snapshot_date
    FROM orders
    WHERE order_status = 'delivered'
),

order_payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS order_payment
    FROM payments
    GROUP BY order_id
),

customer_rfm AS (
    SELECT
        c.customer_unique_id,

        DATEDIFF(
            s.snapshot_date,
            DATE(MAX(o.order_purchase_timestamp))
        ) AS recency,

        COUNT(DISTINCT o.order_id) AS frequency,

        SUM(
            COALESCE(p.order_payment, 0)
        ) AS monetary

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    CROSS JOIN rfm_snapshot s

    LEFT JOIN order_payment_totals p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY
        c.customer_unique_id,
        s.snapshot_date
),

rfm_percentiles AS (
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,

        PERCENT_RANK() OVER (
            ORDER BY recency DESC
        ) AS recency_percentile,

        PERCENT_RANK() OVER (
            ORDER BY monetary ASC
        ) AS monetary_percentile

    FROM customer_rfm
),

rfm_scores AS (
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,

        LEAST(
            5,
            FLOOR(recency_percentile * 5) + 1
        ) AS r_score,

        CASE
            WHEN frequency = 1 THEN 1
            WHEN frequency = 2 THEN 2
            WHEN frequency = 3 THEN 3
            WHEN frequency <= 5 THEN 4
            ELSE 5
        END AS f_score,

        LEAST(
            5,
            FLOOR(monetary_percentile * 5) + 1
        ) AS m_score

    FROM rfm_percentiles
)

SELECT
    'Recency' AS metric,
    r_score AS score,
    COUNT(*) AS customer_count
FROM rfm_scores
GROUP BY r_score

UNION ALL

SELECT
    'Frequency',
    f_score,
    COUNT(*)
FROM rfm_scores
GROUP BY f_score

UNION ALL

SELECT
    'Monetary',
    m_score,
    COUNT(*)
FROM rfm_scores
GROUP BY m_score

ORDER BY metric, score;




-- =====================================================
-- Analysis 04: RFM Customer Segmentation
-- =====================================================

WITH rfm_snapshot AS (
    SELECT
        DATE_ADD(
            DATE(MAX(order_purchase_timestamp)),
            INTERVAL 1 DAY
        ) AS snapshot_date
    FROM orders
    WHERE order_status = 'delivered'
),

order_payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS order_payment
    FROM payments
    GROUP BY order_id
),

customer_rfm AS (
    SELECT
        c.customer_unique_id,

        DATEDIFF(
            s.snapshot_date,
            DATE(MAX(o.order_purchase_timestamp))
        ) AS recency,

        COUNT(DISTINCT o.order_id) AS frequency,

        SUM(COALESCE(p.order_payment, 0)) AS monetary

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    CROSS JOIN rfm_snapshot s

    LEFT JOIN order_payment_totals p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY
        c.customer_unique_id,
        s.snapshot_date
),

rfm_percentiles AS (
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,

        PERCENT_RANK() OVER (
            ORDER BY recency DESC
        ) AS recency_percentile,

        PERCENT_RANK() OVER (
            ORDER BY monetary ASC
        ) AS monetary_percentile

    FROM customer_rfm
),

rfm_scores AS (
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,

        LEAST(
            5,
            FLOOR(recency_percentile * 5) + 1
        ) AS r_score,

        CASE
            WHEN frequency = 1 THEN 1
            WHEN frequency = 2 THEN 2
            WHEN frequency = 3 THEN 3
            WHEN frequency <= 5 THEN 4
            ELSE 5
        END AS f_score,

        LEAST(
            5,
            FLOOR(monetary_percentile * 5) + 1
        ) AS m_score

    FROM rfm_percentiles
),

segmented_customers AS (
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,
        r_score,
        f_score,
        m_score,

        CONCAT(r_score, f_score, m_score) AS rfm_code,

        CASE
            WHEN r_score >= 4
                 AND f_score >= 4
                 AND m_score >= 4
                THEN 'Champions'

            WHEN r_score >= 3
                 AND f_score >= 3
                THEN 'Loyal Customers'

            WHEN r_score >= 4
                 AND f_score = 2
                THEN 'Potential Loyalists'

            WHEN r_score >= 4
                 AND f_score = 1
                THEN 'Recent One-time Customers'

            WHEN r_score <= 2
                 AND f_score >= 2
                THEN 'At Risk'

            WHEN r_score <= 2
                 AND f_score = 1
                 AND m_score >= 3
                THEN 'At Risk - High Monetary'

            WHEN r_score <= 2
                 AND f_score = 1
                 AND m_score <= 2
                THEN 'Hibernating'

            ELSE 'Needs Attention'
        END AS customer_segment

    FROM rfm_scores
)

SELECT
    customer_segment,
    COUNT(*) AS customer_count,

    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS customer_percentage,

    ROUND(AVG(recency), 2) AS average_recency,

    ROUND(AVG(frequency), 2) AS average_frequency,

    ROUND(AVG(monetary), 2) AS average_monetary

FROM segmented_customers

GROUP BY customer_segment
ORDER BY customer_count DESC;




-- =====================================================
-- Analysis 05: Create Reusable Customer RFM View
-- =====================================================

CREATE OR REPLACE VIEW vw_customer_rfm AS

WITH rfm_snapshot AS (
    SELECT
        DATE_ADD(
            DATE(MAX(order_purchase_timestamp)),
            INTERVAL 1 DAY
        ) AS snapshot_date
    FROM orders
    WHERE order_status = 'delivered'
),

order_payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS order_payment
    FROM payments
    GROUP BY order_id
),

customer_rfm AS (
    SELECT
        c.customer_unique_id,

        DATEDIFF(
            s.snapshot_date,
            DATE(MAX(o.order_purchase_timestamp))
        ) AS recency,

        COUNT(DISTINCT o.order_id) AS frequency,

        SUM(COALESCE(p.order_payment, 0)) AS monetary

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    CROSS JOIN rfm_snapshot s

    LEFT JOIN order_payment_totals p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY
        c.customer_unique_id,
        s.snapshot_date
),

rfm_percentiles AS (
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,

        PERCENT_RANK() OVER (
            ORDER BY recency DESC
        ) AS recency_percentile,

        PERCENT_RANK() OVER (
            ORDER BY monetary ASC
        ) AS monetary_percentile

    FROM customer_rfm
),

rfm_scores AS (
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,

        LEAST(
            5,
            FLOOR(recency_percentile * 5) + 1
        ) AS r_score,

        CASE
            WHEN frequency = 1 THEN 1
            WHEN frequency = 2 THEN 2
            WHEN frequency = 3 THEN 3
            WHEN frequency <= 5 THEN 4
            ELSE 5
        END AS f_score,

        LEAST(
            5,
            FLOOR(monetary_percentile * 5) + 1
        ) AS m_score

    FROM rfm_percentiles
)

SELECT
    customer_unique_id,
    recency,
    frequency,
    ROUND(monetary, 2) AS monetary,

    r_score,
    f_score,
    m_score,

    CONCAT(r_score, f_score, m_score) AS rfm_code,

    CASE
        WHEN r_score >= 4
             AND f_score >= 4
             AND m_score >= 4
            THEN 'Champions'

        WHEN r_score >= 3
             AND f_score >= 3
            THEN 'Loyal Customers'

        WHEN r_score >= 4
             AND f_score = 2
            THEN 'Potential Loyalists'

        WHEN r_score >= 4
             AND f_score = 1
            THEN 'Recent One-time Customers'

        WHEN r_score <= 2
             AND f_score >= 2
            THEN 'At Risk'

        WHEN r_score <= 2
             AND f_score = 1
             AND m_score >= 3
            THEN 'High-Value One-time Lapsed'

        WHEN r_score <= 2
             AND f_score = 1
             AND m_score <= 2
            THEN 'Hibernating'

        ELSE 'Needs Attention'
    END AS customer_segment

FROM rfm_scores;




-- =====================================================
-- Analysis 06: Monetary Contribution by RFM Segment
-- =====================================================

SELECT
    customer_segment,

    COUNT(*) AS customer_count,

    ROUND(SUM(monetary), 2) AS total_monetary,

    ROUND(
        SUM(monetary) * 100.0 /
        SUM(SUM(monetary)) OVER (),
        2
    ) AS monetary_contribution_percentage,

    ROUND(AVG(monetary), 2) AS average_monetary,

    ROUND(AVG(recency), 2) AS average_recency,

    ROUND(AVG(frequency), 2) AS average_frequency

FROM vw_customer_rfm

GROUP BY customer_segment

ORDER BY total_monetary DESC;




-- =====================================================
-- Analysis 07: High-Value One-time Lapsed Customers
-- =====================================================

SELECT
    customer_unique_id,
    recency,
    frequency,
    monetary,
    rfm_code,
    customer_segment
FROM vw_customer_rfm
WHERE customer_segment = 'High-Value One-time Lapsed'
ORDER BY monetary DESC, recency ASC
LIMIT 20;

