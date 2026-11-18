# Python Data Cleaning and Validation

## 1. Overview

This stage implements the Python data cleaning and validation pipeline
for the Olist Brazilian E-Commerce dataset.

The objective was to standardize data types, normalize text values,
investigate data-quality issues, validate relationships, identify
anomalies, and export processed datasets without unnecessarily
deleting or modifying source records.

## 2. Dataset Inventory

| Dataset | Original Rows | Final Rows | Columns |
|---|---:|---:|---:|
| olist_customers_dataset | 99,441 | 99,441 | 5 |
| olist_geolocation_dataset | 1,000,163 | 1,000,163 | 6 |
| olist_orders_dataset | 99,441 | 99,441 | 8 |
| olist_order_items_dataset | 112,650 | 112,650 | 7 |
| olist_order_payments_dataset | 103,886 | 103,886 | 6 |
| olist_order_reviews_dataset | 99,224 | 99,224 | 7 |
| olist_products_dataset | 32,951 | 32,951 | 9 |
| olist_sellers_dataset | 3,095 | 3,095 | 4 |
| product_category_name_translation | 71 | 71 | 2 |

Total datasets processed: 9

## 3. Data Cleaning Operations

### Text normalization
- Removed leading and trailing whitespace from text columns.
- Converted whitespace-only review titles into missing values: 2.
- Converted whitespace-only review messages into missing values: 27.

### Datetime conversion
Converted 8 date columns across orders, order items, and reviews
into datetime format.

All non-missing date values were successfully parsed.
Invalid date values: 0.

### Postal code handling
Converted customer, seller, and geolocation ZIP prefixes into string
data types to preserve leading zeros.

### Numeric datatype conversion
Converted the following seven product attributes to Pandas nullable
Int64:

- product_name_lenght
- product_description_lenght
- product_photos_qty
- product_weight_g
- product_length_cm
- product_height_cm
- product_width_cm

All non-missing values were confirmed to be whole numbers before conversion.

## 4. Missing Value Analysis

Missing values were preserved rather than filled with arbitrary values.

| Dataset | Missing Values |
|---|---:|
| Orders | 4,908 |
| Reviews | 145,932 |
| Products | 2,448 |

Review missing values:
- Review titles: 87,658
- Review messages: 58,274

Product missing values were concentrated in descriptive attributes
and physical dimensions.

## 5. Duplicate Investigation

Exact duplicate rows were investigated across all nine datasets.

- Geolocation: 261,831 exact duplicate rows.
- Other eight datasets: 0 exact duplicate rows.

Geolocation duplicates were retained because repeated records were
not sufficient evidence of invalid data.

No records were removed during this stage.

## 6. Key and Relationship Validation

### Primary and composite keys

Eight key definitions were tested.

All eight passed:
- No missing key values.
- No duplicate key combinations.

Composite keys were used for order items, payments, and reviews
where a single column was not sufficient.

### Core foreign-key relationships

All six tested relationships passed.

No unmatched references were found between:
- Orders and customers.
- Order items and orders.
- Order items and products.
- Order items and sellers.
- Payments and orders.
- Reviews and orders.

## 7. Supplementary Lookup Validation

The following lookup gaps were identified:

| Lookup | Unmatched Rows | Unique Values |
|---|---:|---:|
| Customer ZIP to geolocation | 278 | 157 |
| Seller ZIP to geolocation | 7 | 7 |
| Product categories to translations | 13 | 2 |

Additionally, 610 products had missing category values.

The two unmatched product categories were:
- portateis_cozinha_e_preparadores_de_alimentos
- pc_gamer

These records were retained. No missing postal codes or category
translations were fabricated.

## 8. Numeric Validation and Anomaly Investigation

Two payment records had zero credit-card installments.

These records were retained and flagged for investigation.

Twenty-nine geolocation records were outside the approximate
Brazil geographic bounding box used for screening.

These records were also retained and flagged.

Two quality-control columns were added:

- has_installment_count_issue
- is_outside_approx_brazil_bounds

The geographic screening rule is an approximate bounding-box check,
not an official country-boundary test.

Other tested numeric fields passed their defined range checks.

## 9. Final Integrity Validation

All nine datasets preserved their original row counts.

No records were dropped.

The expected nullable integer types and ZIP prefix string types
were verified.

The payment and geolocation anomaly flags were verified.

## 10. Processed Dataset Export

All nine processed datasets were exported as CSV files to:

`data/processed/`

Export verification confirmed that every file retained its expected
row count and column count.

The raw source files were not overwritten.

## 11. Data Quality Decisions

The following principles guided the cleaning process:

1. Preserve original records unless there is sufficient evidence
   to justify removal.
2. Do not fabricate missing values.
3. Use composite keys where required.
4. Retain unmatched lookup records and document coverage gaps.
5. Flag suspicious records instead of silently modifying them.
6. Verify data integrity before and after export.

## 12. Conclusion

The Python cleaning pipeline standardized the datasets, validated
their structure and relationships, investigated data-quality issues,
and generated nine processed CSV files.

All original row counts were preserved, and all exported files
passed row-count and column-count validation.
