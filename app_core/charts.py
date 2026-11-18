from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app_core.theme import COLORS, chart_style


def empty_figure(message: str = "No data for the selected filters") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font={"color": COLORS["muted"], "size": 13},
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return chart_style(fig, 300)


def monthly_payments(frame: pd.DataFrame, payment_column: str = "delivered_recorded_payment_value") -> go.Figure:
    if frame.empty or payment_column not in frame:
        return empty_figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=frame["order_month"], y=frame[payment_column],
        mode="lines+markers", name="Recorded payments",
        line={"color": COLORS["teal"], "width": 3, "shape": "spline"},
        marker={"size": 6, "color": COLORS["teal"], "line": {"color": "#0B1728", "width": 1.5}},
        fill="tozeroy", fillcolor="rgba(70,216,193,.10)",
        hovertemplate="%{x|%b %Y}<br>R$ %{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(yaxis_title="Recorded payment value (R$)", xaxis_title=None, showlegend=False, hovermode="x unified")
    return chart_style(fig, 340)


def monthly_orders(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    fig = px.bar(
        frame, x="order_month", y="delivered_orders",
        labels={"order_month": "Purchase month", "delivered_orders": "Delivered orders"},
        color_discrete_sequence=[COLORS["blue"]],
    )
    fig.update_traces(
        marker={"line": {"width": 0}, "opacity": .88},
        hovertemplate="%{x|%b %Y}<br>Delivered orders: %{y:,}<extra></extra>",
    )
    fig.update_layout(xaxis_title=None, yaxis_title="Delivered orders")
    return chart_style(fig, 330)


def status_donut(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    palette = [COLORS["teal"], COLORS["blue"], COLORS["amber"], COLORS["purple"], COLORS["coral"], "#5BB8CC", "#94A3B8", "#6C7F9A"]
    fig = px.pie(frame, names="order_status", values="total_orders", hole=.70, color_discrete_sequence=palette)
    fig.update_traces(
        textposition="none",
        hovertemplate="%{label}<br>%{value:,} orders<br>%{percent}<extra></extra>",
        marker={"line": {"color": "#101E31", "width": 3}},
    )
    total = int(frame["total_orders"].sum())
    fig.add_annotation(text=f"<b>{total:,}</b><br><span style='font-size:10px;color:#95A7BD'>orders</span>", x=.5, y=.5, showarrow=False, font={"size": 23, "color": COLORS["text"]})
    fig.update_layout(legend={"orientation": "h", "y": -.14, "x": 0, "font": {"size": 10}})
    return chart_style(fig, 340)


def category_bar(frame: pd.DataFrame, value: str = "item_plus_freight_value", limit: int = 10) -> go.Figure:
    if frame.empty:
        return empty_figure()
    view = frame.nlargest(limit, value).sort_values(value)
    view = view.copy()
    view["display_category"] = view["product_category"].fillna("Unknown").astype(str).str.replace("_", " ").str.title()
    fig = px.bar(
        view, x=value, y="display_category", orientation="h",
        color=value, color_continuous_scale=[[0, "#286D79"], [.55, COLORS["teal"]], [1, COLORS["blue"]]],
        labels={value: "Product + freight value (R$)", "display_category": "Product category"},
    )
    fig.update_traces(hovertemplate="%{y}<br>Product + freight: R$ %{x:,.2f}<extra></extra>")
    fig.update_layout(coloraxis_showscale=False, yaxis_title=None, xaxis_title="Product + freight value (R$)")
    return chart_style(fig, max(330, 28 * len(view) + 70))


def state_map(frame: pd.DataFrame, geojson: dict | None, value: str = "recorded_payment_value") -> go.Figure:
    if frame.empty:
        return empty_figure()
    if geojson is None:
        return empty_figure("Brazil state boundary file could not be loaded. Check your internet connection.")
    fig = px.choropleth(
        frame,
        geojson=geojson,
        locations="customer_state",
        featureidkey="properties.sigla",
        color=value,
        color_continuous_scale=[[0, "#19334A"], [.35, "#216B78"], [.7, "#46D8C1"], [1, "#B7F1E6"]],
        hover_name="customer_state",
        hover_data={
            "recorded_payment_value": ":,.2f",
            "delivered_orders": ":,",
            "unique_shoppers_full_period": ":,",
            "customer_state": False,
        },
        labels={
            "recorded_payment_value": "Recorded payments (R$)",
            "delivered_orders": "Delivered orders",
            "unique_shoppers_full_period": "Unique shoppers (full history)",
        },
    )
    fig.update_geos(
        fitbounds="locations", visible=False,
        bgcolor="rgba(0,0,0,0)",
        showcountries=True, countrycolor="rgba(151,176,204,.25)",
    )
    fig.update_traces(marker_line_color="#B4C9D8", marker_line_width=.55)
    fig.update_layout(coloraxis_colorbar={"title": "R$", "tickfont": {"color": COLORS["muted"]}, "outlinewidth": 0})
    return chart_style(fig, 490)


def cohort_heatmap(frame: pd.DataFrame, max_month: int = 17) -> go.Figure:
    if frame.empty:
        return empty_figure()
    view = frame[frame["cohort_index"] <= max_month].copy()
    view["cohort_label"] = pd.to_datetime(view["cohort_month"]).dt.strftime("%b %Y")
    pivot = view.pivot(index="cohort_label", columns="cohort_index", values="retention_percentage")
    pivot = pivot.sort_index(key=lambda values: pd.to_datetime(values, format="%b %Y"))
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"M{int(value)}" for value in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0, "#14243A"], [.12, "#174E60"], [.42, "#228D8C"], [.72, "#46D8C1"], [1, "#D0F6EB"]],
        zmin=0, zmax=100,
        colorbar={"title": "Retention", "ticksuffix": "%", "outlinewidth": 0},
        hovertemplate="Cohort: %{y}<br>Age: %{x}<br>Retention: %{z:.2f}%<extra></extra>",
        xgap=2, ygap=2,
    ))
    fig.update_layout(xaxis_title="Months since first delivered purchase", yaxis_title=None, yaxis={"autorange": "reversed"})
    return chart_style(fig, max(430, len(pivot) * 24 + 100))
