from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_core.analytics import (
    category_scope,
    monthly_scope,
    safe_pct,
    state_scope,
    status_scope,
    trend_comparison,
    weighted_cohort_retention,
)
from app_core.charts import (
    category_bar,
    empty_figure,
    monthly_orders,
    monthly_payments,
    state_map,
    status_donut,
)
from app_core.data import load_brazil_geojson, selected_filters
from app_core.page_utils import page_data, page_footer, page_hero
from app_core.theme import COLORS, PLOTLY_CONFIG, insight_card, metric_card, section_heading, chart_style


data = page_data()
kpi = data["overview_kpis"].iloc[0]
monthly = monthly_scope(data)
monthly_all = data["monthly_performance"].copy().sort_values("order_month")
category_data = category_scope(data)
state_data = state_scope(data)
status_data = status_scope(data)
filters = selected_filters()

page_hero(
    "E-COMMERCE IQ  /  EXECUTIVE OVERVIEW",
    "A clearer view of the commerce engine.",
    "Understand the business at a glance: customer mix, delivered demand, recorded payment activity, product performance and where the customer base is concentrated.",
    data,
)

# Four KPI cards: customer-level values are full-history context; period metrics follow the global date/state filters.
active_customer_spark = monthly_all["monthly_active_delivered_customers"].tail(12).fillna(0).tolist()
repeat_activity_spark = monthly_all["monthly_active_repeat_buyers"].tail(12).fillna(0).tolist()
order_spark = monthly["delivered_orders"].tail(12).fillna(0).tolist() if not monthly.empty else []
payment_spark = monthly["delivered_recorded_payment_value"].tail(12).fillna(0).tolist() if not monthly.empty else []
period_orders = int(monthly["delivered_orders"].sum()) if not monthly.empty else 0
period_payment = float(monthly["delivered_recorded_payment_value"].sum()) if not monthly.empty else 0.0
order_trend, order_trend_down = trend_comparison(monthly, "delivered_orders")
payment_trend, payment_trend_down = trend_comparison(monthly, "delivered_recorded_payment_value")
repeat_rate = float(kpi["repeat_customer_rate"])

section_heading("Business pulse", "Full-history customer metrics + date/state-filtered operating metrics")
metric_cols = st.columns(4, gap="medium")
with metric_cols[0]:
    metric_card(
        "Delivered customers", f"{int(kpi['delivered_customers']):,}",
        "Unique shoppers · full observed history", "◉", COLORS["teal"], active_customer_spark,
    )
with metric_cols[1]:
    metric_card(
        "Repeat customer rate", f"{repeat_rate:.2f}%",
        f"{int(kpi['repeat_customers']):,} repeat shoppers · full history", "↻", COLORS["purple"], repeat_activity_spark,
    )
with metric_cols[2]:
    metric_card(
        "Delivered orders", f"{period_orders:,}",
        "Selected scope · latest 6 vs prior 6 months", "▥", COLORS["blue"], order_spark,
        trend=order_trend, trend_down=order_trend_down,
    )
with metric_cols[3]:
    metric_card(
        "Delivered payment value", f"R$ {period_payment / 1_000_000:.2f}M" if period_payment >= 1_000_000 else f"R$ {period_payment:,.0f}",
        "Recorded payments · not profit · latest 6 vs prior 6 months", "↗", COLORS["amber"], payment_spark,
        trend=payment_trend, trend_down=payment_trend_down,
    )

st.markdown(
    "<div class='callout good-callout'>The customer cards describe all delivered-order history. "
    "The order and payment cards respond to the selected period and state filters. "
    "The sparkline under repeat rate shows monthly active repeat buyers, not a month-by-month repeat-rate calculation.</div>",
    unsafe_allow_html=True,
)

section_heading("Performance trajectory", "Select a period and state scope from the sidebar to explore the operating trend")
left, right = st.columns([1.2, 1], gap="large")
with left:
    with st.container(border=True):
        st.markdown("**Delivered recorded payment value**")
        st.plotly_chart(monthly_payments(monthly), use_container_width=True, config=PLOTLY_CONFIG)
        if len(monthly) >= 2:
            st.caption(f"{len(monthly)} monthly observations · filtered total: R$ {period_payment:,.2f}")
        else:
            st.caption("No monthly observations for the selected filter scope.")
with right:
    with st.container(border=True):
        st.markdown("**Delivered order volume**")
        st.plotly_chart(monthly_orders(monthly), use_container_width=True, config=PLOTLY_CONFIG)
        st.caption(f"{period_orders:,} delivered orders in the selected view.")

