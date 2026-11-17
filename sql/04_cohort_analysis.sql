
-- =====================================================
-- COHORT ANALYSIS
-- Analysis 01: Monthly Customer Retention
-- First delivered purchase defines the cohort.
-- =====================================================

WITH customer_first_purchase AS (
    SELECT
        c.customer_unique_id,

        MIN(o.order_purchase_timestamp)
            AS first_purchase_date

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    WHERE o.order_status = 'delivered'

    GROUP BY c.customer_unique_id
),

customer_cohorts AS (
    SELECT
        customer_unique_id,

        DATE_FORMAT(
            first_purchase_date,
            '%Y-%m-01'
        ) AS cohort_month

    FROM customer_first_purchase
),

monthly_activity AS (
    SELECT DISTINCT
        c.customer_unique_id,

        DATE_FORMAT(
            o.order_purchase_timestamp,
            '%Y-%m-01'
        ) AS activity_month

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    WHERE o.order_status = 'delivered'
),

cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size

    FROM customer_cohorts

    GROUP BY cohort_month
),

cohort_retention AS (
    SELECT
        cc.cohort_month,
        ma.activity_month,

        PERIOD_DIFF(
            EXTRACT(YEAR_MONTH FROM ma.activity_month),
            EXTRACT(YEAR_MONTH FROM cc.cohort_month)
        ) AS cohort_index,

        COUNT(DISTINCT cc.customer_unique_id)
            AS retained_customers

    FROM customer_cohorts cc

    INNER JOIN monthly_activity ma
        ON cc.customer_unique_id = ma.customer_unique_id

    WHERE ma.activity_month >= cc.cohort_month

    GROUP BY
        cc.cohort_month,
        ma.activity_month
)

SELECT
    cr.cohort_month,
    cr.activity_month,
    cr.cohort_index,

    cs.cohort_size,
    cr.retained_customers,

    ROUND(
        cr.retained_customers * 100.0 /
        cs.cohort_size,
        2
    ) AS retention_percentage

FROM cohort_retention cr

INNER JOIN cohort_sizes cs
    ON cr.cohort_month = cs.cohort_month

ORDER BY
    cr.cohort_month,
    cr.cohort_index;





-- =====================================================
-- Analysis 02: Complete Cohort Retention Matrix
-- Include zero-activity months.
-- Leave future unobserved months out of the result.
-- =====================================================

WITH RECURSIVE

customer_first_purchase AS (
    SELECT
        c.customer_unique_id,
        MIN(o.order_purchase_timestamp) AS first_purchase_date
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),

customer_cohorts AS (
    SELECT
        customer_unique_id,
        CAST(
            DATE_FORMAT(first_purchase_date, '%Y-%m-01')
            AS DATE
        ) AS cohort_month
    FROM customer_first_purchase
),

monthly_activity AS (
    SELECT DISTINCT
        c.customer_unique_id,
        CAST(
            DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01')
            AS DATE
        ) AS activity_month
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
),

cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
),

cohort_retention AS (
    SELECT
        cc.cohort_month,
        ma.activity_month,

        PERIOD_DIFF(
            EXTRACT(YEAR_MONTH FROM ma.activity_month),
            EXTRACT(YEAR_MONTH FROM cc.cohort_month)
        ) AS cohort_index,

        COUNT(DISTINCT cc.customer_unique_id)
            AS retained_customers

    FROM customer_cohorts cc

    INNER JOIN monthly_activity ma
        ON cc.customer_unique_id = ma.customer_unique_id

    WHERE ma.activity_month >= cc.cohort_month

    GROUP BY
        cc.cohort_month,
        ma.activity_month
),

last_activity AS (
    SELECT MAX(activity_month) AS max_activity_month
    FROM monthly_activity
),

max_index AS (
    SELECT
        MAX(
            PERIOD_DIFF(
                EXTRACT(YEAR_MONTH FROM la.max_activity_month),
                EXTRACT(YEAR_MONTH FROM cs.cohort_month)
            )
        ) AS max_cohort_index
    FROM cohort_sizes cs
    CROSS JOIN last_activity la
),

month_indices AS (
    SELECT 0 AS cohort_index

    UNION ALL

    SELECT mi.cohort_index + 1
    FROM month_indices mi
    CROSS JOIN max_index mx
    WHERE mi.cohort_index < mx.max_cohort_index
),

