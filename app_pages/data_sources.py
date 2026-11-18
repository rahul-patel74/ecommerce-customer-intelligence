from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from app_core.data import ASSETS_DIR, DATA_DIR, DATA_FILES, load_dashboard_data, load_manifest
from app_core.page_utils import page_footer, page_hero
from app_core.sharing import get_public_app_url, snapshot_metadata
from app_core.theme import section_heading


data = load_dashboard_data()
manifest = load_manifest()
snapshot = snapshot_metadata(manifest)
public_url = get_public_app_url()

page_hero(
    "PLATFORM  /  DATA SOURCES & SETTINGS",
    "Know what powers every number.",
    "Inspect the extract snapshot, dataset grain, data-quality handling, deployment URL, refresh process and external map geometry source. Secrets and database credentials are never displayed here.",
)

section_heading("Snapshot status", "The app reads aggregated CSV extracts generated from the project's local MySQL database")
if snapshot["available"]:
    generated_label = snapshot["ist"].strftime("%d %b %Y, %I:%M %p IST")
else:
    generated_label = "Not recorded"

cols = st.columns(4)
with cols[0]:
    st.metric("Datasets loaded", f"{len(data)} / {len(DATA_FILES)}")
with cols[1]:
    st.metric("Export version", str(manifest.get("export_version", "Unknown")))
with cols[2]:
    st.metric("Last successful export", generated_label)
with cols[3]:
    st.metric("Snapshot age", snapshot["age_label"])

if snapshot["available"]:
    st.caption(
        f"Generated at {snapshot['utc'].strftime('%Y-%m-%d %H:%M:%S UTC')} "
        f"({generated_label}). This timestamp describes the aggregate CSV export, "
        "not the latest transaction date in the historical Olist dataset."
    )
else:
    st.warning("The export manifest does not contain a valid generated_at_utc timestamp. Re-run the dashboard export script to create a timestamped snapshot.")

section_heading("Public application URL", "The app URL is configured after deployment; it is never inferred from a local session")
with st.container(border=True):
    if public_url:
        st.success("Public URL configured")
        st.link_button("Open live E-commerce IQ", public_url, use_container_width=False)
        st.code(public_url, language="text")
    else:
        st.info("No public URL configured. This is normal before deployment.")
        st.markdown("Add the following to Streamlit Community Cloud → App settings → Secrets after deployment:")
        st.code('STREAMLIT_APP_URL = "https://your-app-name.streamlit.app"', language="toml")
        st.caption("For local preview, add STREAMLIT_APP_URL=https://your-app-name.streamlit.app to the root .env file. Do not commit .env.")

section_heading("Dataset registry", "Grain and source description are included in the export manifest")
registry = []
manifest_entries = {item.get("dataset"): item for item in manifest.get("datasets", [])}
for key, filename in DATA_FILES.items():
    frame = data[key]
    entry = manifest_entries.get(key, {})
    file_path = DATA_DIR / filename
    registry.append({
        "Dataset": key,
        "Rows": len(frame),
        "Columns": len(frame.columns),
        "File size (KB)": round(file_path.stat().st_size / 1024, 2) if file_path.exists() else None,
        "Description": entry.get("description", "Aggregated dashboard extract"),
    })
registry_df = pd.DataFrame(registry)
st.dataframe(
    registry_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Rows": st.column_config.NumberColumn("Rows", format="%d"),
        "Columns": st.column_config.NumberColumn("Columns", format="%d"),
        "File size (KB)": st.column_config.NumberColumn("File size (KB)", format="%.2f"),
    },
)

