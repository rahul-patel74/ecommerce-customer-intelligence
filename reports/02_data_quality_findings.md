# Data Quality Findings

## 1. Referential Integrity

| Relationship | Unmatched Records | Observation |
|---|---:|---|
| Orders → Customers | 0 | All customer references exist |
| Order Items → Orders | 0 | All order references exist |
| Order Items → Products | 0 | All product references exist |
| Order Items → Sellers | 0 | All seller references exist |
| Payments → Orders | 0 | All order references exist |
| Reviews → Orders | 0 | All order references exist |
| Customers → Geolocation | 278 | 157 unmatched ZIP prefixes |
| Sellers → Geolocation | 7 | 7 unmatched ZIP prefixes |
| Products → Category Translation | 13 | 2 untranslated categories |

## 2. Geolocation Findings

- Original records: 1,000,163
- Exact duplicate records: 261,831
- Unique ZIP prefixes: 19,015
- Unique ZIP-coordinate combinations: 720,154

Decision: Preserve original records. Investigate aggregation for analytical use.

## 3. Review Findings

- Total review records: 99,224
- Unique review IDs: 98,410
- Duplicate review IDs: 789
- Duplicate review ID and order ID combinations: 0
- Review IDs with consistent information: 789

Decision: Retain records and use review_id + order_id as a candidate composite key.

## 4. Product Category Findings

Untranslated categories:

| Category | Product Count |
|---|---:|
| pc_gamer | 3 |
| portateis_cozinha_e_preparadores_de_alimentos | 10 |

Decision: Preserve original category values and document additional English translations separately.

## 5. Overall Decision

No records will be removed during the data-understanding phase. All identified issues will be handled through documented cleaning and transformation steps.