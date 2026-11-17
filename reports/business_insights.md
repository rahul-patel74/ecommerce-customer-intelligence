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


## Analysis 08: RFM Customer Segmentation

### Segment Results

| Segment | Customers | Percentage | Avg Recency | Avg Frequency | Avg Monetary |
|---|---:|---:|---:|---:|---:|
| Recent One-time Customers | 36,118 | 38.69% | 90.90 | 1.00 | 164.29 |
| High-Value One-time Lapsed | 21,024 | 22.52% | 394.51 | 1.00 | 239.34 |
| Needs Attention | 18,614 | 19.94% | 220.21 | 1.03 | 155.76 |
| Hibernating | 15,368 | 16.46% | 396.42 | 1.00 | 55.74 |
| Potential Loyalists | 1,080 | 1.16% | 89.00 | 2.00 | 296.99 |
| At Risk | 997 | 1.07% | 381.80 | 2.08 | 295.47 |
| Loyal Customers | 125 | 0.13% | 126.94 | 3.14 | 460.08 |
| Champions | 32 | 0.03% | 83.56 | 4.97 | 873.64 |

### Business Insights

- Recent One-time Customers form the largest segment at 38.69%.
- High-Value One-time Lapsed Customers represent 22.52% of the customer base.
- Hibernating customers have the lowest average recorded payment value.
- Champions represent only 32 customers but have the highest average Monetary value.
- Potential Loyalists represent an opportunity to encourage repeat purchases.

### Methodology

- Recency was calculated using the latest delivered purchase date plus one day as the reference date.
- Frequency counts distinct delivered orders.
- Monetary represents total recorded payment value.
- Recency and Monetary scores use percentile-based scoring.
- Frequency uses business-defined thresholds due to the highly skewed purchase-frequency distribution.
- All customers were assigned exactly one segment using ordered CASE conditions.

### Limitation

RFM segments describe historical purchasing behaviour within the available dataset period. They do not establish future purchasing intentions or predict actual customer lifetime value.


## Analysis 09: Monetary Contribution by RFM Segment

### Results

| Customer Segment | Customers | Total Monetary | Contribution | Average Monetary |
|---|---:|---:|---:|---:|
| Recent One-time Customers | 36,118 | 5,933,990.14 | 38.48% | 164.29 |
| High-Value One-time Lapsed | 21,024 | 5,031,852.17 | 32.63% | 239.34 |
| Needs Attention | 18,614 | 2,899,230.62 | 18.80% | 155.76 |
| Hibernating | 15,368 | 856,583.73 | 5.55% | 55.74 |
| Potential Loyalists | 1,080 | 320,754.35 | 2.08% | 296.99 |
| At Risk | 997 | 294,583.92 | 1.91% | 295.47 |
| Loyal Customers | 125 | 57,510.37 | 0.37% | 460.08 |
| Champions | 32 | 27,956.47 | 0.18% | 873.64 |

### Business Insights

- Recent One-time Customers contribute the largest share of recorded payment value at 38.48%.
- High-Value One-time Lapsed Customers contribute 32.63%, making them a potentially valuable re-engagement audience.
- Needs Attention contributes 18.80%.
- The top three segments collectively account for 89.91% of recorded payment value.
- Champions have the highest average monetary value but represent only 0.18% of total monetary contribution.
- Hibernating customers have the lowest average monetary value at 55.74.

### Business Implications

- Encourage repeat purchases among Recent One-time Customers.
- Investigate re-engagement opportunities for High-Value One-time Lapsed Customers.
- Prioritize customer engagement strategies based on both segment size and historical spending.
- Consider personalized retention approaches for Champions and Loyal Customers.

### Methodology

Segment monetary contribution was calculated using the `vw_customer_rfm` view.

Monetary represents the sum of recorded payments associated with delivered orders during the available dataset period.

It is not equivalent to profit or accounting revenue.


## Analysis 10: High-Value One-time Lapsed Customers

### Segment Overview

- Total customers in segment: 21,024
- Average recency: 394.51 days
- Average frequency: 1.00 delivered orders
- Average monetary value: 239.34

### Top 20 Customer Findings

- All 20 highest-spending customers in this segment have a Frequency score of 1.
- All have a Monetary score of 5.
- Their Recency scores are either 1 or 2.
- Their historical spending ranges from 3,016.01 to 13,664.08 among the top 20.

### RFM Code Distribution

