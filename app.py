from __future__ import annotations

import pandas as pd
import streamlit as st

from app_core.data import load_brazil_geojson, load_dashboard_data, load_manifest, month_options
from app_core.theme import apply_theme, brand_lockup

st.set_page_config(
    page_title="E-commerce IQ | Intelligence Studio",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/rahul-patel74/ecommerce-customer-intelligence",
        "Report a bug": "https://github.com/rahul-patel74/ecommerce-customer-intelligence/issues",
        "About": "E-commerce IQ | Customer Intelligence & Retention Analytics",
    },
)
apply_theme()

pages = [
    st.Page("app_pages/overview.py", title="Executive overview", icon=":material/space_dashboard:", default=True),
    st.Page("app_pages/sales_operations.py", title="Sales & operations", icon=":material/monitoring:"),
    st.Page("app_pages/customer_intelligence.py", title="Customer intelligence", icon=":material/groups:"),
    st.Page("app_pages/retention_analytics.py", title="Retention analytics", icon=":material/repeat:"),
    st.Page("app_pages/executive_report.py", title="Reports & exports", icon=":material/description:"),
    st.Page("app_pages/data_sources.py", title="Data & settings", icon=":material/database:"),
]
page = st.navigation(pages, position="sidebar")

# Keep page navigation in Streamlit's native sidebar. A custom horizontal
# page-link row could be clipped beneath the Streamlit header on some screens.

try:
    dashboard_data = load_dashboard_data()
except Exception as error:
    with st.container(border=True):
        st.error("The analytics snapshot could not be loaded.")
        st.write(str(error))
        st.markdown(
            "Run `python scripts/export_dashboard_data.py` from the project root, "
            "then restart the app. Check the Data & settings page after the first successful export."
        )
    st.stop()

manifest = load_manifest()
months = month_options(dashboard_data)
month_labels = [month.strftime("%b %Y") for month in months]

state_options = sorted(
    dashboard_data["state_performance"]["customer_state"].dropna().astype(str).unique()
)
category_options = sorted(
    dashboard_data["category_performance"]["product_category"].dropna().astype(str).unique()
)

# Keep the same range-valued select_slider configuration that worked in the
# first dashboard build. The explicit tuple in `value` is important: it tells
# Streamlit to instantiate a two-handle range slider rather than infer a
# single-value slider from an absent/default widget value. Use a fresh key to
# discard state left behind by previous experimental slider implementations.
PERIOD_WIDGET_KEY = "global_period_range_v3"
PERIOD_DEFAULT = (month_labels[0], month_labels[-1]) if month_labels else None


def sanitize_multiselect_state(key: str, options: list[str]) -> None:
    current = st.session_state.get(key, [])
    if not isinstance(current, list):
        current = []
    valid_values = [value for value in current if value in options]
    if current != valid_values:
        st.session_state[key] = valid_values


sanitize_multiselect_state("global_state_filter", state_options)
sanitize_multiselect_state("global_category_filter", category_options)


def reset_global_filters() -> None:
    """Reset widget state in a callback before the next script run."""
    if PERIOD_DEFAULT is not None:
        st.session_state[PERIOD_WIDGET_KEY] = PERIOD_DEFAULT
    st.session_state["global_state_filter"] = []
    st.session_state["global_category_filter"] = []


with st.sidebar:
    brand_lockup(compact=True)
    st.markdown(
        '<div class="small-badge"><span class="status-dot"></span>ANALYTICS WORKSPACE</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("#### Global filters")
    st.caption(
        "Time filters affect time-series pages. State and category filters apply to their matching analyses."
    )

    if months:
        selected_range = st.select_slider(
            "Analysis period",
            options=month_labels,
            value=PERIOD_DEFAULT,
            key=PERIOD_WIDGET_KEY,
            help="Drag either handle to choose the first and last month.",
        )

        # The explicit tuple value above preserves the original two-handle
        # behavior. Read the widget result locally; never write to its key
        # during this script run.
        if not isinstance(selected_range, (tuple, list)) or len(selected_range) != 2:
            selected_range = PERIOD_DEFAULT

        start_label, end_label = map(str, selected_range)
        if start_label not in month_labels or end_label not in month_labels:
            start_label, end_label = PERIOD_DEFAULT

        start_idx = month_labels.index(start_label)
        end_idx = month_labels.index(end_label)
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx

        start_month = months[start_idx]
        end_month = months[end_idx]
        st.caption(f"Selected: **{month_labels[start_idx]} – {month_labels[end_idx]}**")
    else:
        start_month = None
        end_month = None

    selected_states = st.multiselect(
        "Focus states",
        options=state_options,
        help="Leave empty to include all states. Applies to state-level and state-aware monthly views.",
        key="global_state_filter",
    )
    selected_categories = st.multiselect(
        "Focus product categories",
        options=category_options,
        help="Leave empty to include all categories. Applies to category-level analyses.",
        key="global_category_filter",
    )

    st.session_state["dashboard_filters"] = {
        "date_start": start_month.date() if start_month is not None else None,
        "date_end": end_month.date() if end_month is not None else None,
        "states": selected_states,
        "categories": selected_categories,
    }

    if st.button(
        "Reload dashboard snapshot",
        use_container_width=True,
        help="Reload the curated CSV extracts from app_data. This does not connect to MySQL.",
    ):
        load_dashboard_data.clear()
        load_manifest.clear()
        load_brazil_geojson.clear()
        st.rerun()

    st.button(
        "Reset all filters",
        use_container_width=True,
        on_click=reset_global_filters,
        key="reset_global_filters_button",
        help="Restore the full date range and clear all selected states and categories.",
    )

    st.divider()
    generated_at = manifest.get("generated_at_utc")
    if generated_at:
        try:
            generated_label = (
                pd.Timestamp(generated_at)
                .tz_convert("Asia/Kolkata")
                .strftime("%d %b %Y, %I:%M %p IST")
            )
        except (TypeError, ValueError):
            generated_label = str(generated_at)
    else:
        generated_label = "Manifest not available"

    st.caption("DATA SNAPSHOT")
    st.markdown(f"**{generated_label}**")
    st.caption("Olist Brazilian E-Commerce · 2016–2018")
    st.markdown(
        "<div class='page-foot'>Built for analytical exploration<br/>Python · MySQL · Streamlit · Plotly</div>",
        unsafe_allow_html=True,
    )

page.run()
