# Data dictionary

Two layers matter to a reader: `raw`, which is what arrived, and
`analytics_marts`, which is what the report queries. `analytics_staging` sits
between them and is deliberately uninteresting — one view per raw table whose only
job is to cast, rename and normalise.

All monetary values are in Brazilian reais (R$).

---

## Layer: `raw`

Nine CSVs from the Olist Brazilian E-Commerce dataset, loaded by
`scripts/load_raw.py`. **Every column is TEXT.** Casting happens once, in staging,
where it is visible and tested — see
[decision 0001](decisions/0001-raw-columns-stay-text.md).

Empty cells arrive as **empty strings, not NULL**, which is why every cast in
staging goes through the `safe_*` macros.

| Table | Rows | Grain |
|---|---|---|
| `orders` | 99,441 | one order |
| `customers` | 99,441 | one order's customer record |
| `order_items` | 112,650 | one item in one order |
| `order_payments` | 103,886 | one payment against one order |
| `order_reviews` | 99,224 | one review |
| `products` | 32,951 | one product |
| `sellers` | 3,095 | one seller |
| `geolocation` | 1,000,163 | one zip-code prefix observation |
| `product_category_name_translation` | 71 | one category |

Source, licence and the pinned revision are in
[acknowledgements.md](acknowledgements.md). The data is not version-controlled.

---

## Layer: `analytics_staging`

One view per raw table, named `stg_<table>`. Each casts the TEXT columns to their
real types via the `safe_*` macros and renames them. Notable renames:

| Raw | Staging | Why |
|---|---|---|
| `order_purchase_timestamp` | `purchased_at` | Events are named for when they happened |
| `product_name_lenght` | `name_length` | The source misspells it; staging fixes it so downstream is readable, while the source declaration keeps the original so it stays obvious what upstream sent |
| `review_comment_title` | `comment_title` | Consistent naming |
| `customer_zip_code_prefix` | `zip_code_prefix` | The table is already the customer's |

`stg_geolocation` is **not deduplicated** — roughly one million rows describe
around nineteen thousand zip-code prefixes, and the city spelling varies. Aggregate
before joining it, or a join will multiply your rows.

---

## Layer: `analytics_marts`

### `fct_orders` — one row per order

The central table. Items, payments and reviews are aggregated to the order grain
**before** being joined, so nothing is double-counted.

| Column | Meaning |
|---|---|
| `order_id` | Primary key |
| `customer_unique_id` | The person. See [decision 0004](decisions/0004-the-customer-is-customer-unique-id.md) |
| `customer_city`, `customer_state` | Delivery address |
| `order_status` | One of: delivered, shipped, canceled, unavailable, invoiced, processing, created, approved |
| `purchased_at`, `approved_at`, `handed_to_carrier_at`, `delivered_to_customer_at`, `estimated_delivery_at` | The order's lifecycle. The delivered and estimated columns are NULL for undelivered orders |
| `delivery_days` | Purchase to delivery, in days, **unrounded**. NULL when undelivered |
| `days_late` | Delivery date minus promised date, in **whole days**. Negative is early, 0 is on the promised day. NULL when undelivered |
| `is_late` | TRUE when `days_late > 0`. NULL when undelivered |
| `item_count`, `product_count`, `seller_count` | Distinct counts over the order's items |
| `items_value` | Sum of item prices |
| `freight_value` | Sum of freight on the order |
| `payment_count` | Number of payment rows |
| `order_value` | Sum of payments. **NULL, not 0, for the one order with no payment row** |
| `review_score` | The **latest** review's score. NULL for the 768 orders never reviewed |

### `fct_order_items` — one row per item

| Column | Meaning |
|---|---|
| `order_id`, `order_item_id` | Composite grain |
| `order_item_key` | `order_id || '-' || order_item_id`, so the composite grain can be `unique`-tested |
| `product_id`, `category_name` | Product and its Portuguese category |
| `category_name_english` | English category, falling back to Portuguese for the 3 untranslated ones |
| `seller_id`, `seller_state` | Who sold it and where they are |
| `customer_unique_id`, `customer_state` | Denormalised for convenience |
| `purchased_at`, `purchased_month` | When it was bought |
| `price`, `freight_value`, `item_total` | `item_total` is `price + freight_value` |

### `dim_customers` — one row per person

| Column | Meaning |
|---|---|
| `customer_unique_id` | Primary key |
| `order_count` | Orders placed |
| `first_order_at`, `last_order_at` | Lifespan |
| `city`, `state` | From the **most recent** order, because people move and `min`/`max` over strings would pick alphabetically |

### `mart_revenue_monthly` — one row per month

`month`, `orders`, `active_customers`, `revenue_brl`, `freight_brl`,
`avg_order_value_brl`. 2016 is retained and labelled: the operation effectively
begins in October 2016, so the 2017 growth is the start of the marketplace rather
than a sudden surge in demand.

### `mart_category_revenue` — one row per English category

`category`, `orders`, `items`, `products`, `revenue_brl`,
`avg_item_price_brl`. Built from items. **Freight is excluded**, so categories do
not sum to total revenue — see [Metrics](metrics.md#category-revenue).

### `mart_rfm` — one row per person

`customer_unique_id`, `last_order_date`, `recency_days`, `frequency`, `monetary`,
`r_score`, `f_score`, `m_score`, `rfm_segment`.

`r_score = 5` is the **most recent** customer. `f_score` is nearly
non-discriminating because 96.9% of customers ordered once — see
[Metrics](metrics.md#rfm).

### `mart_cohort_retention` — one row per (cohort, month offset)

`cohort_month`, `month_offset`, `cohort_offset_key`, `cohort_customers`,
`active_customers`, `retention_pct`. Offset 0 is 100% by construction.

### `mart_delivery_performance` — one row per delivery outcome

`delivery_bucket`, `bucket_order`, `orders`, `pct_of_orders`, `reviewed_orders`,
`avg_review_score`, `pct_review_score_le2`, `avg_delivery_days`.

Buckets: `on time`, `late: up to 7 days`, `late: 8 to 14 days`,
`late: more than 14 days`, `never delivered`. `bucket_order` exists so charts sort
by severity instead of alphabetically.

### `mart_late_delivery_by_state` — one row per customer state

`customer_state`, `delivered_orders`, `late_orders`, `late_pct`,
`avg_delivery_days`, `avg_review_score`. `late_pct` is NULL where nothing was
delivered, and the denominator is published next to the rate.

### `mart_late_delivery_by_lane` - one row per (seller state, customer state)

`seller_state`, `customer_state`, `lane` (the label `SP -> RJ`, which is also the
uniqueness key), `is_intrastate`, `delivered_orders`, `late_orders`, `late_pct`,
`avg_handling_days`, `avg_transit_days`, `avg_delivery_days`, `p50_delivery_days`,
`p90_delivery_days`, `promised_days`, `avg_review_score`, `avg_days_late_when_late`,
`orders_over_2w_late`, `late_pct_if_promise_plus3`, `late_pct_if_promise_plus7`.

Covers the 96,411 of 96,476 delivered orders whose items all came from sellers in a
single state; an order spanning two seller states has no single lane and is left
out. The handling/transit split and the promise counterfactuals are defined in
[metrics.md](metrics.md).