cohort_grid AS (
    SELECT
        cs.cohort_month,
        cs.cohort_size,
        mi.cohort_index,

        DATE_ADD(
            cs.cohort_month,
            INTERVAL mi.cohort_index MONTH
        ) AS activity_month

    FROM cohort_sizes cs

    CROSS JOIN month_indices mi
    CROSS JOIN last_activity la

    WHERE DATE_ADD(
        cs.cohort_month,
        INTERVAL mi.cohort_index MONTH
    ) <= la.max_activity_month
)

SELECT
    g.cohort_month,
    g.activity_month,
    g.cohort_index,
    g.cohort_size,

    COALESCE(
        cr.retained_customers, 0
    ) AS retained_customers,

    ROUND(
        COALESCE(cr.retained_customers, 0)
        * 100.0 / g.cohort_size,
        2
    ) AS retention_percentage

FROM cohort_grid g

LEFT JOIN cohort_retention cr
    ON g.cohort_month = cr.cohort_month
   AND g.cohort_index = cr.cohort_index

ORDER BY
    g.cohort_month,
    g.cohort_index;





-- =====================================================
-- Analysis 03: Month 1 Customer Retention
-- Exclude cohorts without a complete Month 1 period.
-- =====================================================

WITH customer_first_purchase AS (
    SELECT
        c.customer_unique_id,
        MIN(o.order_purchase_timestamp) AS first_purchase_date
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),

customer_cohorts AS (
    SELECT
        customer_unique_id,
        CAST(
            DATE_FORMAT(first_purchase_date, '%Y-%m-01')
            AS DATE
        ) AS cohort_month
    FROM customer_first_purchase
),

monthly_activity AS (
    SELECT DISTINCT
        c.customer_unique_id,
        CAST(
            DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01')
            AS DATE
        ) AS activity_month
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
),

last_activity AS (
    SELECT MAX(activity_month) AS max_activity_month
    FROM monthly_activity
)

SELECT
    cc.cohort_month,
    COUNT(*) AS cohort_size,
    COUNT(DISTINCT ma.customer_unique_id)
        AS month_1_retained_customers,

    ROUND(
        COUNT(DISTINCT ma.customer_unique_id) * 100.0
        / COUNT(*),
        2
    ) AS month_1_retention_percentage

FROM customer_cohorts cc

CROSS JOIN last_activity la

LEFT JOIN monthly_activity ma
    ON cc.customer_unique_id = ma.customer_unique_id
   AND ma.activity_month =
       DATE_ADD(cc.cohort_month, INTERVAL 1 MONTH)

WHERE DATE_ADD(
    cc.cohort_month,
    INTERVAL 1 MONTH
) <= la.max_activity_month

GROUP BY cc.cohort_month

ORDER BY cc.cohort_month;




-- =====================================================
-- Analysis 04: Retention Trend by Cohort Age
-- Weighted retention across eligible cohorts.
-- =====================================================

WITH RECURSIVE

customer_first_purchase AS (
    SELECT
        c.customer_unique_id,
        MIN(o.order_purchase_timestamp) AS first_purchase_date
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),

customer_cohorts AS (
    SELECT
        customer_unique_id,
        CAST(
            DATE_FORMAT(first_purchase_date, '%Y-%m-01')
            AS DATE
        ) AS cohort_month
    FROM customer_first_purchase
),

monthly_activity AS (
    SELECT DISTINCT
        c.customer_unique_id,
        CAST(
            DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01')
            AS DATE
        ) AS activity_month
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
),

cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
),

cohort_retention AS (
    SELECT
        cc.cohort_month,
        ma.activity_month,

        PERIOD_DIFF(
            EXTRACT(YEAR_MONTH FROM ma.activity_month),
            EXTRACT(YEAR_MONTH FROM cc.cohort_month)
        ) AS cohort_index,

        COUNT(DISTINCT cc.customer_unique_id)
            AS retained_customers

    FROM customer_cohorts cc
    INNER JOIN monthly_activity ma
        ON cc.customer_unique_id = ma.customer_unique_id

    WHERE ma.activity_month >= cc.cohort_month

    GROUP BY
        cc.cohort_month,
        ma.activity_month
),

last_activity AS (
    SELECT MAX(activity_month) AS max_activity_month
    FROM monthly_activity
),

max_index AS (
    SELECT
        MAX(
            PERIOD_DIFF(
                EXTRACT(YEAR_MONTH FROM la.max_activity_month),
                EXTRACT(YEAR_MONTH FROM cs.cohort_month)
            )
        ) AS max_cohort_index
    FROM cohort_sizes cs
    CROSS JOIN last_activity la
),

