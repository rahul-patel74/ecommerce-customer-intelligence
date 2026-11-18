from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "app_data"

EXPECTED_SEGMENTS = {
    "Recent One-time Customers": 36118,
    "High-Value One-time Lapsed": 21024,
    "Needs Attention": 18614,
    "Hibernating": 15368,
    "Potential Loyalists": 1080,
    "At Risk": 997,
    "Loyal Customers": 125,
    "Champions": 32,
}

REQUIRED_FILES = [
    "overview_kpis.csv", "monthly_performance.csv", "order_status.csv",
    "monthly_order_status.csv", "monthly_state_order_status.csv", "category_performance.csv",
    "monthly_category_performance.csv", "rfm_segments.csv",
    "customer_frequency.csv", "customer_type_metrics.csv",
    "cohort_retention.csv", "state_performance.csv",
    "monthly_state_performance.csv", "payment_methods.csv",
    "delivery_performance.csv", "data_quality.csv", "data_manifest.json",
]


def validate_dashboard_data() -> None:
    total_checks = 0
    failures = 0

    def check(condition: bool, description: str) -> None:
        nonlocal total_checks, failures
        total_checks += 1
        passed = bool(condition)
        failures += 0 if passed else 1
        print(f"[{'PASS' if passed else 'FAIL'}] {description}")

    print("=" * 64)
    print("E-COMMERCE INTELLIGENCE | DATA QUALITY GATE")
    print("=" * 64)

    missing = [name for name in REQUIRED_FILES if not (DATA_DIR / name).exists()]
    check(not missing, f"All {len(REQUIRED_FILES)} required export files exist")
    if missing:
        print("Missing:", ", ".join(missing))
        raise FileNotFoundError("Export files are missing; rerun export_dashboard_data.py")

    data = {
        filename.removesuffix(".csv"): pd.read_csv(DATA_DIR / filename)
        for filename in REQUIRED_FILES if filename.endswith(".csv")
    }
    manifest = json.loads((DATA_DIR / "data_manifest.json").read_text(encoding="utf-8"))

    check(manifest.get("dataset_count") == 16, "Manifest lists 16 exported datasets")
    check(len(data["overview_kpis"]) == 1, "Overview contains one KPI row")
    kpi = data["overview_kpis"].iloc[0]
    check(int(kpi["delivered_customers"]) == 93358, "Delivered shoppers reconcile to 93,358")
    check(int(kpi["one_time_customers"]) == 90557, "One-time shoppers reconcile to 90,557")
    check(int(kpi["repeat_customers"]) == 2801, "Repeat shoppers reconcile to 2,801")
    check(int(kpi["one_time_customers"] + kpi["repeat_customers"]) == int(kpi["delivered_customers"]),
          "One-time and repeat shoppers sum to total delivered shoppers")

    segments = data["rfm_segments"]
    actual_segments = dict(zip(segments.customer_segment, segments.customer_count.astype(int)))
    check(actual_segments == EXPECTED_SEGMENTS, "All eight RFM segment counts match validated SQL results")
    check(int(segments.customer_count.sum()) == 93358, "RFM segment counts sum to 93,358")
    check(int(data["customer_frequency"].customer_count.sum()) == 93358,
          "Purchase-frequency groups sum to 93,358 customers")

    cohort = data["cohort_retention"]
    check(len(cohort) == 278, "Cohort view contains 278 cohort-month records")
    check(cohort.cohort_month.nunique() == 23, "Cohort view contains 23 cohorts")
    check(not cohort.duplicated(["cohort_month", "cohort_index"]).any(),
          "Cohort-month keys are unique")
    check(cohort.retention_percentage.between(0, 100).all(),
          "Cohort retention percentages are within 0-100")
    check((cohort.retained_customers <= cohort.cohort_size).all(),
          "Retained customers never exceed cohort size")
    month_zero = cohort.loc[cohort.cohort_index == 0]
    check((month_zero.retained_customers == month_zero.cohort_size).all(),
          "Month 0 retained customers equal cohort size")

    status = data["order_status"]
    check(len(status) == 8 and int(status.total_orders.sum()) == 99441,
          "All-time order-status counts reconcile to 99,441 orders")
    monthly_status = data["monthly_order_status"]
    check(int(monthly_status.total_orders.sum()) == 99441,
          "Monthly order-status counts reconcile to 99,441 orders")
    monthly_state_status = data["monthly_state_order_status"]
    check(int(monthly_state_status.total_orders.sum()) == 99441,
          "Monthly state + status counts reconcile to 99,441 orders")

    monthly = data["monthly_performance"]
    check(len(monthly) == 25, "Monthly performance contains 25 months")
    check(pd.to_datetime(monthly.order_month, errors="coerce").notna().all(),
          "Monthly performance dates parse successfully")
    check(int(monthly.total_orders.sum()) == 99441,
          "Monthly order counts reconcile to 99,441 orders")
    check((monthly.delivered_orders <= monthly.total_orders).all(),
          "Monthly delivered orders do not exceed total orders")

    categories = data["category_performance"]
    check(len(categories) == 74, "Category performance contains 74 category groups")
    monthly_categories = data["monthly_category_performance"]
    check(not monthly_categories.empty, "Monthly category performance is populated")
    check((monthly_categories.item_plus_freight_value >= 0).all(),
          "Monthly category item-plus-freight values are non-negative")

    states = data["state_performance"]
    monthly_states = data["monthly_state_performance"]
    check(len(states) == 27, "State performance contains 27 state groups")
    check(not monthly_states.empty, "Monthly state performance is populated")
    check(int(states.delivered_orders.sum()) == int(monthly.delivered_orders.sum()),
          "State delivered-order totals reconcile with monthly delivered orders")
    check(int(monthly_states.delivered_orders.sum()) == int(monthly.delivered_orders.sum()),
          "Monthly state delivered-order totals reconcile with monthly data")

    customer_types = data["customer_type_metrics"]
    customer_type_map = dict(zip(customer_types.customer_type, customer_types.customer_count.astype(int)))
    check(customer_type_map.get("One-time customers") == 90557
          and customer_type_map.get("Repeat customers") == 2801,
          "Customer type counts reconcile with one-time and repeat analysis")

    data_quality = data["data_quality"].set_index("issue")
    dq = dict(zip(data_quality.index, data_quality.flagged_rows.astype(int)))
    check(dq.get("Credit-card payments with zero installments") == 2,
          "Two zero-installment credit-card records are documented")
    check(dq.get("Geolocation rows outside approximate Brazil bounds") == 29,
          "Twenty-nine approximate Brazil-boundary records are documented")
    check(dq.get("Excess exact duplicate geolocation rows") == 261831,
          "Geolocation duplicate excess count matches investigation")
    check(dq.get("Customer ZIP records without a geolocation match") == 278,
          "Customer geolocation lookup gap matches 278 records")
    check(dq.get("Seller ZIP records without a geolocation match") == 7,
          "Seller geolocation lookup gap matches 7 records")
    check(dq.get("Products with a missing category") == 610,
          "Missing product category count matches 610 records")
    check(dq.get("Products assigned to untranslated categories") == 13,
          "Untranslated product category count matches 13 records")

    payment_methods = data["payment_methods"]
    check(int(payment_methods.payment_records.sum()) == 103886,
          "Payment-method record counts reconcile to 103,886")
    delivery = data["delivery_performance"]
    check(not delivery.empty and delivery.on_time_delivery_rate.between(0, 100).all(),
          "Delivery performance rates are valid")

    print("\n" + "=" * 64)
    print(f"RESULT: {total_checks - failures} checks passed | {failures} failed | {total_checks} total")
    print("=" * 64)
    if failures:
        raise ValueError("Data validation failed. Review failed checks before launching the app.")


if __name__ == "__main__":
    validate_dashboard_data()
