from __future__ import annotations

import numpy as np
import pandas as pd

from app_core.data import (
    filter_by_categories,
    filter_by_period,
    filter_by_states,
    selected_filters,
)


def monthly_scope(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Monthly order/payment series, optionally constrained to selected states."""
    filters = selected_filters()
    if filters.get("states"):
        frame = filter_by_period(data["monthly_state_performance"])
        frame = filter_by_states(frame)
        if frame.empty:
            return pd.DataFrame(columns=[
                "order_month", "total_orders", "delivered_orders",
                "delivered_recorded_payment_value", "shopper_months",
            ])
        result = frame.groupby("order_month", as_index=False).agg(
            delivered_orders=("delivered_orders", "sum"),
            delivered_recorded_payment_value=("recorded_payment_value", "sum"),
        )
        # Keep the all-status order count correct when a state filter is active.
        # The state/status extract supplies cancelled, shipped and other statuses too.
        status_frame = filter_by_period(data["monthly_state_order_status"])
        status_frame = filter_by_states(status_frame)
        total_by_month = status_frame.groupby("order_month", as_index=False).agg(
            total_orders=("total_orders", "sum")
        )
        result = result.merge(total_by_month, on="order_month", how="left")
        result["total_orders"] = result["total_orders"].fillna(0).astype(int)
        return result.sort_values("order_month")
    frame = filter_by_period(data["monthly_performance"])
    return frame.sort_values("order_month")


def category_scope(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = filter_by_period(data["monthly_category_performance"])
    frame = filter_by_categories(frame)
    if frame.empty:
        return frame
    return frame.groupby("product_category", as_index=False).agg(
        total_orders=("total_orders", "sum"),
        order_item_lines=("order_item_lines", "sum"),
        product_value=("product_value", "sum"),
        freight_value=("freight_value", "sum"),
        item_plus_freight_value=("item_plus_freight_value", "sum"),
    ).sort_values("item_plus_freight_value", ascending=False)


def status_scope(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if selected_filters().get("states"):
        frame = filter_by_period(data["monthly_state_order_status"])
        frame = filter_by_states(frame)
    else:
        frame = filter_by_period(data["monthly_order_status"])
    if frame.empty:
        return frame
    return frame.groupby("order_status", as_index=False).agg(
        total_orders=("total_orders", "sum")
    ).sort_values("total_orders", ascending=False)


def state_scope(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Filter state operating metrics by period; keep distinct shoppers full-period.

    Monthly distinct shopper counts cannot be summed across months without
    double-counting shoppers who return. The state shopper count therefore
    comes from the all-history state extract and is explicitly labelled as such.
    """
    frame = filter_by_period(data["monthly_state_performance"])
    frame = filter_by_states(frame)
    if frame.empty:
        return pd.DataFrame(columns=[
            "customer_state", "delivered_orders",
            "recorded_payment_value", "unique_shoppers_full_period",
        ])
    result = frame.groupby("customer_state", as_index=False).agg(
        delivered_orders=("delivered_orders", "sum"),
        recorded_payment_value=("recorded_payment_value", "sum"),
    )
    full_period_shoppers = data["state_performance"][
        ["customer_state", "unique_shoppers"]
    ].rename(columns={"unique_shoppers": "unique_shoppers_full_period"})
    result = result.merge(full_period_shoppers, on="customer_state", how="left")
    return result.sort_values("recorded_payment_value", ascending=False)


def trend_comparison(frame: pd.DataFrame, value_column: str) -> tuple[str, bool]:
    """Compare the latest six available months with the preceding six."""
    if frame.empty or value_column not in frame.columns:
        return "No comparison", False
    values = frame.sort_values("order_month")[value_column].fillna(0).astype(float).tolist()
    if len(values) < 2:
        return "Limited history", False
    recent = float(np.sum(values[-6:]))
    previous_values = values[-12:-6]
    if not previous_values:
        return "Baseline period", False
    previous = float(np.sum(previous_values))
    if previous == 0:
        return "No prior baseline", False
    change = (recent - previous) / abs(previous) * 100
    return f"{'+' if change >= 0 else ''}{change:.1f}% vs prior period", change < 0


def weighted_cohort_retention(cohort: pd.DataFrame) -> pd.DataFrame:
    if cohort.empty:
        return pd.DataFrame(columns=["cohort_index", "eligible_customers", "retained_customers", "retention_percentage", "cohorts_observed"])
    result = cohort.groupby("cohort_index", as_index=False).agg(
        eligible_customers=("cohort_size", "sum"),
        retained_customers=("retained_customers", "sum"),
        cohorts_observed=("cohort_month", "nunique"),
    )
    result["retention_percentage"] = np.where(
        result["eligible_customers"] > 0,
        result["retained_customers"] / result["eligible_customers"] * 100,
        0,
    )
    return result


def first_month_retention(cohort: pd.DataFrame) -> tuple[int, int, float]:
    month_one = cohort.loc[cohort["cohort_index"] == 1]
    eligible = int(month_one["cohort_size"].sum())
    retained = int(month_one["retained_customers"].sum())
    rate = retained / eligible * 100 if eligible else 0.0
    return retained, eligible, rate


def safe_pct(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) * 100 if denominator else 0.0
