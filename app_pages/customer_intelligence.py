from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_core.data import selected_filters
from app_core.page_utils import page_data, page_footer, page_hero
from app_core.theme import COLORS, PLOTLY_CONFIG, chart_style, format_brl, insight_card, metric_card, section_heading


data = page_data()
kpi = data["overview_kpis"].iloc[0]
rfm = data["rfm_segments"].copy().sort_values("customer_count", ascending=False)
frequency = data["customer_frequency"].copy()
types = data["customer_type_metrics"].copy()
filters = selected_filters()

page_hero(
    "CUSTOMER INTELLIGENCE  /  RFM & SHOPPER VALUE",
    "Know the customers behind the orders.",
    "Explore the one-time versus repeat customer split, purchase frequency and historical value segments. RFM metrics describe delivered-order history across the full observed dataset.",
)

one_time = types.loc[types.customer_type == "One-time customers"]
repeat = types.loc[types.customer_type == "Repeat customers"]
one_time_row = one_time.iloc[0] if not one_time.empty else None
repeat_row = repeat.iloc[0] if not repeat.empty else None
repeat_rate = float(kpi["repeat_customer_rate"])

section_heading("Customer base profile", "Full observed delivered-order history · not affected by the date slicer")
cols = st.columns(4)
with cols[0]: metric_card("Delivered shoppers", f"{int(kpi['delivered_customers']):,}", "Unique customer identity", "◉", COLORS["teal"], frequency.customer_count.tolist())
with cols[1]: metric_card("One-time shoppers", f"{int(kpi['one_time_customers']):,}", f"{100-repeat_rate:.2f}% of customer base", "1×", COLORS["amber"], [int(kpi["one_time_customers"]), int(kpi["one_time_customers"])])
with cols[2]: metric_card("Repeat shoppers", f"{int(kpi['repeat_customers']):,}", f"{repeat_rate:.2f}% of customer base", "↻", COLORS["purple"], [int(kpi["repeat_customers"]), int(kpi["repeat_customers"])])
with cols[3]: metric_card("Avg. delivered orders", f"{float(kpi['average_orders_per_customer']):.2f}", "Per unique delivered shopper", "▤", COLORS["blue"], frequency.frequency.tolist())

st.markdown(
    "<div class='callout'>The 3% repeat-customer share is calculated across the full delivered-order history. It is not the same measure as Month 1 cohort retention, which tests activity in the next calendar month.</div>",
    unsafe_allow_html=True,
)

