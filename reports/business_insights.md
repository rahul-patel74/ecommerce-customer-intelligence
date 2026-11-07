## Analysis 01: Customer Purchase Frequency

### Key Metrics

| Metric | Result |
|---|---:|
| Unique delivered customers | 93,358 |
| One-time customers | 90,557 |
| Repeat customers | 2,801 |
| Repeat customer percentage | 3.00% |
| Average delivered orders per customer | 1.03 |

### Business Insights

- Most customers placed only one delivered order.
- Repeat customers represent approximately 3% of customers with delivered purchases.
- Average delivered purchase frequency is 1.03 orders per customer.
- Customer retention is an important area for further investigation.

### Methodology

- Customer identity was determined using customer_unique_id.
- Only orders with order_status = 'delivered' were included.
- Orders were counted distinctly to avoid duplicate order counting.


## Analysis 02: Customer Order Frequency Distribution

### Results

| Delivered Orders | Number of Customers | Customer Percentage |
|---:|---:|---:|
| 1 | 90,557 | 97.00% |
| 2 | 2,573 | 2.76% |
| 3 | 181 | 0.19% |
| 4 | 28 | 0.03% |
| 5 | 9 | 0.01% |
| 6 | 5 | 0.01% |
| 7 | 3 | Less than 0.01% |
| 9 | 1 | Less than 0.01% |
| 15 | 1 | Less than 0.01% |

### Business Insights

- Approximately 97% of customers made only one delivered purchase.
- Most repeat customers purchased exactly twice.
- Only 228 customers made three or more delivered purchases.
- One customer placed 15 delivered orders, representing the highest observed purchase frequency.
- The results indicate that repeat purchasing is relatively uncommon in the dataset.

### Methodology

- Customers were identified using `customer_unique_id`.
- Only delivered orders were considered.
- Purchase frequency was calculated using distinct order IDs.
- Customer percentages were calculated against all 93,358 unique delivered customers.

### Business Implication

Customer retention is an important area for further investigation. Additional analysis of customer spending, purchase timing and retention cohorts is required before making recommendations about customer engagement strategies.


## Analysis 03: Customer Spending by Purchase Frequency

### Key Results

| Delivered Orders | Customers | Recorded Payment Value | Average Payment per Customer | Payment Share |
|---:|---:|---:|---:|---:|
| 1 | 90,557 | 14,558,104.56 | 160.76 | 94.40% |
| 2 | 2,573 | 748,808.38 | 291.03 | 4.86% |
| 3 | 181 | 78,445.86 | 433.40 | 0.51% |
| 4 | 28 | 22,086.28 | 788.80 | 0.14% |
| 5 | 9 | 6,607.63 | 734.18 | 0.04% |
| 6 | 5 | 3,516.57 | 703.31 | 0.02% |
| 7 | 3 | 2,840.56 | 946.85 | 0.02% |
| 9 | 1 | 1,172.66 | 1,172.66 | 0.01% |
| 15 | 1 | 879.27 | 879.27 | 0.01% |

### One-time vs Repeat Customer Comparison

| Metric | One-time Customers | Repeat Customers |
|---|---:|---:|
| Number of customers | 90,557 | 2,801 |
| Customer percentage | 97.00% | 3.00% |
| Recorded payment value | 14,558,104.56 | 864,357.21 |
| Payment value percentage | 94.40% | 5.60% |
| Average payment per customer | 160.76 | 308.59 |

### Business Insights

- Repeat customers generate approximately 1.92 times the average recorded payment value per customer compared with one-time customers.
- Repeat customers represent approximately 3% of the customer base but contribute 5.60% of recorded payment value.
- Most recorded payment value comes from one-time customers because they make up the overwhelming majority of shoppers.
- Customer retention deserves further investigation.

### Methodology

- Only delivered orders were included.
- Customer identity was determined using `customer_unique_id`.
- Multiple payment records belonging to the same order were aggregated before joining with customer records.
- Customers without recorded payments were retained using LEFT JOIN.
- Average payment per customer was calculated using zero for customers without an associated payment record.

### Data Limitations

Recorded payment value is not equivalent to profit or accounting revenue. The analysis represents observed customer spending during the available dataset period, not complete future customer lifetime value.

One delivered order has no associated payment record, which remains a documented data-quality anomaly.


## Analysis 04: Top 10 Highest-Spending Customers

### Results

