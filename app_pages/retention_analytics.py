from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_core.analytics import first_month_retention, weighted_cohort_retention
from app_core.charts import cohort_heatmap, empty_figure
from app_core.page_utils import page_data, page_footer, page_hero
from app_core.theme import COLORS, PLOTLY_CONFIG, chart_style, insight_card, metric_card, section_heading


data = page_data()
cohort = data["cohort_retention"].copy()
weighted = weighted_cohort_retention(cohort)
retained_m1, eligible_m1, rate_m1 = first_month_retention(cohort)
cohort_months = sorted(pd.to_datetime(cohort.cohort_month).dropna().unique())

page_hero(
    "RETENTION ANALYTICS  /  MONTHLY COHORTS",
    "See when shoppers come back.",
    "Compare acquisition-month cohorts, track the share that makes another delivered purchase and inspect how retention evolves as cohorts age.",
    ["Delivered orders only", "Calendar-month activity", "Weighted across eligible cohorts"],
)

section_heading("Retention scorecard", "Month 1 is the first full calendar month after the customer's first delivered purchase")
st.caption("Cohort metrics use the complete historical delivered-order dataset. The global date, state and category slicers do not recalculate the cohort matrix.")
cols = st.columns(4)
with cols[0]: metric_card("Month 1 retention", f"{rate_m1:.2f}%", f"{retained_m1:,} returned of {eligible_m1:,} eligible", "↻", COLORS["coral"], weighted.retention_percentage.head(12).tolist())
with cols[1]: metric_card("Cohorts analyzed", f"{len(cohort_months)}", "Monthly first-purchase cohorts", "▦", COLORS["teal"], [len(cohort_months)] * 4)
with cols[2]: metric_card("Cohort-month cells", f"{len(cohort):,}", "Observed months plus zero-activity months", "▤", COLORS["blue"], [len(cohort)] * 4)
with cols[3]: metric_card("Month 1 returners", f"{retained_m1:,}", "Across all 22 eligible cohorts", "◉", COLORS["amber"], [retained_m1] * 4)

st.markdown(
    "<div class='callout'>Cohort retention is not the same as the 3% repeat-customer share. The 3% figure asks whether a shopper made more than one delivered purchase anywhere in the observed history. Month 1 asks whether a shopper returned in the next calendar month.</div>",
    unsafe_allow_html=True,
)

section_heading("Cohort retention heatmap", "Rows are acquisition cohorts; columns are months since first delivered purchase")
with st.container(border=True):
    max_available = int(cohort.cohort_index.max()) if not cohort.empty else 0
    max_month = st.slider("Show cohort age through month", min_value=1, max_value=max(1, max_available), value=min(17, max(1, max_available)), key="retention_max_age")
    st.plotly_chart(cohort_heatmap(cohort, max_month=max_month), use_container_width=True, config=PLOTLY_CONFIG)
    st.caption("Month 0 is 100% by definition. Blank future months are not included; observed zero-return months remain visible as 0%.")

section_heading("Weighted retention curve", "Retained customers divided by the combined size of cohorts eligible to be observed at each cohort age")
left, right = st.columns([1.1, .9], gap="large")
with left:
    with st.container(border=True):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=weighted.cohort_index, y=weighted.retention_percentage,
            mode="lines+markers", line={"color": COLORS["teal"], "width": 3, "shape": "spline"},
            marker={"size": 7, "color": COLORS["teal"]},
            fill="tozeroy", fillcolor="rgba(70,216,193,.09)",
            customdata=weighted[["eligible_customers", "retained_customers", "cohorts_observed"]].to_numpy(),
            hovertemplate="Cohort age: M%{x}<br>Retention: %{y:.2f}%<br>Retained: %{customdata[1]:,}<br>Eligible: %{customdata[0]:,}<br>Cohorts: %{customdata[2]}<extra></extra>",
        ))
        fig.update_layout(xaxis_title="Months since first purchase", yaxis_title="Weighted retention (%)", xaxis={"dtick":1})
        st.plotly_chart(chart_style(fig, 370), use_container_width=True, config=PLOTLY_CONFIG)
with right:
    with st.container(border=True):
        st.markdown("**Cohort-age diagnostics**")
        max_age = int(weighted.cohort_index.max()) if not weighted.empty else 0
        age = st.select_slider("Inspect cohort age", options=list(range(0, max_age + 1)), value=min(1, max_age), key="cohort_age_detail")
        row = weighted.loc[weighted.cohort_index == age]
        if not row.empty:
            selected = row.iloc[0]
            st.metric("Weighted retention", f"{float(selected.retention_percentage):.2f}%")
            st.metric("Retained shoppers", f"{int(selected.retained_customers):,}")
            st.metric("Eligible customers", f"{int(selected.eligible_customers):,}")
            st.metric("Cohorts contributing", f"{int(selected.cohorts_observed):,}")
        st.markdown("<div class='callout'>Later cohort ages have fewer eligible cohorts and smaller denominators. Interpret those tail percentages cautiously.</div>", unsafe_allow_html=True)

section_heading("Inspect an individual cohort")
with st.container(border=True):
    cohort_lookup = {pd.Timestamp(value).strftime("%B %Y"): pd.Timestamp(value) for value in cohort_months}
    selected_label = st.selectbox("Acquisition cohort", list(cohort_lookup), index=0 if cohort_lookup else None, key="selected_retention_cohort")
    if selected_label:
        selected_month = cohort_lookup[selected_label]
        selected = cohort[cohort.cohort_month == selected_month].sort_values("cohort_index")
        if not selected.empty:
            fig = go.Figure(go.Scatter(
                x=selected.cohort_index, y=selected.retention_percentage,
                mode="lines+markers", line={"color": COLORS["blue"], "width": 3},
                marker={"size": 7},
                customdata=selected[["retained_customers", "cohort_size"]].to_numpy(),
                hovertemplate="Month %{x}<br>Retention: %{y:.2f}%<br>Retained: %{customdata[0]:,}<br>Cohort size: %{customdata[1]:,}<extra></extra>",
            ))
            fig.update_layout(xaxis_title="Cohort age (months)", yaxis_title="Retention (%)")
            st.plotly_chart(chart_style(fig, 300), use_container_width=True, config=PLOTLY_CONFIG)
            st.dataframe(selected, use_container_width=True, hide_index=True)

with st.expander("Methodology and interpretation"):
    st.markdown(
        """
        - Cohort assignment uses each shopper's first **delivered** purchase month.
        - Shopper identity uses `customer_unique_id`, not the order-specific `customer_id`.
        - Monthly activity means at least one delivered purchase in a calendar month.
        - A shopper can skip a month and return later; this is monthly activity retention, not continuous retention.
        - Weighted retention sums retained shoppers and eligible cohort sizes at each cohort age.
        - Months beyond the final observed activity month are not fabricated or displayed.
        """
    )
page_footer()
