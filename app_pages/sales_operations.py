from __future__ import annotations

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_core.analytics import monthly_scope, category_scope, state_scope, status_scope
from app_core.charts import category_bar, empty_figure, monthly_orders, monthly_payments, status_donut
from app_core.data import filter_by_period, selected_filters
from app_core.page_utils import page_data, page_footer, page_hero
from app_core.theme import COLORS, PLOTLY_CONFIG, chart_style, format_brl, metric_card, section_heading


data = page_data()
monthly = monthly_scope(data)
period_status = status_scope(data)
categories = category_scope(data)
states = state_scope(data)
filters = selected_filters()
delivery = filter_by_period(data["delivery_performance"])

page_hero(
    "OPERATIONS  /  SALES & FULFILLMENT",
    "Follow the order journey.",
    "Explore purchase activity, payment mix, product-category contribution, delivery speed and service reliability across the selected analysis window.",
)

total_orders = int(period_status.total_orders.sum()) if not period_status.empty else 0
delivered_orders = int(period_status.loc[period_status.order_status == "delivered", "total_orders"].sum()) if not period_status.empty else 0
delivered_rate = delivered_orders / total_orders * 100 if total_orders else 0
payment_value = float(monthly.delivered_recorded_payment_value.sum()) if not monthly.empty else 0
if not delivery.empty:
    delivery_weights = delivery["delivered_orders_with_dates"].fillna(0).clip(lower=0)
    if float(delivery_weights.sum()) > 0:
        avg_delivery = float(np.average(delivery["average_delivery_days"], weights=delivery_weights))
        on_time = float(np.average(delivery["on_time_delivery_rate"], weights=delivery_weights))
    else:
        avg_delivery = 0.0
        on_time = 0.0
else:
    avg_delivery = 0.0
    on_time = 0.0

section_heading("Operational scorecard", "Period-filtered order and fulfillment indicators")
cols = st.columns(4)
with cols[0]: metric_card("Orders in scope", f"{total_orders:,}", "All statuses · selected months", "▤", COLORS["blue"], monthly.total_orders.tail(12).tolist() if not monthly.empty else [])
with cols[1]: metric_card("Delivered share", f"{delivered_rate:.1f}%", f"{delivered_orders:,} delivered orders", "✓", COLORS["teal"], period_status.total_orders.tail(6).tolist() if len(period_status) > 1 else [])
with cols[2]: metric_card("Delivered payment value", format_brl(payment_value, compact=True), "Recorded payment · delivered orders", "↗", COLORS["amber"], monthly.delivered_recorded_payment_value.tail(12).tolist() if not monthly.empty else [])
with cols[3]: metric_card("Avg. delivery time", f"{avg_delivery:.1f} days" if avg_delivery else "N/A", f"{on_time:.1f}% average on-time rate" if not delivery.empty else "No complete delivery dates", "◷", COLORS["purple"], delivery.average_delivery_days.tail(12).tolist() if not delivery.empty else [])