section_heading("Where performance is coming from", "Category filters affect the category view; state filters affect the map and state ranking")
map_col, category_col = st.columns([1.12, 1], gap="large")
with map_col:
    with st.container(border=True):
        st.markdown("**Brazil · state-level payment footprint**")
        geojson = load_brazil_geojson()
        st.plotly_chart(state_map(state_data, geojson), use_container_width=True, config={**PLOTLY_CONFIG, "scrollZoom": False})
        if geojson is None:
            st.caption("Map boundaries are hosted from an IBGE-derived, CC0-licensed GeoJSON source. The state scorecard remains available on the Sales & Operations page.")
        else:
            st.caption("Hover for delivered orders and period-filtered recorded payments. Unique shopper counts shown in the tooltip are full-history distinct counts. Geometry source: IBGE-derived state boundaries.")
        if not state_data.empty:
            top_state = state_data.iloc[0]
            st.markdown(
                f"<span class='small-badge'>Leading state · {top_state['customer_state']}</span> "
                f"<span style='color:#9DB0C5;font-size:11px'>R$ {float(top_state['recorded_payment_value']):,.0f} recorded payments</span>",
                unsafe_allow_html=True,
            )
with category_col:
    with st.container(border=True):
        st.markdown("**Category contribution · delivered items**")
        st.plotly_chart(category_bar(category_data, limit=10), use_container_width=True, config=PLOTLY_CONFIG)
        st.caption("Product price + freight at delivered order-item level. Category view responds to date and category filters; state selection does not apply. Not accounting revenue or profit.")

section_heading("Order health", "Order status is filtered by date; the current status mix is not a delivery-quality score")
status_col, insight_col = st.columns([.95, 1.05], gap="large")
with status_col:
    with st.container(border=True):
        st.markdown("**Order status distribution**")
        st.plotly_chart(status_donut(status_data), use_container_width=True, config=PLOTLY_CONFIG)
        status_scope_note = "selected states" if filters.get("states") else "all states"
        st.caption(f"{int(status_data['total_orders'].sum()) if not status_data.empty else 0:,} orders in the selected purchase-month window · {status_scope_note}.")
with insight_col:
    with st.container(border=True):
        st.markdown("**Signals worth attention**")
        one_time_share = safe_pct(int(kpi["one_time_customers"]), int(kpi["delivered_customers"]))
        if not state_data.empty:
            state_total = float(state_data["recorded_payment_value"].sum())
            top_state = state_data.iloc[0]
            state_share = safe_pct(float(top_state["recorded_payment_value"]), state_total)
            state_title = f"{top_state['customer_state']} leads the selected state view"
            state_copy = f"{state_share:.1f}% of selected-state recorded payment value is associated with {top_state['customer_state']}."
        else:
            state_title, state_copy = "No state records in this filter", "Expand the state or date selection to restore the geographic ranking."
        if not category_data.empty:
            top_category = category_data.iloc[0]
            category_title = str(top_category["product_category"]).replace("_", " ").title()
            category_copy = f"Top selected category by delivered product-plus-freight value: R$ {float(top_category['item_plus_freight_value']):,.0f}."
        else:
            category_title, category_copy = "No category records in this filter", "Clear the category selection or widen the analysis period."
        insight_card("Customer retention", f"{one_time_share:.1f}% are one-time buyers", "Most shoppers made only one delivered purchase across the observed period. This is an observed behavior, not an explanation for why they did not return.", COLORS["coral"])
        st.markdown("<div style='height:9px'></div>", unsafe_allow_html=True)
        insight_card("Geography", state_title, state_copy, COLORS["blue"])
        st.markdown("<div style='height:9px'></div>", unsafe_allow_html=True)
        insight_card("Product mix", category_title, category_copy, COLORS["amber"])

section_heading("Data quality watchlist", "Flagged records are preserved, not silently altered")
dq = data["data_quality"]
for start in range(0, len(dq), 3):
    dq_cols = st.columns(3, gap="medium")
    for col, row in zip(dq_cols, dq.iloc[start:start + 3].itertuples()):
        with col:
            accent = COLORS["amber"] if row.severity == "Review" else COLORS["blue"]
            st.markdown(
                f"<div class='insight-card' style='min-height:118px;border-top:2px solid {accent}'>"
                f"<div class='insight-label'>{row.severity.upper()}</div>"
                f"<div style='font:800 24px Manrope;color:#F5F8FD;margin-top:7px'>{int(row.flagged_rows):,}</div>"
                f"<div class='insight-copy'>{row.issue}</div></div>",
                unsafe_allow_html=True,
            )
st.caption("The geolocation boundary check is an approximate Brazil bounding-box screen, not an official border test. Exact repeated geolocation entries were retained after investigation.")

page_footer()
