
-- =====================================================
-- CUSTOMER ANALYSIS
-- Analysis 01: Customer Purchase Frequency
-- Only delivered orders are considered.
-- Customer identity: customer_unique_id
-- =====================================================

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)

SELECT
    COUNT(*) AS total_unique_customers,

    SUM(total_orders = 1) AS one_time_customers,

    SUM(total_orders > 1) AS repeat_customers,

    ROUND(
        SUM(total_orders > 1) * 100.0 / COUNT(*),
        2
    ) AS repeat_customer_percentage,

    ROUND(
        AVG(total_orders),
        2
    ) AS average_orders_per_customer

FROM customer_orders;




-- =====================================================
-- Analysis 02: Customer Order Frequency Distribution
-- =====================================================

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)

SELECT
    total_orders,
    COUNT(*) AS number_of_customers,

    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS customer_percentage

FROM customer_orders

GROUP BY total_orders
ORDER BY total_orders;




-- =====================================================
-- Analysis 03: Customer Spending by Purchase Frequency
-- Only delivered orders are included.
-- =====================================================

WITH order_payments AS (
    SELECT
        order_id,
        SUM(payment_value) AS order_payment_value
    FROM payments
    GROUP BY order_id
),

customer_metrics AS (
    SELECT
        c.customer_unique_id,

        COUNT(DISTINCT o.order_id) AS delivered_orders,

        COUNT(DISTINCT
            CASE
                WHEN op.order_id IS NOT NULL THEN o.order_id
            END
        ) AS orders_with_payment,

        SUM(op.order_payment_value) AS total_recorded_payment

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN order_payments op
        ON o.order_id = op.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY c.customer_unique_id
)

SELECT
    delivered_orders,

    COUNT(*) AS number_of_customers,

    SUM(orders_with_payment) AS orders_with_payment,

    ROUND(
        SUM(total_recorded_payment), 2
    ) AS total_recorded_payment,

    ROUND(
        AVG(COALESCE(total_recorded_payment, 0)), 2
    ) AS average_payment_per_customer,

    ROUND(
        SUM(total_recorded_payment) * 100.0 /
        SUM(SUM(total_recorded_payment)) OVER (),
        2
    ) AS payment_value_percentage

FROM customer_metrics

GROUP BY delivered_orders
ORDER BY delivered_orders;





-- =====================================================
-- Analysis 04: Top 10 Highest-Spending Customers
-- =====================================================

WITH order_payments AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_payment
    FROM payments
    GROUP BY order_id
),

customer_spending AS (
    SELECT
        c.customer_unique_id,

        COUNT(DISTINCT o.order_id) AS delivered_orders,

        COALESCE(
            SUM(op.total_payment), 0
        ) AS total_recorded_payment

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN order_payments op
        ON o.order_id = op.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY c.customer_unique_id
),

ranked_customers AS (
    SELECT
        customer_unique_id,
        delivered_orders,
        total_recorded_payment,

        DENSE_RANK() OVER (
            ORDER BY total_recorded_payment DESC
        ) AS spending_rank

    FROM customer_spending
)

SELECT
    spending_rank,
    customer_unique_id,
    delivered_orders,
    ROUND(total_recorded_payment, 2) AS total_recorded_payment

FROM ranked_customers

WHERE spending_rank <= 10
ORDER BY spending_rank;





-- =====================================================
-- Analysis 05: Investigating High-Spending Customers
-- Compare payment totals with item and freight values.
-- =====================================================

WITH order_payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_payment
    FROM payments
    GROUP BY order_id
),

order_item_totals AS (
    SELECT
        order_id,
        COUNT(*) AS total_items,
        SUM(price) AS total_product_price,
        SUM(freight_value) AS total_freight
    FROM order_items
    GROUP BY order_id
),

delivered_customer_orders AS (
    SELECT
        c.customer_unique_id,
        o.order_id,
        COALESCE(p.total_payment, 0) AS order_payment
    FROM orders o
    INNER JOIN customers c
        ON o.customer_id = c.customer_id
    LEFT JOIN order_payment_totals p
        ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
),

