# 0004 — The customer is `customer_unique_id`, not `customer_id`

**Status:** Accepted
**Date:** 2026-10-14

## Situation

The `customers` table has two identifiers, and the one that looks like a customer
key is the wrong one.

| Column | Distinct values | What it actually is |
|---|---|---|
| `customer_id` | 99,441 | Assigned per **order** |
| `customer_unique_id` | 96,096 | The person |

Every table joins on `customer_id`, so it is the natural key to reach for. It is
also one row per order — 99,441 rows for 96,096 people — which means any analysis
keyed on it counts a returning customer as a brand-new one.

## Decision

`customer_unique_id` is the customer key everywhere: `dim_customers`,
`fct_orders.customer_unique_id`, `mart_rfm`, `mart_cohort_retention`, and every
"active customers" count.

`customer_id` still exists in `stg_customers` and `stg_orders` as the join path
between the two source tables. It is never used as an analysis grain.

Because the source does not provide a dimension keyed on the person, `dim_customers`
builds one. Doing this explicitly, once, in a tested model is what makes the error
below impossible to repeat downstream.

## Consequences

- **Buys: the difference between a real finding and a fabricated one.** Keyed on
  `customer_id`, repeat purchase is **0%** — every customer has exactly one order
  by construction, and a retention analysis would report "nobody ever comes back"
  with total confidence. Keyed on `customer_unique_id` it is **3.12%** (2,997 of
  96,096). A low number, but a true one, and the entire retention and RFM analysis
  depends on it.
- **Costs:** `customer_unique_id` is derived by the source system and imperfect. A
  person who changes their details may be counted twice, so 3.12% is a **floor**,
  not an exact figure. This is stated in the report rather than presented as
  precision that does not exist.
- **Also decided here:** city and state in `dim_customers` come from the person's
  **most recent** order. People move, and the alternative — `min()` or `max()` over
  the address strings — would pick an answer alphabetically, which means nothing.
