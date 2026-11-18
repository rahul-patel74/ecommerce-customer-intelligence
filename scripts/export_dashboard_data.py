from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "app_data"
STAGING_DIR = OUTPUT_DIR / ".staging"
load_dotenv(PROJECT_ROOT / ".env")

QUERIES: dict[str, str] = {
    "overview_kpis": """
        SELECT
            COUNT(*) AS delivered_customers,
            SUM(frequency = 1) AS one_time_customers,
            SUM(frequency > 1) AS repeat_customers,
            SUM(frequency) AS delivered_orders,
            ROUND(SUM(monetary), 2) AS delivered_recorded_payment_value,
            ROUND(AVG(monetary), 2) AS average_payment_per_customer,
            ROUND(AVG(frequency), 2) AS average_orders_per_customer,
            ROUND(SUM(frequency > 1) * 100.0 / COUNT(*), 2)
                AS repeat_customer_rate
        FROM vw_customer_rfm
    """,

    "monthly_performance": """
        WITH order_payment_totals AS (
            SELECT order_id, SUM(payment_value) AS order_payment
            FROM payments
            GROUP BY order_id
        ),
        delivered_customer_frequency AS (
            SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS lifetime_delivered_orders
            FROM orders o
            INNER JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        )
        SELECT
            CAST(DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01') AS DATE)
                AS order_month,
            COUNT(*) AS total_orders,
            SUM(o.order_status = 'delivered') AS delivered_orders,
            ROUND(SUM(COALESCE(p.order_payment, 0)), 2)
                AS all_status_recorded_payment_value,
            ROUND(SUM(CASE WHEN o.order_status = 'delivered'
                THEN COALESCE(p.order_payment, 0) ELSE 0 END), 2)
                AS delivered_recorded_payment_value,
            COUNT(DISTINCT CASE WHEN o.order_status = 'delivered'
                THEN c.customer_unique_id END) AS monthly_active_delivered_customers,
            COUNT(DISTINCT CASE WHEN o.order_status = 'delivered'
                AND f.lifetime_delivered_orders > 1
                THEN c.customer_unique_id END) AS monthly_active_repeat_buyers
        FROM orders o
        INNER JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN order_payment_totals p ON o.order_id = p.order_id
        LEFT JOIN delivered_customer_frequency f
            ON c.customer_unique_id = f.customer_unique_id
        GROUP BY order_month
        ORDER BY order_month
    """,

    "order_status": """
        SELECT
            order_status,
            COUNT(*) AS total_orders,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)
                AS order_percentage
        FROM orders
        GROUP BY order_status
        ORDER BY total_orders DESC
    """,

    "monthly_order_status": """
        SELECT
            CAST(DATE_FORMAT(order_purchase_timestamp, '%Y-%m-01') AS DATE)
                AS order_month,
            order_status,
            COUNT(*) AS total_orders
        FROM orders
        GROUP BY order_month, order_status
        ORDER BY order_month, order_status
    """,

    "monthly_state_order_status": """
        SELECT
            CAST(DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01') AS DATE)
                AS order_month,
            c.customer_state,
            o.order_status,
            COUNT(*) AS total_orders
        FROM orders o
        INNER JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY order_month, c.customer_state, o.order_status
        ORDER BY order_month, c.customer_state, o.order_status
    """,

    "category_performance": """
        SELECT
            COALESCE(t.product_category_name_english,
                     p.product_category_name, 'Unknown / Missing')
                AS product_category,
            COUNT(DISTINCT oi.order_id) AS total_orders,
            COUNT(*) AS order_item_lines,
            ROUND(SUM(oi.price), 2) AS product_value,
            ROUND(SUM(oi.freight_value), 2) AS freight_value,
            ROUND(SUM(oi.price + oi.freight_value), 2)
                AS item_plus_freight_value
        FROM order_items oi
        INNER JOIN orders o ON oi.order_id = o.order_id
        INNER JOIN products p ON oi.product_id = p.product_id
        LEFT JOIN category_translation t
            ON p.product_category_name = t.product_category_name
        WHERE o.order_status = 'delivered'
        GROUP BY product_category
        ORDER BY item_plus_freight_value DESC
    """,

    "monthly_category_performance": """
        SELECT
            CAST(DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01') AS DATE)
                AS order_month,
            COALESCE(t.product_category_name_english,
                     p.product_category_name, 'Unknown / Missing')
                AS product_category,
            COUNT(DISTINCT oi.order_id) AS total_orders,
            COUNT(*) AS order_item_lines,
            ROUND(SUM(oi.price), 2) AS product_value,
            ROUND(SUM(oi.freight_value), 2) AS freight_value,
            ROUND(SUM(oi.price + oi.freight_value), 2)
                AS item_plus_freight_value
        FROM order_items oi
        INNER JOIN orders o ON oi.order_id = o.order_id
        INNER JOIN products p ON oi.product_id = p.product_id
        LEFT JOIN category_translation t
            ON p.product_category_name = t.product_category_name
        WHERE o.order_status = 'delivered'
        GROUP BY order_month, product_category
        ORDER BY order_month, item_plus_freight_value DESC
    """,

    "rfm_segments": """
        SELECT
            customer_segment,
            COUNT(*) AS customer_count,
            ROUND(AVG(recency), 2) AS average_recency,
            ROUND(AVG(frequency), 2) AS average_frequency,
            ROUND(AVG(monetary), 2) AS average_monetary,
            ROUND(SUM(monetary), 2) AS total_monetary
        FROM vw_customer_rfm
        GROUP BY customer_segment
        ORDER BY customer_count DESC
    """,

    "customer_frequency": """
        SELECT
            frequency,
            COUNT(*) AS customer_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)
                AS customer_percentage,
            ROUND(AVG(monetary), 2) AS average_monetary,
            ROUND(SUM(monetary), 2) AS total_monetary
        FROM vw_customer_rfm
        GROUP BY frequency
        ORDER BY frequency
    """,

    "customer_type_metrics": """
        WITH order_payment_totals AS (
            SELECT order_id, SUM(payment_value) AS order_payment
            FROM payments
            GROUP BY order_id
        ), customer_metrics AS (
            SELECT
                c.customer_unique_id,
                COUNT(DISTINCT o.order_id) AS delivered_orders,
                COUNT(DISTINCT CASE WHEN p.order_id IS NOT NULL
                    THEN o.order_id END) AS paid_orders,
                SUM(COALESCE(p.order_payment, 0)) AS recorded_payment_value
            FROM orders o
            INNER JOIN customers c ON o.customer_id = c.customer_id
            LEFT JOIN order_payment_totals p ON o.order_id = p.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        )
        SELECT
            CASE WHEN delivered_orders = 1
                THEN 'One-time customers' ELSE 'Repeat customers' END
                AS customer_type,
            COUNT(*) AS customer_count,
            SUM(delivered_orders) AS delivered_orders,
            SUM(paid_orders) AS paid_orders,
            ROUND(SUM(recorded_payment_value), 2)
                AS recorded_payment_value,
            ROUND(AVG(recorded_payment_value), 2)
                AS average_payment_per_customer,
            ROUND(SUM(recorded_payment_value) / NULLIF(SUM(paid_orders), 0), 2)
                AS average_payment_per_paid_order
        FROM customer_metrics
        GROUP BY customer_type
        ORDER BY customer_count DESC
    """,

    "cohort_retention": """
        SELECT cohort_month, activity_month, cohort_index, cohort_size,
               retained_customers, retention_percentage
        FROM vw_cohort_retention
        ORDER BY cohort_month, cohort_index
    """,

    "state_performance": """
        WITH order_payment_totals AS (
            SELECT order_id, SUM(payment_value) AS order_payment
            FROM payments GROUP BY order_id
        )
        SELECT
            c.customer_state,
            COUNT(DISTINCT o.order_id) AS delivered_orders,
            COUNT(DISTINCT c.customer_unique_id) AS unique_shoppers,
            ROUND(SUM(COALESCE(p.order_payment, 0)), 2)
                AS recorded_payment_value
        FROM orders o
        INNER JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN order_payment_totals p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_state
        ORDER BY recorded_payment_value DESC
    """,

    "monthly_state_performance": """
        WITH order_payment_totals AS (
            SELECT order_id, SUM(payment_value) AS order_payment
            FROM payments GROUP BY order_id
        )
        SELECT
            CAST(DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01') AS DATE)
                AS order_month,
            c.customer_state,
            COUNT(DISTINCT o.order_id) AS delivered_orders,
            COUNT(DISTINCT c.customer_unique_id) AS unique_shoppers,
            ROUND(SUM(COALESCE(p.order_payment, 0)), 2)
                AS recorded_payment_value
        FROM orders o
        INNER JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN order_payment_totals p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY order_month, c.customer_state
        ORDER BY order_month, c.customer_state
    """,

    "payment_methods": """
        SELECT
            COALESCE(payment_type, 'unknown') AS payment_type,
            COUNT(*) AS payment_records,
            COUNT(DISTINCT order_id) AS orders_using_method,
            ROUND(SUM(payment_value), 2) AS recorded_payment_value,
            ROUND(AVG(payment_value), 2) AS average_payment_record
        FROM payments
        GROUP BY payment_type
        ORDER BY recorded_payment_value DESC
    """,

    "delivery_performance": """
        SELECT
            CAST(DATE_FORMAT(order_purchase_timestamp, '%Y-%m-01') AS DATE)
                AS order_month,
            COUNT(*) AS delivered_orders_with_dates,
            ROUND(AVG(TIMESTAMPDIFF(HOUR,
                order_purchase_timestamp, order_delivered_customer_date) / 24.0), 2)
                AS average_delivery_days,
            ROUND(AVG(TIMESTAMPDIFF(HOUR,
                order_purchase_timestamp, order_estimated_delivery_date) / 24.0), 2)
                AS average_estimated_days,
            ROUND(100.0 * AVG(order_delivered_customer_date <=
                order_estimated_delivery_date), 2) AS on_time_delivery_rate
        FROM orders
        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NOT NULL
          AND order_estimated_delivery_date IS NOT NULL
        GROUP BY order_month
        ORDER BY order_month
    """,

    "data_quality": """
        SELECT 'Credit-card payments with zero installments' AS issue,
               COUNT(*) AS flagged_rows, 'Review' AS severity,
               'Preserved and flagged; intended installment count is unknown.' AS decision
        FROM payments
        WHERE payment_type = 'credit_card' AND payment_installments = 0
        UNION ALL
        SELECT 'Geolocation rows outside approximate Brazil bounds',
               COUNT(*), 'Review',
               'Preserved and flagged; bounding box is a screening rule, not an official border.'
        FROM geolocation
        WHERE geolocation_lat IS NOT NULL AND geolocation_lng IS NOT NULL
          AND NOT (geolocation_lat BETWEEN -35 AND 6
                   AND geolocation_lng BETWEEN -75 AND -32)
        UNION ALL
        SELECT 'Excess exact duplicate geolocation rows',
               COALESCE(SUM(duplicate_count - 1), 0), 'Information',
               'Retained; repeat rows were not assumed to be erroneous.'
        FROM (
            SELECT COUNT(*) AS duplicate_count
            FROM geolocation
            GROUP BY
                CAST(geolocation_zip_code_prefix AS BINARY),
                geolocation_lat,
                geolocation_lng,
                CAST(geolocation_city AS BINARY),
                CAST(geolocation_state AS BINARY)
            HAVING COUNT(*) > 1
        ) duplicate_groups
        UNION ALL
        SELECT 'Customer ZIP records without a geolocation match',
               COUNT(*), 'Information',
               'Customer records retained; no geographic coordinates were fabricated.'
        FROM customers c
        WHERE NOT EXISTS (
            SELECT 1 FROM geolocation g
            WHERE g.geolocation_zip_code_prefix = c.customer_zip_code_prefix
        )
        UNION ALL
        SELECT 'Seller ZIP records without a geolocation match',
               COUNT(*), 'Information',
               'Seller records retained; no geographic coordinates were fabricated.'
        FROM sellers s
        WHERE NOT EXISTS (
            SELECT 1 FROM geolocation g
            WHERE g.geolocation_zip_code_prefix = s.seller_zip_code_prefix
        )
        UNION ALL
        SELECT 'Products with a missing category',
               COUNT(*), 'Information',
               'Product records retained; missing category values were not imputed.'
        FROM products
        WHERE product_category_name IS NULL
        UNION ALL
        SELECT 'Products assigned to untranslated categories',
               COUNT(*), 'Information',
               'Original category names retained; no translation was invented.'
        FROM products p
        WHERE p.product_category_name IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM category_translation t
              WHERE t.product_category_name = p.product_category_name
          )
    """,
}

