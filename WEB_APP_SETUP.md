# E-commerce IQ — Web Application Setup

This is an upgraded multi-page Streamlit application for the Olist E-commerce Customer Intelligence project. It uses Streamlit 1.46 or later for the modern multipage API and custom page links.

## App experience

- Executive overview with KPI cards, sparklines, operating trends, a Brazil state choropleth, category performance, order status and data-quality signals.
- Sales & Operations with monthly order status, payment methods, delivery performance, category detail and state scorecards.
- Customer Intelligence with the one-time/repeat comparison, purchase-frequency distribution and RFM segmentation.
- Retention Analytics with a cohort heatmap, weighted retention curve and individual cohort drill-down.
- Reports & Exports with downloadable PDF/HTML executive briefs and curated CSV snapshots.
- Data & Settings with a dataset registry, source lineage, data-quality notes and refresh instructions.

## 1. Install dependencies

Use the existing project virtual environment, then run:

```cmd
pip install -r requirements.txt
```

## 2. Configure MySQL extraction credentials

Copy `.env.example` to `.env` and enter the local MySQL credentials. `.env` is ignored by Git.

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ecommerce_customer_intelligence
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
```

Do not paste credentials into source code or commit `.env`.

## 3. Refresh the aggregate dashboard extracts

Run these from the repository root:

```cmd
python scripts\export_dashboard_data.py
python scripts\validate_dashboard_data.py
```

The export script reads the established MySQL tables and views, writes the new CSV snapshots into `app_data/`, and creates `app_data/data_manifest.json`. It uses a staging directory and replaces the current files only after every query and file write succeeds.

The curated `app_data/*.csv` extracts are small aggregate datasets and are intended to be committed. Do not commit `data/raw/`, `data/processed/`, `.env` or MySQL credentials.

## 4. Run locally

```cmd
streamlit run app.py
```

Streamlit normally opens the app at `http://localhost:8501`.

## 5. Deploy on Streamlit Community Cloud

1. Push the application code and the curated `app_data/*.csv` snapshots to GitHub.
2. Create a Streamlit Community Cloud app pointing to the repository, branch and `app.py` entry point.
3. Add a `requirements.txt` dependency file (already included).
4. No MySQL secrets are required for the deployed read-only app because it reads the committed aggregate CSV snapshots rather than connecting to the developer's laptop.
5. The Brazil map loads state-boundary GeoJSON from the public source described below. If the map source is unreachable, state rankings remain available.

For a future scheduled data refresh, use a hosted database or a secure scheduled export workflow. Do not try to expose a local MySQL instance or embed credentials in the deployed app.

## Filter behavior

- The global date filter applies to monthly order, payment, status, category, state and delivery views where monthly extracts exist.
- State selection applies to state-level views and state-aware monthly order/payment totals.
- Product-category selection applies to category analyses.
- Full-history customer/RFM metrics and cohort retention remain clearly identified as full-history measures. The app does not pretend these full-history aggregates recalculate for a selected month window.
- Payment methods are a full-period aggregate in the current extract and are labelled accordingly.

## Geography source and attribution

The state choropleth uses the `estados.geojson` resource from [henriquemalvar/br-geojson](https://github.com/henriquemalvar/br-geojson), which documents IBGE territorial meshes and CC0 1.0 licensing. See the [IBGE territorial service](https://servicodados.ibge.gov.br/) for the upstream geographic reference.

## Metric definitions and limitations

- **Recorded payment value** means the sum of payment records; it is not profit, net revenue or margin.
- Delivered-order customer metrics use `customer_unique_id` as the shopper identifier and only delivered orders.
- State-level distinct shopper counts can overlap across states.
- Monthly cohort retention measures delivered purchase activity in a calendar month, not continuous retention.
- The dataset is historical (2016–2018); it does not represent current activity or predict future customer intent.
- Data-quality flags are shown as investigation findings. The source records are retained rather than silently corrected or deleted.
