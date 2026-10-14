# Metrics

Every number in the report, defined once. Where two of these could reasonably be
computed differently, the difference is stated — because that difference is
usually the reason two people disagree about the same dataset.

All monetary values are in Brazilian reais (R$), as recorded in the source.

---

## Revenue

**Definition.** The sum of `payment_value` across every payment row for an order,
aggregated to the order first, then summed by month. Computed in
`mart_revenue_monthly.revenue_brl`.

**This is gross merchandise value as recorded by the payment system.** It is not
profit, not margin, and not net of anything — this dataset contains no cost data,
no returns and no refunds.

**It includes orders that were later cancelled or marked unavailable**, because a
payment was recorded for them. That is roughly 3% of orders. The report states
this rather than implying that "revenue" means delivered-and-kept revenue.

**It includes freight**, which is what the customer actually paid. Where freight
must be excluded, `mart_category_revenue.revenue_brl` uses item price only — see
below.

---

## Order value

**Definition.** `fct_orders.order_value` — the same payment total as above, at the
order grain. NULL for orders with no payment row (there is exactly one such order
in this dataset).

**A missing amount is not a zero amount.** Leaving it NULL keeps it out of
averages instead of pulling them down with an order that was never paid.

---

## Average order value

**Definition.** `mart_revenue_monthly.avg_order_value_brl` = mean `order_value`
across the orders in that month.

**Read it as an average over orders placed, not over orders completed.** A month
with many cancellations still counts those orders in the denominator.

---

## Category revenue

**Definition.** `mart_category_revenue.revenue_brl` = the sum of item `price` for
that category. Built from items, never from orders.

**Freight is excluded, deliberately.** One shipment can carry items from several
categories and the freight is charged once for the whole order, so there is no
honest way to attribute it per category. Spreading it with an invented rule would
produce a number that looks precise and is not.

**Categories therefore do not sum to total revenue.** The gap is freight. This is
expected, not a bug.

**Three of the 74 categories have no English translation.** They keep their
Portuguese names rather than being folded into "unknown", so their revenue stays
visible and checkable.

---

## Late delivery

**Definition.** `fct_orders.is_late` — TRUE when the delivery date is later than
the promised date. `fct_orders.days_late` is the difference **in whole days**:
negative is early, `0` is on the promised day, positive is the number of days
late.

**Counted in whole days, and this is the least obvious definition here.** Every
one of the 99,441 estimates in the source is stored at exactly `00:00:00` — a date
sitting in a timestamp column — while all 96,476 actual deliveries carry a real
time. Comparing instants would judge a customer's delivery against a precision the
promise never had: 1,292 orders that arrived on the promised day, at 00:03 for
instance, would be counted as late. Full reasoning and the measurement are in
[decision 0003](decisions/0003-lateness-in-whole-days.md).

**Never delivered is its own outcome, and it is not "on time".** Orders
cancelled, unavailable or still in transit at the end of the snapshot have
`is_late = NULL`. They are reported as `never delivered` rather than dropped,
because for the customer they are the worst outcome available, and dropping them
would flatter the delivery record.

---

## Late percentage

**Definition.** `mart_late_delivery_by_state.late_pct` = late orders ÷ delivered
orders × 100, for that state.

**The denominator is deliveries, not orders.** An order that was never delivered
cannot be late.

**It is NULL, not 0, where nothing was delivered.** A state with no deliveries
must not be able to rank as "perfect" by arithmetic accident. The
`delivered_orders` count is published next to the rate so a reader can tell a real
8% from a 1-in-12.

---

## Review score

**Definition.** `review_score`, an integer 1–5, left by the customer.

**Aggregates use `avg()` and are reported to three decimals**, because scores are
integers and a two-decimal average hides a real difference between 4.296 and
4.30.

**Reviews are self-selected.** Only customers who chose to write one appear. This
is not the satisfaction of the population, and the report says so.

**One review per order is used in `fct_orders`, not all of them.** 99,224 review
rows cover 98,673 distinct orders, so a direct join would inflate order counts,
and 768 orders have no review at all. Where an order has more than one review, the
**latest** is used — chosen over the maximum, which would systematically flatter
the result. See [decision 0002](decisions/0002-aggregate-to-the-order-grain.md).

**The distribution is bimodal** — 57,328 fives against 11,424 ones — which is why
`pct_review_score_le2` accompanies every average. A mean of 4.3 is consistent with
both a happy marketplace and a polarised one.

---

## Active customer

**Definition.** A distinct `customer_unique_id` that placed at least one order in
the period.

**The person, not the order.** `customer_id` is assigned per order, so counting it
would make every customer look new every time they returned. See
[decision 0004](decisions/0004-the-customer-is-customer-unique-id.md).

---

## Repeat-purchase rate

**Definition.** Customers with more than one order ÷ all customers.

**Measured: 3.12%** — 2,997 of 96,096 people. This is the project's least
comfortable finding and it is stated as a headline rather than buried: the
overwhelming majority of this marketplace's customers buy once.

**It is a floor, not a ceiling.** `customer_unique_id` is derived by the source
system and imperfect; a person who changes their details may be counted twice,
which would make retention look better, not worse.

---

## Cohort retention

**Definition.** `mart_cohort_retention.retention_pct` = customers from a cohort who
ordered again in a given month ÷ the size of that cohort × 100. The cohort is the
month of a customer's **first** order; `month_offset` is how many months later
they returned.

**Offset 0 is 100% by construction** — it is the acquisition month itself. It is
not a finding, and it is asserted by a test, because an offset-0 that is *not*
100% means the cohort logic is broken rather than that the business changed.

**Offsets are counted on the calendar**, not in days, so a 30-day month cannot
create an off-by-one.

**Counted in distinct people**: a customer who ordered twice in one month is one
retained customer, not two.

---

## RFM

**Definition.** Each customer scored 1–5 on Recency, Frequency and Monetary with
`ntile(5)`, plus a segment label. In `mart_rfm`.

**Direction of the scores, which is the trap.** Recency is *days since* the last
order, so smaller is better and the scores are ordered descending — `r_score = 5`
is the **most recent** customer. Frequency and Monetary are ascending, so 5 is the
best. Getting one of these backwards produces a working model with no error
message that quietly ranks the best customers as the worst.

**The snapshot date is the day after the last order in the data**, so no customer
can have a negative recency.

**`f_score` is close to meaningless here and is labelled as such.** 96.9% of
customers ordered exactly once, so nearly everyone ties, and `ntile` splits a tied
mass arbitrarily. It is kept because that flatness *is* the finding — but no
segment chart should be presented as though Frequency discriminated.

---

## Orders vs order items

**Two grains exist and mixing them is the most likely way to get a wrong total.**

- `fct_orders` — one row per order. Use it for counts of orders, order value and
  delivery outcomes.
- `fct_order_items` — one row per item. Use it for anything about products,
  categories or sellers.

An order with four items appears once in `fct_orders` and four times in
`fct_order_items`. Summing freight from the items table while counting orders from
the orders table would count the freight once per item.