| Rank | Delivered Orders | Recorded Payment Value |
|---:|---:|---:|
| 1 | 1 | 13,664.08 |
| 2 | 2 | 7,571.63 |
| 3 | 1 | 7,274.88 |
| 4 | 1 | 6,929.31 |
| 5 | 1 | 6,922.21 |
| 6 | 1 | 6,726.66 |
| 7 | 1 | 6,081.54 |
| 8 | 1 | 4,764.34 |
| 9 | 1 | 4,681.78 |
| 10 | 4 | 4,655.91 |

### Business Insights

- The highest-spending customer generated 13,664.08 in recorded payment value through one delivered order.
- Eight of the top ten customers made only one delivered purchase.
- High transaction value does not necessarily indicate customer loyalty.
- The top ten customers collectively generated 69,272.34, approximately 0.45% of total recorded payments from delivered orders.
- The highest-value customer transaction should be investigated to understand its composition.

### Methodology

- Only delivered orders were included.
- Payment records were aggregated at order level before customer-level aggregation.
- Customers were identified using customer_unique_id.
- DENSE_RANK() was used to identify the highest-spending customers.

### Limitation

Recorded payment value represents observed spending within the dataset period, not profit or complete customer lifetime value.


## Analysis 05: Investigating High-Spending Customers

### Key Findings

- The highest-spending customer generated 13,664.08 through one delivered order containing eight items.
- Eight of the ten highest-spending customers made only one delivered purchase.
- The second-ranked customer generated 7,571.63 through two delivered purchases.
- High transaction value does not necessarily indicate repeat purchasing behaviour.

### Order Composition

For the highest-spending customer:

| Component | Amount |
|---|---:|
| Product price | 13,440.00 |
| Freight | 224.08 |
| Recorded payment | 13,664.08 |

The product price and freight totals match the recorded payment.

### Data Quality Observation

One investigated order showed a 0.03 difference between recorded payment and product-plus-freight totals. Further investigation is required.

### Business Implication

Customer spending should be evaluated alongside purchase frequency. High-value transactions and customer loyalty represent different dimensions of customer behaviour.

### Payment Reconciliation Investigation

Investigated order:
3e073b27114fe955e184db124d34a566

| Component | Amount |
|---|---:|
| Product price | 1,020.00 |
| Freight | 27.96 |
| Product + freight | 1,047.96 |
| Recorded payment | 1,047.99 |
| Difference | 0.03 |

The order contains six units of the same product and one credit-card payment with six installments.

The reason for the 0.03 difference could not be established from the available records.

Decision: Preserve the original payment and order-item values. Document the discrepancy without making an unsupported correction.


## Analysis 06: Customer Geographic Distribution

### Key Findings

- São Paulo (SP) generated the highest recorded payment value: 5,770,266.19.
- SP contributed 41.92% of state-level shopper counts and 37.41% of recorded payment value.
- Rio de Janeiro contributed 13.33% of payment value.
- Minas Gerais contributed 11.80% of payment value.
- The top three states (SP, RJ and MG) generated 62.54% of recorded payment value.

### Business Insights

- São Paulo is the largest customer market by both shopper count and recorded payment value.
- Rio de Janeiro contributes a slightly higher share of payment value than its share of state-level shoppers.
- The business is geographically concentrated, with three states contributing approximately 62.54% of payment value.

### Methodology

- Only delivered orders were included.
- Geographic classification uses customer_state.
- Customers were identified using customer_unique_id.
- Payment records were aggregated at order level before joining with customer records.
- State-level customer counts use distinct customer_unique_id values.

### Data Limitation

A shopper may have customer records associated with multiple states. Therefore, state-level distinct shopper counts may overlap and should not be interpreted as mutually exclusive global customer counts.


## Analysis 07: Average Payment Per Delivered Order

### Results

| Metric | One-time Customers | Repeat Customers |
|---|---:|---:|
| Customers | 90,557 | 2,801 |
| Delivered orders | 90,557 | 5,921 |
| Paid orders | 90,556 | 5,921 |
| Total recorded payment | 14,558,104.56 | 864,357.21 |
| Average payment per customer | 160.76 | 308.59 |
| Average payment per paid order | 160.76 | 145.98 |

### Business Insights

- Repeat customers generate higher cumulative payment value per customer because they purchase more frequently.
- Their average payment per order is approximately 9.2% lower than that of one-time customers.
- One-time customers generate higher average payment per individual order.
- Customer spending differences are therefore influenced by purchase frequency, not just transaction size.

### Data Limitation

One delivered order has no associated payment record. The one-time customer group has 90,557 delivered orders but only 90,556 paid orders.

Average payment per order is calculated using orders with recorded payments.

Recorded payment value is not equivalent to profit or accounting revenue.

### Business Implication

Customer retention and purchase frequency may be more important opportunities than simply increasing average transaction value.