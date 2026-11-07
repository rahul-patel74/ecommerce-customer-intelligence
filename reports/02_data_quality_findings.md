# Data Quality Findings and Database Validation

## 1. Project Overview

This report documents the data-quality investigation and relational database validation performed on the Olist Brazilian E-Commerce Public Dataset.

**Database:** `ecommerce_customer_intelligence`  
**Database engine:** MySQL 8.0.42  
**Dataset:** Olist Brazilian E-Commerce Public Dataset

The purpose of this phase was to understand the dataset structure, identify data-quality issues, load the source tables into MySQL, and validate relationships between the tables.

No raw records were deleted during this phase.

## 2. Database Import Summary

All nine source CSV files were successfully imported.

| Table | Imported Records |
|---|---:|
| customers | 99,441 |
| orders | 99,441 |
| order_items | 112,650 |
| payments | 103,886 |
| reviews | 99,224 |
| products | 32,951 |
| sellers | 3,095 |
| geolocation | 1,000,163 |
| category_translation | 71 |

All imported row counts match the source dataset.

## 3. Database Schema and Key Validation

The following primary keys were established:

| Table | Primary Key |
|---|---|
| customers | customer_id |
| orders | order_id |
| order_items | order_id, order_item_id |
| payments | order_id, payment_sequential |
| reviews | review_id, order_id |
| products | product_id |
| sellers | seller_id |
| geolocation | geolocation_id |
| category_translation | product_category_name |

The `reviews` table uses a composite primary key because `review_id` is repeated across different orders.

The geolocation table uses an auto-incrementing identifier because ZIP prefixes and geographic coordinates are not unique.

### Foreign-Key Validation

Six foreign-key relationships were validated.

| Relationship | Unmatched Records |
|---|---:|
| orders → customers | 0 |
| order_items → orders | 0 |
| order_items → products | 0 |
| order_items → sellers | 0 |
| payments → orders | 0 |
| reviews → orders | 0 |

All six relationships passed validation.

### Customer Identity

| Metric | Value |
|---|---:|
| Customer records | 99,441 |
| Unique shoppers (`customer_unique_id`) | 96,096 |
| Additional customer records | 3,345 |

`customer_id` identifies the order-specific customer record, whereas `customer_unique_id` identifies the actual shopper.

The latter will be used for repeat-purchase and customer-retention analysis.

## 4. Lookup Coverage Issues

Three lookup relationships were investigated.

| Relationship | Unmatched Records | Distinct Unmatched Values |
|---|---:|---:|
| Customers → Geolocation | 278 | 157 ZIP prefixes |
| Sellers → Geolocation | 7 | 7 ZIP prefixes |
| Products → Category Translation | 13 | 2 categories |

The unmatched product categories were:

| Original Category | Product Count |
|---|---:|
| pc_gamer | 3 |
| portateis_cozinha_e_preparadores_de_alimentos | 10 |

These are lookup coverage gaps, not violations of the enforced foreign keys.

Decisions:
- Customer and seller records with unmatched ZIP prefixes were retained.
- No geographic coordinates were invented.
- Original Portuguese product categories were preserved.
- English translations will use LEFT JOIN so untranslated products are not excluded.

## 5. Missing-Value Analysis

### Orders

| Column | Missing Records |
|---|---:|
| order_approved_at | 160 |
| order_delivered_carrier_date | 1,783 |
| order_delivered_customer_date | 2,965 |

Missing timestamps were retained. Their business meaning will be investigated through order status and delivery analysis.

### Products

| Column | Missing Records |
|---|---:|
| product_category_name | 610 |
| product_name_lenght | 610 |
| product_description_lenght | 610 |
| product_photos_qty | 610 |
| product_weight_g | 2 |
| product_length_cm | 2 |
| product_height_cm | 2 |
| product_width_cm | 2 |

These missing values were preserved rather than replaced with arbitrary values.

### Reviews

After whitespace normalization:

| Metric | Missing Records |
|---|---:|
| review_comment_title | 87,658 |
| review_comment_message | 58,274 |

The original Python missing-value analysis reported 87,656 missing titles and 58,247 missing messages.

Further investigation identified:
- 2 whitespace-only review titles.
- 27 whitespace-only review messages.

These were normalized to SQL NULL values. Meaningful customer comments were preserved.

## 6. Duplicate Analysis