section_heading("Data lineage", "Source database → SQL views and aggregate queries → local CSV snapshots → Streamlit pages")
with st.container(border=True):
    st.markdown(
        """
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:9px;align-items:stretch">
          <div style="background:#13283D;border:1px solid #28465D;border-radius:12px;padding:15px;text-align:center">
            <div style="color:#46D8C1;font-size:11px;font-weight:800;letter-spacing:.1em">SOURCE</div>
            <div style="font:700 14px Manrope;color:#F2F6FC;margin-top:7px">MySQL 8</div>
            <div style="color:#9CB0C5;font-size:10px;margin-top:5px">9 relational tables</div>
          </div>
          <div style="background:#13283D;border:1px solid #28465D;border-radius:12px;padding:15px;text-align:center">
            <div style="color:#6EA8FE;font-size:11px;font-weight:800;letter-spacing:.1em">ANALYSIS</div>
            <div style="font:700 14px Manrope;color:#F2F6FC;margin-top:7px">SQL views</div>
            <div style="color:#9CB0C5;font-size:10px;margin-top:5px">RFM + cohort</div>
          </div>
          <div style="background:#13283D;border:1px solid #28465D;border-radius:12px;padding:15px;text-align:center">
            <div style="color:#B39AFB;font-size:11px;font-weight:800;letter-spacing:.1em">SNAPSHOT</div>
            <div style="font:700 14px Manrope;color:#F2F6FC;margin-top:7px">Aggregated CSVs</div>
            <div style="color:#9CB0C5;font-size:10px;margin-top:5px">app_data/</div>
          </div>
          <div style="background:#13283D;border:1px solid #28465D;border-radius:12px;padding:15px;text-align:center">
            <div style="color:#F6C56F;font-size:11px;font-weight:800;letter-spacing:.1em">PRESENTATION</div>
            <div style="font:700 14px Manrope;color:#F2F6FC;margin-top:7px">Streamlit IQ</div>
            <div style="color:#9CB0C5;font-size:10px;margin-top:5px">Charts + reports</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("The deployed app uses the aggregate snapshot. It does not connect to a developer laptop's local MySQL server.")

section_heading("Data-quality decisions")
quality = data["data_quality"]
st.dataframe(quality, hide_index=True, use_container_width=True, column_config={
    "flagged_rows": st.column_config.NumberColumn("Flagged rows", format="%d"),
})
st.markdown(
    "<div class='callout'>The cleaning process preserves missing values, unmatched lookup references and investigated anomalies. "
    "The geolocation boundary flag uses an approximate Brazil bounding box; it is not a definitive border validation. "
    "Repeated geolocation rows are preserved because repetition alone did not prove they were invalid.</div>",
    unsafe_allow_html=True,
)

section_heading("Configuration and refresh")
left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown("**Local environment variables**")
        st.code(
            "DB_HOST=localhost\nDB_PORT=3306\nDB_NAME=ecommerce_customer_intelligence\n"
            "DB_USER=your_user\nDB_PASSWORD=your_password\n"
            "STREAMLIT_APP_URL=https://your-app-name.streamlit.app",
            language="ini",
        )
        st.caption("Actual values belong in `.env`. The `.env` file is ignored by Git and is never displayed here.")
with right:
    with st.container(border=True):
        st.markdown("**Refresh sequence**")
        st.code("python scripts/export_dashboard_data.py\npython scripts/validate_dashboard_data.py", language="bash")
        st.caption("The export script extracts from MySQL, writes a manifest and replaces the aggregate snapshots only after all queries succeed. Commit the refreshed app_data snapshot to redeploy.")

section_heading("External map geometry")
with st.container(border=True):
    st.markdown("**Brazil state boundaries**")
    st.write("The choropleth uses a public GeoJSON compilation of IBGE state boundary data. The source repository documents the state properties and CC0 1.0 license.")
    st.markdown("Source: [henriquemalvar/br-geojson](https://github.com/henriquemalvar/br-geojson) · [IBGE territorial meshes](https://servicodados.ibge.gov.br/) · CC0 1.0")
    st.caption("The map is cached in the app. If the external geometry service is unreachable, the state ranking remains available.")

if manifest:
    with st.expander("View export manifest"):
        st.json(manifest)
    st.download_button(
        "Download data manifest",
        data=json.dumps(manifest, indent=2).encode("utf-8"),
        file_name="data_manifest.json",
        mime="application/json",
    )

page_footer()
