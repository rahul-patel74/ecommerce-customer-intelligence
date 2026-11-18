from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "app_data"
ASSETS_DIR = PROJECT_ROOT / "assets"

DATA_FILES = {
    "overview_kpis": "overview_kpis.csv",
    "monthly_performance": "monthly_performance.csv",
    "order_status": "order_status.csv",
    "monthly_order_status": "monthly_order_status.csv",
    "monthly_state_order_status": "monthly_state_order_status.csv",
    "category_performance": "category_performance.csv",
    "monthly_category_performance": "monthly_category_performance.csv",
    "rfm_segments": "rfm_segments.csv",
    "customer_frequency": "customer_frequency.csv",
    "customer_type_metrics": "customer_type_metrics.csv",
    "cohort_retention": "cohort_retention.csv",
    "state_performance": "state_performance.csv",
    "monthly_state_performance": "monthly_state_performance.csv",
    "payment_methods": "payment_methods.csv",
    "delivery_performance": "delivery_performance.csv",
    "data_quality": "data_quality.csv",
}

DATE_COLUMNS = {
    "monthly_performance": ["order_month"],
    "monthly_order_status": ["order_month"],
    "monthly_state_order_status": ["order_month"],
    "monthly_category_performance": ["order_month"],
    "cohort_retention": ["cohort_month", "activity_month"],
    "monthly_state_performance": ["order_month"],
    "delivery_performance": ["order_month"],
}

NUMERIC_COLUMNS = {
    "overview_kpis": [
        "delivered_customers", "one_time_customers", "repeat_customers",
        "delivered_orders", "delivered_recorded_payment_value",
        "average_payment_per_customer", "average_orders_per_customer",
        "repeat_customer_rate",
    ],
    "monthly_performance": [
        "total_orders", "delivered_orders", "all_status_recorded_payment_value",
        "delivered_recorded_payment_value", "monthly_active_delivered_customers",
        "monthly_active_repeat_buyers",
    ],
    "order_status": ["total_orders", "order_percentage"],
    "monthly_order_status": ["total_orders"],
    "monthly_state_order_status": ["total_orders"],
    "category_performance": [
        "total_orders", "order_item_lines", "product_value", "freight_value",
        "item_plus_freight_value",
    ],
    "monthly_category_performance": [
        "total_orders", "order_item_lines", "product_value", "freight_value",
        "item_plus_freight_value",
    ],
    "rfm_segments": [
        "customer_count", "average_recency", "average_frequency",
        "average_monetary", "total_monetary",
    ],
    "customer_frequency": [
        "frequency", "customer_count", "customer_percentage",
        "average_monetary", "total_monetary",
    ],
    "customer_type_metrics": [
        "customer_count", "delivered_orders", "paid_orders",
        "recorded_payment_value", "average_payment_per_customer",
        "average_payment_per_paid_order",
    ],
    "cohort_retention": [
        "cohort_index", "cohort_size", "retained_customers", "retention_percentage",
    ],
    "state_performance": [
        "delivered_orders", "unique_shoppers", "recorded_payment_value",
    ],
    "monthly_state_performance": [
        "delivered_orders", "unique_shoppers", "recorded_payment_value",
    ],
    "payment_methods": [
        "payment_records", "orders_using_method", "recorded_payment_value",
        "average_payment_record",
    ],
    "delivery_performance": [
        "delivered_orders_with_dates", "average_delivery_days",
        "average_estimated_days", "on_time_delivery_rate",
    ],
    "data_quality": ["flagged_rows"],
}

REQUIRED_COLUMNS = {
    "overview_kpis": ["delivered_customers", "one_time_customers", "repeat_customers", "delivered_recorded_payment_value"],
    "monthly_performance": ["order_month", "total_orders", "delivered_orders", "delivered_recorded_payment_value"],
    "order_status": ["order_status", "total_orders", "order_percentage"],
    "monthly_order_status": ["order_month", "order_status", "total_orders"],
    "monthly_state_order_status": ["order_month", "customer_state", "order_status", "total_orders"],
    "category_performance": ["product_category", "item_plus_freight_value"],
    "monthly_category_performance": ["order_month", "product_category", "item_plus_freight_value"],
    "rfm_segments": ["customer_segment", "customer_count", "total_monetary"],
    "customer_frequency": ["frequency", "customer_count"],
    "customer_type_metrics": ["customer_type", "customer_count", "recorded_payment_value"],
    "cohort_retention": ["cohort_month", "activity_month", "cohort_index", "cohort_size", "retained_customers", "retention_percentage"],
    "state_performance": ["customer_state", "delivered_orders", "recorded_payment_value"],
    "monthly_state_performance": ["order_month", "customer_state", "delivered_orders", "recorded_payment_value"],
    "payment_methods": ["payment_type", "payment_records", "recorded_payment_value"],
    "delivery_performance": ["order_month", "average_delivery_days", "on_time_delivery_rate"],
    "data_quality": ["issue", "flagged_rows", "severity", "decision"],
}


