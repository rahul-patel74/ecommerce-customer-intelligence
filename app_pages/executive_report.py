from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from app_core.analytics import first_month_retention, monthly_scope, category_scope, state_scope
from app_core.data import DATA_DIR, DATA_FILES, load_dashboard_data, selected_filters, load_manifest
from app_core.page_utils import page_data, page_footer, page_hero
from app_core.reporting import build_filtered_extract_bundle, build_html_report, build_pdf_report
from app_core.sharing import get_public_app_url, snapshot_metadata
from app_core.theme import section_heading


data = page_data()
filters = selected_filters()
manifest = load_manifest()
snapshot = snapshot_metadata(manifest)
monthly = monthly_scope(data)
categories = category_scope(data)
states = state_scope(data)
kpi = data["overview_kpis"].iloc[0]
retained, eligible, retention_rate = first_month_retention(data["cohort_retention"])

page_hero(
    "REPORTING  /  EXECUTIVE BRIEF & DATA EXPORTS",
    "Turn analysis into a shareable report.",
    "Generate a dated executive brief using the active dashboard filters, then download the filtered analytical extracts.",
)

period_orders = int(monthly.delivered_orders.sum()) if not monthly.empty else 0
period_payment = float(monthly.delivered_recorded_payment_value.sum()) if not monthly.empty else 0
period_label = "Full available period"
if filters.get("date_start") and filters.get("date_end"):
    period_label = (
        f"{pd.Timestamp(filters['date_start']):%b %Y} - "
        f"{pd.Timestamp(filters['date_end']):%b %Y}"
    )
state_label = ", ".join(filters.get("states") or []) or "All states"
category_label = ", ".join(filters.get("categories") or []) or "All categories"
snapshot_label = (
    snapshot["ist"].strftime("%d %b %Y, %I:%M %p IST")
    if snapshot["available"] else "Not recorded"
)

section_heading("Active report scope", "These are the filters used for the reports generated below")
cols = st.columns(3)
with cols[0]:
    st.metric("Analysis period", period_label)
with cols[1]:
    st.metric("State scope", f"{len(filters.get('states') or [])} selected" if filters.get("states") else "All states")
with cols[2]:
    st.metric("Category scope", f"{len(filters.get('categories') or [])} selected" if filters.get("categories") else "All categories")
st.caption(f"States: {state_label}  ·  Categories: {category_label}")

section_heading("Report preview", "Filtered operating measures are separated from full-history customer measures")
cols = st.columns(4)
with cols[0]:
    st.metric("Delivered customers · full history", f"{int(kpi.delivered_customers):,}")
with cols[1]:
    st.metric("Repeat customer rate · full history", f"{float(kpi.repeat_customer_rate):.2f}%")
with cols[2]:
    st.metric("Delivered orders · selected scope", f"{period_orders:,}")
with cols[3]:
    st.metric("Delivered payments · selected scope", f"R$ {period_payment:,.0f}")

st.markdown(
    "<div class='callout good-callout'>PDF and HTML reports use the active date, state and category filters wherever the underlying aggregate supports those dimensions. RFM, cohort retention, payment methods and data-quality findings remain full-history or full-snapshot context and are labelled as such.</div>",
    unsafe_allow_html=True,
)