| RFM Code | Interpretation | Customers |
|---|---|---:|
| 115 | Lowest Recency score, lowest Frequency score, highest Monetary score | 15 |
| 215 | Second-lowest Recency score, lowest Frequency score, highest Monetary score | 5 |

### Business Insights

- Customers can generate substantial historical payment value without becoming repeat purchasers.
- All 20 highest-spending customers in this segment have only one delivered order.
- These customers represent potential re-engagement opportunities because of their historical monetary value.
- High-value lapsed customers may deserve different engagement strategies from low-value inactive customers.

### Suggested Business Action

Consider targeted win-back campaigns based on historical spending, with different incentives for higher-value customers.

### Data Limitation

The dataset covers historical transactions from 2016–2018. The analysis identifies historical customer behaviour and does not establish whether these customers are currently reachable or likely to purchase again.

The monetary metric represents recorded payment value, not profit or complete customer lifetime value.


## Analysis 11: Month 1 Cohort Retention

### Overall Result

The weighted Month 1 retention rate across cohorts with a complete Month 1 observation was approximately 0.48%.

- Eligible cohort customers: 87,214
- Customers returning in Month 1: 421
- Weighted Month 1 retention: 0.48%

### Selected Cohort Results

| Cohort | Cohort Size | Month 1 Returning Customers | Retention |
|---|---:|---:|---:|
| August 2017 | 4,057 | 28 | 0.69% |
| September 2017 | 4,004 | 28 | 0.70% |
| October 2017 | 4,328 | 31 | 0.72% |
| November 2017 | 7,060 | 40 | 0.57% |
| April 2018 | 6,582 | 39 | 0.59% |

### Business Insights

- Month 1 customer retention is consistently low across the observed cohorts.
- October 2017 recorded the highest Month 1 retention among the substantial cohorts shown, at 0.72%.
- Larger acquisition cohorts do not necessarily have higher retention percentages.
- Small cohorts can produce misleadingly high retention percentages. December 2016 recorded 100% retention from a single customer.
- Customer repeat purchasing is an important area for further investigation.

### Methodology

- Customers were assigned to cohorts using their first delivered purchase month.
- Month 1 represents the next calendar month after the cohort month.
- Customers were counted using customer_unique_id.
- Only delivered orders were included.
- The August 2018 cohort was excluded because September 2018 activity is unavailable.
- The overall retention rate uses a weighted calculation across eligible cohort customers.

### Data Limitation

The dataset only contains historical purchase activity through August 2018. Recent cohorts have fewer observable months than older cohorts. Retention comparisons must account for this difference.


## Analysis 12: Weighted Customer Retention by Cohort Age

### Overall Results

The weighted retention analysis shows that repeat purchasing is uncommon across the observed customer cohorts.

| Cohort Age | Eligible Customers | Retained Customers | Weighted Retention |
|---:|---:|---:|---:|
| Month 0 | 93,358 | 93,358 | 100.00% |
| Month 1 | 87,214 | 421 | 0.48% |
| Month 2 | 81,265 | 273 | 0.34% |
| Month 3 | 75,387 | 192 | 0.25% |
| Month 6 | 55,525 | 129 | 0.23% |
| Month 9 | 37,057 | 60 | 0.16% |
| Month 12 | 21,665 | 36 | 0.17% |
| Month 17 | 5,112 | 10 | 0.20% |

### Business Insights

- Month 1 weighted retention is approximately 0.48%, indicating that very few customers make another delivered purchase in the calendar month following their first purchase.
- Retention falls to approximately 0.34% in Month 2 and 0.25% in Month 3.
- From Month 3 onward, retention remains generally low, with modest fluctuations across later cohort ages.
- Retention percentages do not decline in a perfectly straight line because the eligible cohort population changes at each cohort age.
- Later cohort ages have smaller eligible populations. Their percentages should therefore be interpreted cautiously.
- These results suggest that repeat purchasing and customer retention are important areas for further business investigation.

### Methodology

- Cohorts are based on each customer's first delivered purchase month.
- Activity is measured using delivered purchases in each subsequent calendar month.
- Customer identity is determined using customer_unique_id.
- Weighted retention is calculated as total retained customers divided by total eligible customers across the cohorts observable at that cohort age.
- Month 0 represents the initial purchase month and therefore has 100% retention.
- Only observed months are included; future, unobserved months are excluded.

### Data Limitations

This analysis measures monthly purchasing activity, not continuous customer retention. Customers may skip months and return later. The dataset ends in August 2018, meaning later cohort ages contain fewer eligible cohorts and customers.