section_heading("Demand and payment trends")
a, b = st.columns(2, gap="large")
with a:
    with st.container(border=True):
        st.markdown("**Monthly orders by status**")
        if filters.get("states"):
            status_monthly = filter_by_period(data["monthly_state_order_status"])
            status_monthly = status_monthly[status_monthly.customer_state.isin(filters["states"])]
        else:
            status_monthly = filter_by_period(data["monthly_order_status"])
        if not status_monthly.empty:
            available_statuses = sorted(status_monthly["order_status"].dropna().unique().tolist())
            chosen_statuses = st.multiselect(
                "Order statuses",
                options=available_statuses,
                default=available_statuses,
                key="sales_order_status_filter",
                help="Filter only this monthly order-status chart. The scorecard above keeps all statuses in scope.",
            )
            status_monthly = status_monthly[status_monthly["order_status"].isin(chosen_statuses)]
            if status_monthly.empty:
                st.info("Select at least one order status to display the monthly breakdown.")
            else:
                pivot = status_monthly.pivot_table(index="order_month", columns="order_status", values="total_orders", aggfunc="sum", fill_value=0).sort_index()
                fig = go.Figure()
                palette = [COLORS["teal"], COLORS["blue"], COLORS["amber"], COLORS["purple"], COLORS["coral"], "#5BB8CC", "#91A5BA", "#6E819B"]
                for color, status_name in zip(palette, pivot.columns):
                    fig.add_trace(go.Bar(x=pivot.index, y=pivot[status_name], name=status_name.title(), marker_color=color))
                fig.update_layout(barmode="stack", xaxis_title=None, yaxis_title="Orders", legend={"orientation": "h", "y": -0.23})
                st.plotly_chart(chart_style(fig, 370), use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.plotly_chart(empty_figure(), use_container_width=True)
with b:
    with st.container(border=True):
        st.markdown("**Delivered recorded payment trend**")
        st.plotly_chart(monthly_payments(monthly), use_container_width=True, config=PLOTLY_CONFIG)
        st.caption("Payment value is aggregated from payment records linked to delivered orders; it is not profit.")

section_heading("Payments and fulfillment")
a, b = st.columns([.92, 1.08], gap="large")
with a:
    with st.container(border=True):
        st.markdown("**Payment method mix**")
        payment = data["payment_methods"].copy().sort_values("recorded_payment_value", ascending=False)
        fig = px.pie(payment, names="payment_type", values="recorded_payment_value", hole=.68,
                     color_discrete_sequence=[COLORS["teal"], COLORS["blue"], COLORS["purple"], COLORS["amber"], COLORS["coral"]])
        fig.update_traces(textinfo="none", hovertemplate="%{label}<br>R$ %{value:,.2f}<br>%{percent}<extra></extra>")
        fig.add_annotation(text=f"<b>R$ {payment.recorded_payment_value.sum()/1_000_000:.2f}M</b><br><span style='font-size:10px;color:#95A7BD'>payment value</span>", showarrow=False, x=.5, y=.5, font={"size":18,"color":COLORS["text"]})
        fig.update_layout(legend={"orientation":"h","y":-.16})
        st.plotly_chart(chart_style(fig, 350), use_container_width=True, config=PLOTLY_CONFIG)
        st.caption("Payment methods cover all order statuses and the full observed period; date and state slicers do not alter this extract.")
with b:
    with st.container(border=True):
        st.markdown("**Delivery reliability by month**")
        if not delivery.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=delivery.order_month, y=delivery.average_delivery_days, name="Average delivery days", mode="lines+markers", line={"color": COLORS["blue"], "width": 3}, yaxis="y"))
            fig.add_trace(go.Scatter(x=delivery.order_month, y=delivery.on_time_delivery_rate, name="On-time rate", mode="lines+markers", line={"color": COLORS["teal"], "width": 2.5}, yaxis="y2"))
            fig.update_layout(
                yaxis={"title":"Average days", "gridcolor":"rgba(151,176,204,.09)"},
                yaxis2={"title":"On-time rate (%)", "overlaying":"y", "side":"right", "range":[0,105], "showgrid":False},
                xaxis_title=None, legend={"orientation":"h","y":-0.2},
            )
            st.plotly_chart(chart_style(fig, 350), use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("No delivered orders with complete delivery and estimated dates for this period.")
        st.caption("On-time means the delivered timestamp is on or before the estimated delivery timestamp. This monthly extract covers all states; the date filter applies, but the state filter does not.")

section_heading("Product category performance", "Delivered order items only; amounts include product price and freight")
with st.container(border=True):
    top_n = st.select_slider("Show categories", options=[5, 10, 15, 20], value=10, key="sales_top_categories")
    st.plotly_chart(category_bar(categories, limit=top_n), use_container_width=True, config=PLOTLY_CONFIG)
    if not categories.empty:
        detail = categories.copy()
        detail["product_category"] = detail.product_category.astype(str).str.replace("_", " ").str.title()
        st.dataframe(detail, use_container_width=True, hide_index=True, column_config={
            "product_category": st.column_config.TextColumn("Product category"),
            "total_orders": st.column_config.NumberColumn("Orders", format="%d"),
            "order_item_lines": st.column_config.NumberColumn("Item lines", format="%d"),
            "product_value": st.column_config.NumberColumn("Product value", format="R$ %.2f"),
            "freight_value": st.column_config.NumberColumn("Freight", format="R$ %.2f"),
            "item_plus_freight_value": st.column_config.NumberColumn("Product + freight", format="R$ %.2f"),
        })
    else:
        st.info("No category records match the selected filters.")

section_heading("State scorecard")
with st.container(border=True):
    if not states.empty:
        st.dataframe(states, use_container_width=True, hide_index=True, column_config={
            "customer_state": st.column_config.TextColumn("State", help="Brazilian state abbreviation"),
            "delivered_orders": st.column_config.NumberColumn("Delivered orders", format="%d"),
            "unique_shoppers_full_period": st.column_config.NumberColumn("Unique shoppers · full history", format="%d"),
            "recorded_payment_value": st.column_config.NumberColumn("Recorded payments", format="R$ %.2f"),
        })
    else:
        st.info("No state records match the current filters.")
    st.caption("Delivered orders and recorded payments respond to the selected date window. Unique shopper counts are full-history distinct counts; the same shopper can appear in more than one state across customer records.")

page_footer()