section_heading("Download executive report", "PDF for sharing · HTML for a responsive, self-contained brief")
try:
    pdf_bytes = build_pdf_report(data)
    html_bytes = build_html_report(data)
    filtered_zip = build_filtered_extract_bundle(data)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

    a, b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            st.markdown("**Executive PDF**")
            st.caption("Filtered monthly, order-status, category and state results, plus explicitly labelled full-history context.")
            st.download_button(
                "↓  Download PDF report",
                data=pdf_bytes,
                file_name=f"ecommerce_iq_filtered_executive_brief_{timestamp}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
    with b:
        with st.container(border=True):
            st.markdown("**Shareable HTML brief**")
            st.caption("Self-contained HTML snapshot with the selected filter scope and a live-app link when configured.")
            st.download_button(
                "↓  Download HTML report",
                data=html_bytes,
                file_name=f"ecommerce_iq_filtered_executive_brief_{timestamp}.html",
                mime="text/html",
                use_container_width=True,
            )

    with st.container(border=True):
        st.markdown("**Filtered data bundle**")
        st.caption("ZIP containing date/state/category-filtered CSVs where supported, plus separately named full-history context files and a filter-context manifest.")
        st.download_button(
            "↓  Download filtered CSV bundle",
            data=filtered_zip,
            file_name=f"ecommerce_iq_filtered_data_{timestamp}.zip",
            mime="application/zip",
            use_container_width=True,
        )
except Exception as error:
    st.error(f"Report generation failed: {error}")
    st.exception(error)

section_heading("Download dashboard snapshots", "These are the complete curated export snapshots, not filter-specific extracts")
with st.container(border=True):
    dataset_labels = {
        "overview_kpis": "Overview KPI snapshot",
        "monthly_performance": "Monthly business performance",
        "order_status": "Order status distribution",
        "monthly_order_status": "Monthly order status",
        "monthly_state_order_status": "Monthly state + order status",
        "category_performance": "Category performance",
        "monthly_category_performance": "Monthly category performance",
        "rfm_segments": "RFM segment summary",
        "customer_frequency": "Customer frequency distribution",
        "customer_type_metrics": "One-time vs repeat customers",
        "cohort_retention": "Cohort retention matrix (long format)",
        "state_performance": "State performance",
        "monthly_state_performance": "Monthly state performance",
        "payment_methods": "Payment methods",
        "delivery_performance": "Delivery performance",
        "data_quality": "Data quality flags",
    }
    keys = list(dataset_labels)
    for start in range(0, len(keys), 3):
        cols = st.columns(3)
        for col, key in zip(cols, keys[start:start + 3]):
            frame = data[key]
            filename = DATA_FILES[key]
            with col:
                st.markdown(f"**{dataset_labels[key]}**")
                st.caption(f"{len(frame):,} rows · {len(frame.columns)} columns · full snapshot")
                st.download_button(
                    "Download full CSV",
                    data=(DATA_DIR / filename).read_bytes(),
                    file_name=filename,
                    mime="text/csv",
                    key=f"download_full_{key}",
                    use_container_width=True,
                )

section_heading("Share the live application", "Configure the public URL once after deploying on Streamlit Community Cloud")
public_url = get_public_app_url()
with st.container(border=True):
    if public_url:
        st.success("Public application URL configured")
        st.link_button("↗  Open live E-commerce IQ", public_url, use_container_width=True)
        st.code(public_url, language="text")
        st.caption("The configured URL is included in newly generated HTML and PDF reports.")
    else:
        st.info("No public application URL is configured yet. This is expected before deployment.")
        st.markdown("**After deployment:** open your Streamlit Community Cloud app settings and add this to the Secrets field:")
        st.code('STREAMLIT_APP_URL = "https://your-app-name.streamlit.app"', language="toml")
        st.caption("For local preview, add STREAMLIT_APP_URL=https://your-app-name.streamlit.app to your local .env file. The URL is never guessed from localhost.")

section_heading("Data snapshot & refresh", "The timestamp identifies when the committed aggregate CSV extracts were last generated")
left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown("**Last successful data export**")
        st.metric("Snapshot generated", snapshot_label)
        st.metric("Snapshot age", snapshot["age_label"])
        st.caption("This is the CSV export time, not the date of the latest underlying transaction. The Olist source data remains historical (2016–2018).")
with right:
    with st.container(border=True):
        st.markdown("**Refresh sequence**")
        st.code("python scripts/export_dashboard_data.py\npython scripts/validate_dashboard_data.py", language="bash")
        st.caption("Run in the local MySQL environment, confirm the validation gate passes, then commit the refreshed aggregate snapshots and redeploy.")

st.caption("Recorded payment value is not profit. Category values include item price and freight. Full-history RFM and cohort metrics are not recalculated by the global filters.")
page_footer()
