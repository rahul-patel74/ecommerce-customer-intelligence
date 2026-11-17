# E-commerce Customer Intelligence & Retention Analytics

An end-to-end data analytics project using Python, MySQL and Power BI to investigate customer purchasing behavior, customer value, RFM segmentation and repeat-purchase retention.

## Project Overview

Understanding customer behavior is essential for improving customer retention and long-term business performance.

This project analyzes the Brazilian E-Commerce Public Dataset by Olist to investigate how customers purchase, how frequently they return, how much they spend and how customer groups behave over time.

The project combines Python-based data exploration and cleaning, relational data analysis using MySQL, and interactive reporting using Power BI.

## Business Objectives

- Understand customer purchasing behavior and purchase frequency.
- Identify one-time and repeat customers.
- Analyze customer spending patterns and geographic distribution.
- Segment customers using Recency, Frequency and Monetary (RFM) analysis.
- Evaluate customer retention through monthly cohort analysis.
- Identify opportunities for customer engagement and retention improvement.

## Dataset

**Source:** [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

The dataset contains Brazilian e-commerce transactions and related information covering 2016–2018.

It consists of nine CSV files:

| Dataset | Records |
|---|---:|
| Customers | 99,441 |
| Orders | 99,441 |
| Order Items | 112,650 |
| Order Payments | 103,886 |
| Order Reviews | 99,224 |
| Products | 32,951 |
| Sellers | 3,095 |
| Geolocation | 1,000,163 |
| Category Translation | 71 |

The nine datasets were loaded into a relational MySQL database and connected through primary and foreign key relationships where appropriate.

**Note:** The raw dataset is not included in this repository. Download it from Kaggle and place the CSV files in the `data/raw/` directory.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data exploration, cleaning and analysis |
| Pandas and NumPy | Data manipulation and transformation |
| Jupyter Notebook | Exploratory analysis and documentation |
| MySQL | Relational database and business analysis |
| SQL | Joins, aggregations, CTEs, window functions and cohort analysis |
| Power BI | Interactive dashboard and visualization |
| DAX | KPI calculations and analytical measures |
| Git and GitHub | Version control and project management |

## Project Workflow

### 1. Data Understanding and Quality Assessment

- Inspected all nine datasets and their structures.
- Examined data types, missing values and duplicate records.
- Investigated primary keys, composite keys and relationships.
- Identified unmatched lookup records and unusual order lifecycle cases.
- Documented data-quality findings before performing business analysis.

### 2. Data Cleaning and Preparation

Used Python to inspect and prepare the datasets.

Activities included:

- Missing-value analysis.
- Duplicate investigation.
- Data type validation.
- Timestamp handling.
- Key and relationship validation.
- Review text normalization.
- Documentation of data-quality issues and limitations.

The original records were retained where duplicates or unmatched values could not be established as data errors.

### 3. MySQL Database and SQL Analysis

Created the `ecommerce_customer_intelligence` database with nine relational tables.

Performed SQL analysis using joins, aggregate functions, Common Table Expressions (CTEs), subqueries and window functions.

The analyses covered:

- Overall customer purchasing behavior.
- One-time versus repeat customers.
- Purchase frequency distribution.
- Customer spending patterns.
- High-value customers.
- Geographic customer distribution.
- Average payment per delivered order.
- RFM customer segmentation.
- Monthly cohort retention.

### 4. RFM Customer Segmentation

Applied RFM analysis using:

- **Recency:** Days since the customer's latest delivered purchase.
- **Frequency:** Number of delivered purchases.
- **Monetary:** Total recorded payment associated with delivered purchases.

Created customer segments using RFM scores:

- Champions
- Loyal Customers
- Potential Loyalists
- Recent One-time Customers
- At Risk
- High-Value One-time Lapsed
- Hibernating
- Needs Attention

Created the MySQL view `vw_customer_rfm` to make the customer-level segmentation available for further analysis.

### 5. Cohort Retention Analysis

Performed monthly cohort analysis to understand repeat-purchase behavior over time.

The analysis includes:

- First delivered purchase month as the cohort assignment.
- Monthly delivered purchase activity.
- Cohort size and retained customer counts.
- Complete retention matrix, including observed months with zero returning customers.
- Month 1 retention by acquisition cohort.
- Weighted retention trend across cohort ages.

Created the MySQL view `vw_cohort_retention` containing 278 cohort-month records across 23 monthly cohorts.

## Key Business Findings

### Customer Purchasing Behavior

- Identified **93,358 unique customers** with at least one delivered purchase.
- 90,557 customers made only one delivered purchase.
- 2,801 customers made repeat delivered purchases.
- Repeat customers represented approximately **3.00%** of delivered customers.
- The average number of delivered orders per customer was approximately 1.03.

### Customer Spending

- One-time customers accounted for approximately 94.40% of recorded delivered-order payment value.
- Repeat customers had higher average spending per customer, at approximately 308.59 compared with 160.76 for one-time customers.
- However, repeat customers had a lower average payment per delivered order, at approximately 145.98 compared with 160.76 for one-time customers.

### RFM Segmentation

- Recent One-time Customers: 36,118 customers (38.69%).
- High-Value One-time Lapsed: 21,024 customers (22.52%).
- Needs Attention: 18,614 customers (19.94%).
- Hibernating: 15,368 customers (16.46%).
- Champions: 32 customers (0.03%).

The segmentation highlights a large population of one-time customers and potential opportunities for targeted retention and re-engagement initiatives.

### Cohort Retention

- Weighted Month 1 retention was approximately **0.48%**.
- 421 customers returned in Month 1 out of 87,214 customers belonging to cohorts with a complete Month 1 observation.
- Weighted retention declined to approximately 0.34% in Month 2 and 0.25% in Month 3.
- Repeat purchasing remained generally low across the observed cohort ages.

These findings suggest that encouraging repeat purchases is an important area for further investigation.

## Power BI Dashboard

The Power BI dashboard presents the cohort retention analysis through:

- KPI cards showing total customers, cohorts analyzed, Month 1 returning customers and Month 1 retention.
- A customer cohort retention heatmap.
- A weighted customer retention trend chart.

The heatmap highlights differences in retention across acquisition cohorts and subsequent months. Blank cells represent periods that were not observed in the dataset, rather than months with zero retention.

![Customer Cohort Retention Dashboard](powerbi/ecommerce_customer_cohort_dashboard.png)

**Dashboard file:** `powerbi/ecommerce_customer_cohort_analysis.pbix`

<!-- Add a dashboard screenshot here after saving it in the repository. -->

## Repository Structure

```text
ecommerce-customer-intelligence/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── 01_data_understanding.ipynb
│   ├── 02_data_cleaning.ipynb
│   └── 03_customer_analysis.ipynb
│
├── powerbi/
│   ├── ecommerce_customer_cohort_dashboard.png
│   └── ecommerce_customer_cohort_analysis.pbix
│
├── reports/
│   ├── 02_data_quality_findings.md
│   ├── business_insights.md
│   └── mermaid-diagram.png
│
├── sql/
│   ├── 00_create_database.sql
│   ├── 01_database_schema.sql
│   ├── 02_customer_analysis.sql
│   ├── 03_rfm_segmentation.sql
│   ├── 04_cohort_analysis.sql
│   └── 05_load_data.sql
│
├── src/
│   ├── __init__.py
│   ├── cleaning.py
│   └── validation.py
│
├── tests/
├── .gitignore
├── README.md
└── requirements.txt
```

## How to Reproduce the Project

### 1. Download the Dataset

Download the Brazilian E-Commerce Public Dataset from Kaggle and place the nine CSV files inside `data/raw/`.

### 2. Set Up Python

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

### 3. Run the Notebooks

Run the notebooks in sequence:

1. `01_data_understanding.ipynb`
2. `02_data_cleaning.ipynb`
3. `03_customer_analysis.ipynb`

### 4. Set Up MySQL

Run the SQL scripts in the following order in a fresh database environment:

1. `00_create_database.sql`
2. `01_database_schema.sql`
3. `05_load_data.sql`
4. `02_customer_analysis.sql`
5. `03_rfm_segmentation.sql`
6. `04_cohort_analysis.sql`

Update local file paths and MySQL import settings where required. The data-loading script is intended for empty tables in a fresh database. Do not run it again against an already populated database without preparing the tables first.

### 5. Open the Power BI Dashboard

Install the MySQL Connector/NET required by the Power BI MySQL connector, configure the database connection and load the analytical views where needed.

Open the `.pbix` file in Power BI Desktop.

## Limitations

- The dataset represents historical transactions from 2016–2018 and does not represent current customer activity.
- The analysis measures delivered purchases; other order statuses are excluded from the customer retention calculations.
- Monthly cohort retention measures activity in a calendar month, not continuous monthly retention.
- Later cohort ages have fewer eligible customers because the dataset ends in August 2018.
- RFM segments describe observed historical behavior and do not establish future customer intent.
- The analysis is observational and does not establish the causes of low repeat purchasing.

## Project Outcome

This project demonstrates an end-to-end analytics workflow, from multi-table dataset exploration and preparation to relational SQL analysis, customer segmentation, cohort retention and Power BI reporting.

It applies practical data analytics techniques to a real-world e-commerce dataset and translates analytical results into business-oriented findings.

---

- **Project:** E-commerce Customer Intelligence & Retention Analytics
- **Domain:** E-commerce / Customer Analytics
- **Tools:** Python, MySQL, SQL, Power BI and DAX
- **Dataset:** Olist Brazilian E-Commerce Public Dataset