customer_spending AS (
    SELECT
        customer_unique_id,
        COUNT(*) AS delivered_orders,
        SUM(order_payment) AS total_recorded_payment
    FROM delivered_customer_orders
    GROUP BY customer_unique_id
),

ranked_customers AS (
    SELECT
        customer_unique_id,
        DENSE_RANK() OVER (
            ORDER BY total_recorded_payment DESC
        ) AS spending_rank
    FROM customer_spending
)

SELECT
    r.spending_rank,
    d.customer_unique_id,
    d.order_id,
    ROUND(d.order_payment, 2) AS order_payment,
    COALESCE(i.total_items, 0) AS total_items,
    ROUND(COALESCE(i.total_product_price, 0), 2)
        AS total_product_price,
    ROUND(COALESCE(i.total_freight, 0), 2)
        AS total_freight,
    ROUND(
        COALESCE(i.total_product_price, 0)
        + COALESCE(i.total_freight, 0), 2
    ) AS product_plus_freight

FROM ranked_customers r

INNER JOIN delivered_customer_orders d
    ON r.customer_unique_id = d.customer_unique_id

LEFT JOIN order_item_totals i
    ON d.order_id = i.order_id

WHERE r.spending_rank <= 10

ORDER BY r.spending_rank, d.order_id;



-- =====================================================
-- Analysis 06: Customer Geographic Distribution
-- Geography is based on the customer record
-- associated with each delivered order.
-- =====================================================

WITH order_payments AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_payment
    FROM payments
    GROUP BY order_id
),

state_metrics AS (
    SELECT
        c.customer_state,

        COUNT(DISTINCT o.order_id) AS delivered_orders,

        COUNT(DISTINCT c.customer_unique_id)
            AS unique_shoppers,

        SUM(COALESCE(op.total_payment, 0))
            AS total_recorded_payment

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN order_payments op
        ON o.order_id = op.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY c.customer_state
)

SELECT
    customer_state,
    delivered_orders,
    unique_shoppers,

    ROUND(
        unique_shoppers * 100.0 /
        SUM(unique_shoppers) OVER (), 2
    ) AS shopper_percentage,

    ROUND(total_recorded_payment, 2)
        AS total_recorded_payment,

    ROUND(
        total_recorded_payment * 100.0 /
        SUM(total_recorded_payment) OVER (), 2
    ) AS payment_percentage

FROM state_metrics

ORDER BY total_recorded_payment DESC;





-- =====================================================
-- Analysis 07: Average Payment Per Delivered Order
-- One-time vs Repeat Customers
-- =====================================================

WITH order_payments AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_payment
    FROM payments
    GROUP BY order_id
),

customer_metrics AS (
    SELECT
        c.customer_unique_id,

        COUNT(DISTINCT o.order_id) AS delivered_orders,

        COUNT(
            DISTINCT CASE
                WHEN op.order_id IS NOT NULL
                THEN o.order_id
            END
        ) AS orders_with_payment,

        SUM(op.total_payment) AS total_payment

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN order_payments op
        ON o.order_id = op.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY c.customer_unique_id
)

SELECT
    CASE
        WHEN delivered_orders = 1
            THEN 'One-time Customer'
        ELSE 'Repeat Customer'
    END AS customer_type,

    COUNT(*) AS total_customers,

    SUM(delivered_orders) AS delivered_orders,

    SUM(orders_with_payment) AS paid_orders,

    ROUND(SUM(total_payment), 2)
        AS total_recorded_payment,

    ROUND(
        SUM(total_payment) / COUNT(*), 2
    ) AS average_payment_per_customer,

    ROUND(
        SUM(total_payment) / SUM(orders_with_payment), 2
    ) AS average_payment_per_order

FROM customer_metrics

GROUP BY customer_type
ORDER BY average_payment_per_order DESC;