class DashboardDataError(RuntimeError):
    """Raised when dashboard snapshots are missing or malformed."""


@st.cache_data(show_spinner=False, ttl=900)
def load_dashboard_data() -> dict[str, pd.DataFrame]:
    """Load all pre-aggregated dashboard snapshots with typed columns."""
    datasets: dict[str, pd.DataFrame] = {}
    missing = [filename for filename in DATA_FILES.values() if not (DATA_DIR / filename).is_file()]
    if missing:
        joined = ", ".join(missing)
        raise DashboardDataError(
            f"Dashboard extracts are missing: {joined}. Run `python scripts/export_dashboard_data.py`."
        )

    for key, filename in DATA_FILES.items():
        path = DATA_DIR / filename
        try:
            frame = pd.read_csv(path, low_memory=False)
        except Exception as exc:
            raise DashboardDataError(f"Could not read {filename}: {exc}") from exc
        if frame.empty:
            raise DashboardDataError(f"{filename} is empty. Re-run the export script.")

        missing_columns = [column for column in REQUIRED_COLUMNS[key] if column not in frame.columns]
        if missing_columns:
            raise DashboardDataError(
                f"{filename} is missing columns: {', '.join(missing_columns)}. Re-run the current export script."
            )

        for column in DATE_COLUMNS.get(key, []):
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
        for column in NUMERIC_COLUMNS.get(key, []):
            if column in frame.columns:
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
        datasets[key] = frame

    return datasets


@st.cache_data(show_spinner=False, ttl=86400)
def load_manifest() -> dict[str, Any]:
    path = DATA_DIR / "data_manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


@st.cache_data(show_spinner=False, ttl=86400)
def load_brazil_geojson() -> dict[str, Any] | None:
    """Load IBGE-derived Brazilian state boundaries; gracefully return None offline."""
    import requests

    url = (
        "https://cdn.jsdelivr.net/gh/henriquemalvar/br-geojson@main/"
        "dist/estados.geojson"
    )
    try:
        response = requests.get(url, timeout=12)
        response.raise_for_status()
        geojson = response.json()
        features = geojson.get("features", [])
        if not features:
            return None
        if not all("sigla" in feature.get("properties", {}) for feature in features):
            return None
        return geojson
    except (requests.RequestException, ValueError, TypeError):
        return None


def month_options(data: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    values = pd.to_datetime(data["monthly_performance"]["order_month"], errors="coerce").dropna()
    return sorted(pd.Timestamp(value).normalize() for value in values.unique())


def selected_filters() -> dict[str, Any]:
    return st.session_state.get(
        "dashboard_filters",
        {"date_start": None, "date_end": None, "states": [], "categories": []},
    )


def filter_by_period(frame: pd.DataFrame, date_column: str = "order_month") -> pd.DataFrame:
    filters = selected_filters()
    if date_column not in frame.columns:
        return frame.copy()
    result = frame.copy()
    result[date_column] = pd.to_datetime(result[date_column], errors="coerce")
    if filters.get("date_start") is not None:
        result = result[result[date_column] >= pd.Timestamp(filters["date_start"])]
    if filters.get("date_end") is not None:
        result = result[result[date_column] <= pd.Timestamp(filters["date_end"])]
    return result


def filter_by_states(frame: pd.DataFrame, state_column: str = "customer_state") -> pd.DataFrame:
    filters = selected_filters()
    states = filters.get("states") or []
    if not states or state_column not in frame.columns:
        return frame.copy()
    return frame[frame[state_column].isin(states)].copy()


def filter_by_categories(frame: pd.DataFrame, category_column: str = "product_category") -> pd.DataFrame:
    filters = selected_filters()
    categories = filters.get("categories") or []
    if not categories or category_column not in frame.columns:
        return frame.copy()
    return frame[frame[category_column].isin(categories)].copy()


def filter_context_label() -> str:
    filters = selected_filters()
    start = filters.get("date_start")
    end = filters.get("date_end")
    if start and end:
        period = f"{pd.Timestamp(start):%b %Y} - {pd.Timestamp(end):%b %Y}"
    else:
        period = "Full period"
    states = filters.get("states") or []
    state_label = ", ".join(states) if states else "All states"
    categories = filters.get("categories") or []
    category_label = f"{len(categories)} category filter(s)" if categories else "All categories"
    return f"{period}  |  {state_label}  |  {category_label}"