DATASET_DESCRIPTIONS = {
    "overview_kpis": "Full-period customer KPIs from vw_customer_rfm.",
    "monthly_performance": "One row per purchase month; all-status and delivered-only payment totals are separated.",
    "order_status": "All-time distribution of order statuses.",
    "monthly_order_status": "Order counts by purchase month and order status.",
    "monthly_state_order_status": "Order counts by purchase month, customer state and order status.",
    "category_performance": "Delivered order-item value and freight aggregated by product category.",
    "monthly_category_performance": "Delivered order-item metrics by month and product category.",
    "rfm_segments": "Customer counts and RFM metrics by segment from vw_customer_rfm.",
    "customer_frequency": "Delivered purchase frequency distribution from vw_customer_rfm.",
    "customer_type_metrics": "Delivered order and recorded payment comparison for one-time and repeat customers.",
    "cohort_retention": "Long-format cohort retention data from vw_cohort_retention.",
    "state_performance": "Delivered order metrics by customer state.",
    "monthly_state_performance": "Delivered order and payment metrics by month and customer state.",
    "payment_methods": "Recorded payment values grouped by payment method, across all order statuses.",
    "delivery_performance": "Delivery-time and on-time metrics for delivered orders with usable dates.",
    "data_quality": "Documented SQL checks for known payment, geographic and lookup-quality findings.",
}