section_heading("One-time vs repeat customer economics", "Recorded payment value; not profit, net revenue or customer lifetime value")
left, right = st.columns([1, 1.1], gap="large")
with left:
    with st.container(border=True):
        st.markdown("**Customer group comparison**")
        if not types.empty:
            fig = px.bar(
                types.melt(id_vars="customer_type", value_vars=["average_payment_per_customer", "average_payment_per_paid_order"], var_name="metric", value_name="amount"),
                x="customer_type", y="amount", color="metric", barmode="group",
                color_discrete_sequence=[COLORS["teal"], COLORS["blue"]],
                labels={"customer_type":"Customer type", "amount":"Recorded payment value (R$)", "metric":"Measure"},
            )
            fig.update_traces(hovertemplate="%{x}<br>R$ %{y:,.2f}<extra></extra>")
            fig.update_layout(legend={"orientation":"h","y":-0.2}, xaxis_title=None, yaxis_title="R$")
            st.plotly_chart(chart_style(fig, 350), use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("Customer group comparison is unavailable.")
with right:
    with st.container(border=True):
        st.markdown("**What the comparison says**")
        if one_time_row is not None and repeat_row is not None:
            avg_customer_ratio = float(repeat_row.average_payment_per_customer) / max(float(one_time_row.average_payment_per_customer), 1)
            order_diff = (float(repeat_row.average_payment_per_paid_order) / max(float(one_time_row.average_payment_per_paid_order), 1) - 1) * 100
            insight_card("Average payment per customer", f"{avg_customer_ratio:.2f}× higher for repeat buyers", f"One-time: R$ {float(one_time_row.average_payment_per_customer):,.2f} · Repeat: R$ {float(repeat_row.average_payment_per_customer):,.2f}", COLORS["teal"])
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            insight_card("Average payment per paid order", f"{abs(order_diff):.1f}% {'higher' if order_diff > 0 else 'lower'} for repeat buyers", f"One-time: R$ {float(one_time_row.average_payment_per_paid_order):,.2f} · Repeat: R$ {float(repeat_row.average_payment_per_paid_order):,.2f}", COLORS["amber"])
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            insight_card("Interpretation", "Purchase frequency matters", "Repeat customers accumulate more recorded payment value per customer because they place more delivered orders. Their typical paid order is not necessarily larger.", COLORS["purple"])

section_heading("Purchase frequency distribution", "Long-tail customers are shown in the full table; chart focuses on the readable range")
with st.container(border=True):
    frequency_plot = frequency.copy()
    frequency_plot["frequency_band"] = frequency_plot.frequency.astype(int).astype(str)
    frequency_plot.loc[frequency_plot.frequency >= 6, "frequency_band"] = "6+"
    frequency_banded = frequency_plot.groupby("frequency_band", as_index=False).agg(
        customer_count=("customer_count", "sum"),
        total_monetary=("total_monetary", "sum"),
    )
    band_order = ["1", "2", "3", "4", "5", "6+"]
    frequency_banded["frequency_band"] = pd.Categorical(frequency_banded.frequency_band, categories=band_order, ordered=True)
    frequency_banded = frequency_banded.sort_values("frequency_band")
    fig = px.bar(
        frequency_banded, x="frequency_band", y="customer_count",
        color="frequency_band", color_discrete_sequence=[COLORS["teal"], COLORS["blue"], COLORS["purple"], COLORS["amber"], COLORS["coral"], "#7890A8"],
        labels={"frequency_band":"Delivered orders per shopper", "customer_count":"Customers"},
    )
    fig.update_traces(hovertemplate="Frequency: %{x}<br>Customers: %{y:,}<extra></extra>")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Customers")
    st.plotly_chart(chart_style(fig, 330), use_container_width=True, config=PLOTLY_CONFIG)
    with st.expander("Inspect exact frequency counts"):
        st.dataframe(frequency, use_container_width=True, hide_index=True, column_config={
            "frequency": st.column_config.NumberColumn("Delivered orders", format="%d"),
            "customer_count": st.column_config.NumberColumn("Customers", format="%d"),
            "customer_percentage": st.column_config.NumberColumn("Customer share", format="%.2f%%"),
            "average_monetary": st.column_config.NumberColumn("Average recorded payment", format="R$ %.2f"),
            "total_monetary": st.column_config.NumberColumn("Total recorded payment", format="R$ %.2f"),
        })

section_heading("RFM segment landscape", "Rule-based historical segmentation · eight segments")
left, right = st.columns([1.05, .95], gap="large")
with left:
    with st.container(border=True):
        st.markdown("**Customer count by segment**")
        selected_segment = st.selectbox("Highlight a segment", ["All segments"] + rfm.customer_segment.tolist(), key="rfm_segment_focus")
        view = rfm.copy()
        view["focus"] = (
            view.customer_segment.eq(selected_segment).map({True: "Selected segment", False: "Other segments"})
            if selected_segment != "All segments"
            else "All segments"
        )
        fig = px.bar(
            view.sort_values("customer_count"), x="customer_count", y="customer_segment", orientation="h",
            color="focus", color_discrete_map={
                "Selected segment": COLORS["teal"],
                "Other segments": "#40566F",
                "All segments": COLORS["blue"],
            },
            labels={"customer_count":"Customers", "customer_segment":"RFM segment", "focus":"Selection"},
        )
        fig.update_traces(hovertemplate="%{y}<br>Customers: %{x:,}<extra></extra>")
        fig.update_layout(showlegend=False, xaxis_title="Customers", yaxis_title=None)
        st.plotly_chart(chart_style(fig, 390), use_container_width=True, config=PLOTLY_CONFIG)
with right:
    with st.container(border=True):
        st.markdown("**Segment value map**")
        fig = px.treemap(
            rfm, path=["customer_segment"], values="customer_count", color="average_monetary",
            color_continuous_scale=[[0, "#17354A"], [.5, COLORS["teal"]], [1, COLORS["amber"]]],
            hover_data={"customer_count":":,", "average_monetary":":.2f", "total_monetary":":.2f"},
        )
        fig.update_layout(coloraxis_colorbar={"title":"Avg. value (R$)"})
        st.plotly_chart(chart_style(fig, 390), use_container_width=True, config=PLOTLY_CONFIG)

with st.container(border=True):
    st.markdown("**RFM segment detail**")
    st.dataframe(rfm, use_container_width=True, hide_index=True, column_config={
        "customer_segment": st.column_config.TextColumn("Customer segment"),
        "customer_count": st.column_config.NumberColumn("Customers", format="%d"),
        "average_recency": st.column_config.NumberColumn("Avg. recency (days)", format="%.1f"),
        "average_frequency": st.column_config.NumberColumn("Avg. frequency", format="%.2f"),
        "average_monetary": st.column_config.NumberColumn("Avg. monetary", format="R$ %.2f"),
        "total_monetary": st.column_config.NumberColumn("Total monetary", format="R$ %.2f"),
    })

st.caption("RFM segment rules and percentile thresholds are defined in sql/03_rfm_segmentation.sql. Segment labels reflect historical behavior and should not be interpreted as predictive scores.")
page_footer()
