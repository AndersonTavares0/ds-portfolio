# 0002 — Fact tables aggregate to the order grain before joining

**Status:** Accepted
**Date:** 2026-10-14

## Situation

`fct_orders` is one row per order, but three of the tables that describe an order
are finer-grained than that:

| Table | Rows | Distinct orders | Rows per order |
|---|---|---|---|
| `order_items` | 112,650 | 98,666 | up to 21 |
| `order_payments` | 103,886 | 99,440 | up to 29 |
| `order_reviews` | 99,224 | 98,673 | occasionally 2+ |

Joining all three onto `orders` in one query produces the **cross product** of
their rows for each order. Every total computed afterwards is inflated, no
database errors, and the result looks entirely reasonable.

Reviews have a second problem: 99,224 review rows cover only 98,673 orders, and
768 orders have no review at all. A join also has to decide *which* review
represents an order, and that decision is invisible unless it is written down.

## Decision

Each finer-grained table is aggregated to the order grain in its own CTE first,
and only then joined. Every `count` and `sum` in `fct_orders` is therefore computed
over a single row per order.

Where an order has more than one review, the **latest** is used:

```sql
row_number() over (
    partition by order_id
    order by review_created_at desc nulls last, review_id desc
) as rn
```

`max(review_score)` was rejected. It would systematically flatter the result: a
customer who complained and was then persuaded to update their review gets the
better score, and the improvement would be indistinguishable from a genuinely
better experience.

## Consequences

- **Costs:** more CTEs and more code than a single join. Reading `fct_orders`
  requires trusting that the aggregation above it is correct — so it is tested.
- **Buys:** every order-level number in the report is safe by construction. The
  `order_value` total equals the payment table's total, the item counts equal the
  item table's, and none of it depends on a reader noticing the grain.
- **Related:** `fct_order_items` has the opposite grain and exists for the
  opposite questions. The rule for a reader is in
  [Metrics](../metrics.md#orders-vs-order-items): orders for counts and money,
  items for products, categories and sellers.
- **Note:** `order_value` is NULL for the one order with no payment row rather than
  zero, so it stays out of averages instead of pulling them down.