month_indices AS (
    SELECT 0 AS cohort_index

    UNION ALL

    SELECT cohort_index + 1
    FROM month_indices
    CROSS JOIN max_index
    WHERE cohort_index < max_cohort_index
),

cohort_grid AS (
    SELECT
        cs.cohort_month,
        cs.cohort_size,
        mi.cohort_index,

        DATE_ADD(
            cs.cohort_month,
            INTERVAL mi.cohort_index MONTH
        ) AS activity_month

    FROM cohort_sizes cs
    CROSS JOIN month_indices mi
    CROSS JOIN last_activity la

    WHERE DATE_ADD(
        cs.cohort_month,
        INTERVAL mi.cohort_index MONTH
    ) <= la.max_activity_month
)

SELECT
    g.cohort_index,

    COUNT(*) AS eligible_cohorts,

    SUM(g.cohort_size) AS eligible_customers,

    SUM(
        COALESCE(cr.retained_customers, 0)
    ) AS retained_customers,

    ROUND(
        SUM(COALESCE(cr.retained_customers, 0))
        * 100.0 / SUM(g.cohort_size),
        2
    ) AS weighted_retention_percentage

FROM cohort_grid g

LEFT JOIN cohort_retention cr
    ON g.cohort_month = cr.cohort_month
   AND g.cohort_index = cr.cohort_index

GROUP BY g.cohort_index
ORDER BY g.cohort_index;





-- =====================================================
-- Analysis 05: Create Cohort Retention View
-- Complete long-format dataset for Power BI.
-- =====================================================

CREATE OR REPLACE VIEW vw_cohort_retention AS

WITH RECURSIVE

customer_first_purchase AS (
    SELECT
        c.customer_unique_id,
        MIN(o.order_purchase_timestamp) AS first_purchase_date
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),

customer_cohorts AS (
    SELECT
        customer_unique_id,
        CAST(
            DATE_FORMAT(first_purchase_date, '%Y-%m-01')
            AS DATE
        ) AS cohort_month
    FROM customer_first_purchase
),

monthly_activity AS (
    SELECT DISTINCT
        c.customer_unique_id,
        CAST(
            DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01')
            AS DATE
        ) AS activity_month
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
),

cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
),

last_activity AS (
    SELECT MAX(activity_month) AS max_activity_month
    FROM monthly_activity
),

max_index AS (
    SELECT
        MAX(
            PERIOD_DIFF(
                EXTRACT(YEAR_MONTH FROM la.max_activity_month),
                EXTRACT(YEAR_MONTH FROM cs.cohort_month)
            )
        ) AS max_cohort_index
    FROM cohort_sizes cs
    CROSS JOIN last_activity la
),

month_indices AS (
    SELECT 0 AS cohort_index

    UNION ALL

    SELECT mi.cohort_index + 1
    FROM month_indices mi
    CROSS JOIN max_index mx
    WHERE mi.cohort_index < mx.max_cohort_index
),

cohort_grid AS (
    SELECT
        cs.cohort_month,
        cs.cohort_size,
        mi.cohort_index,

        DATE_ADD(
            cs.cohort_month,
            INTERVAL mi.cohort_index MONTH
        ) AS activity_month

    FROM cohort_sizes cs
    CROSS JOIN month_indices mi
    CROSS JOIN last_activity la

    WHERE DATE_ADD(
        cs.cohort_month,
        INTERVAL mi.cohort_index MONTH
    ) <= la.max_activity_month
),

cohort_retention AS (
    SELECT
        cc.cohort_month,

        PERIOD_DIFF(
            EXTRACT(YEAR_MONTH FROM ma.activity_month),
            EXTRACT(YEAR_MONTH FROM cc.cohort_month)
        ) AS cohort_index,

        COUNT(DISTINCT cc.customer_unique_id)
            AS retained_customers

    FROM customer_cohorts cc
    INNER JOIN monthly_activity ma
        ON cc.customer_unique_id = ma.customer_unique_id
       AND ma.activity_month >= cc.cohort_month

    GROUP BY
        cc.cohort_month,
        ma.activity_month
)

SELECT
    g.cohort_month,
    g.activity_month,
    g.cohort_index,
    g.cohort_size,

    COALESCE(
        cr.retained_customers,
        0
    ) AS retained_customers,

    ROUND(
        COALESCE(cr.retained_customers, 0)
        * 100.0 / g.cohort_size,
        2
    ) AS retention_percentage

FROM cohort_grid g

LEFT JOIN cohort_retention cr
    ON g.cohort_month = cr.cohort_month
   AND g.cohort_index = cr.cohort_index;