### Exact Duplicate Records

Exact duplicate analysis found:

| Table | Excess Duplicate Rows |
|---|---:|
| customers | 0 |
| geolocation | 261,831 |
| orders | 0 |
| order_items | 0 |
| payments | 0 |
| reviews | 0 |
| products | 0 |
| sellers | 0 |
| category_translation | 0 |

Geolocation duplicates were verified in MySQL using exact binary comparisons.

| Geolocation Metric | Result |
|---|---:|
| Duplicate groups | 128,174 |
| Excess duplicate rows | 261,831 |
| Maximum occurrences of one record | 314 |

The original geolocation records were retained. Duplicate detection does not automatically imply that records should be deleted.

### Customer Identity Duplicates

The 3,345 additional customer records represent repeated `customer_unique_id` values across order-specific customer records. These are important for shopper-level analysis.

### Review ID Repetition

| Metric | Result |
|---|---:|
| Repeated review ID groups | 789 |
| Additional occurrences | 814 |
| Maximum occurrences | 3 |

The composite key `(review_id, order_id)` uniquely identifies review records.

## 7. Order Relationship Investigation

The following order relationships were investigated:

| Relationship | Orders Without Related Records |
|---|---:|
| Orders → Order Items | 775 |
| Orders → Payments | 1 |
| Orders → Reviews | 768 |

### Orders Without Items

| Order Status | Orders Without Items |
|---|---:|
| unavailable | 603 |
| canceled | 164 |
| created | 5 |
| invoiced | 2 |
| shipped | 1 |
| **Total** | **775** |

The 767 unavailable and canceled orders account for most of the missing item relationships.

The remaining eight orders were investigated separately:
- Five created orders.
- Two invoiced orders.
- One shipped order.

All eight had payment records, with a combined payment value of 915.06. Six also had review records.

The reason their item records are missing has not been established. They were retained and documented as anomalies.

### Delivered Order Without Payment

One delivered order had no associated payment record:

`bfbd0f9bdef84302105ad712db648a6c`

Its delivery date was November 9, 2016, while its estimated delivery date was October 4, 2016.

This represents a 36-day delivery delay relative to the estimated date.

The absence of a matching payment record remains an unresolved dataset anomaly.

Missing review records are not automatically considered errors because submitting a review is optional.

## 8. Import and Data-Type Corrections

Several technical issues were identified and corrected during MySQL loading.

### Geolocation Precision

The original source coordinates contained:
- Latitude: up to 20 decimal places.
- Longitude: up to 16 decimal places.

The final schema uses:

`DECIMAL(23,20)` for latitude and longitude.

The final geolocation import loaded 1,000,163 records with zero warnings.

### Review CSV Formatting

The review CSV uses Windows CRLF line endings and contains embedded line breaks in customer comments.

The MySQL import was adjusted to use:
- `LINES TERMINATED BY '\r\n'`
- `OPTIONALLY ENCLOSED BY '"'`
- `ESCAPED BY '"'`

The import initially loaded 99,223 records. A comparison of composite review keys against the source file identified one missing record, which was inserted and verified separately.

Final review count: 99,224.

### Whitespace Normalization

Whitespace-only review comments were converted to SQL NULL values, without deleting meaningful customer text.

## 9. Final Decisions

The following decisions were made during this phase:

1. Preserve the original source CSV files.
2. Retain all geolocation records, including duplicates.
3. Preserve missing timestamps rather than inventing values.
4. Retain customers and sellers with unmatched geographic ZIP prefixes.
5. Preserve original product categories and handle missing translations through LEFT JOIN.
6. Use `customer_unique_id` for shopper-level analytics.
7. Use composite keys for order items, payments, and reviews.
8. Retain unusual orders and document their missing relationships.
9. Normalize whitespace-only review comments to SQL NULL.
10. Keep the saved SQL schema synchronized with the final MySQL table definitions.

## 10. Conclusion

The nine Olist dataset tables have been imported and their row counts verified.

All six core foreign-key relationships passed validation. Primary keys, lookup coverage, missing values, duplicate patterns, and unusual order relationships were investigated.

The database is ready for the next analytical phase, subject to the documented anomalies and the completion of a reproducible loading procedure.

**Next phase:** Customer Analysis, RFM Segmentation, and Cohort Retention Analysis using Python and MySQL.