def get_database_connection():
    required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if os.getenv(key) is None]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connection_timeout=15,
    )


def export_dashboard_data():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.mkdir(parents=True)

    connection = None
    export_summary = []

    try:
        print("Connecting to MySQL database...")
        connection = get_database_connection()
        print("Database connection successful.")

        for dataset_name, query in QUERIES.items():
            print(f"Extracting {dataset_name}...")
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]

            df = pd.DataFrame(rows, columns=columns)
            if df.empty:
                raise ValueError(f"{dataset_name} returned no rows; export stopped.")

            output_path = STAGING_DIR / f"{dataset_name}.csv"
            df.to_csv(output_path, index=False, encoding="utf-8")

            export_summary.append({
                "dataset": dataset_name,
                "file": output_path.name,
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
                "size_bytes": int(output_path.stat().st_size),
                "description": DATASET_DESCRIPTIONS[dataset_name],
            })

        manifest = {
            "project": "E-commerce Customer Intelligence & Retention Analytics",
            "database": os.getenv("DB_NAME"),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "export_version": 2,
            "dataset_count": len(export_summary),
            "datasets": export_summary,
            "notes": [
                "All extracts are aggregated analytical data; customer identifiers are not exported.",
                "Payment value is not profit or accounting revenue.",
                "Monthly recorded payments include all order statuses unless a dataset description says otherwise.",
                "State-level distinct shopper counts may overlap across states.",
            ],
        }
        (STAGING_DIR / "data_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

        # Replace files only after every query and write succeeds.
        for staged_file in STAGING_DIR.iterdir():
            if staged_file.is_file():
                staged_file.replace(OUTPUT_DIR / staged_file.name)

        summary_df = pd.DataFrame(export_summary)
        print("\nExport summary")
        print(summary_df[["dataset", "rows", "columns", "size_bytes"]].to_string(index=False))
        print(f"\nDatasets exported: {len(export_summary)}")
        print(f"Output directory: {OUTPUT_DIR}")
        print("Manifest: data_manifest.json")

    except Exception as error:
        print(f"Export failed: {error}")
        raise
    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("\nDatabase connection closed.")
        if STAGING_DIR.exists():
            shutil.rmtree(STAGING_DIR, ignore_errors=True)


if __name__ == "__main__":
    export_dashboard_data()
