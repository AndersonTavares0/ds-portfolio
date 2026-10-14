# 0003 — Lateness is measured in whole days

**Status:** Accepted
**Date:** 2026-10-14

## Situation

The first definition of "late" compared timestamps: an order was late when
`delivered_to_customer_at > estimated_delivery_at`. That produced 7,827 late
orders out of 96,476 deliveries — 8.11%.

Then the singular test `assert_late_orders_are_later_than_estimate` failed with six
rows: orders flagged late whose lateness was not positive. The six were deliveries
216 to 349 seconds after the deadline, and the cause of the *failure* was mundane —
`days_late` had been rounded to two decimals, so a four-minute-late delivery became
`0.00`. But looking at those rows to fix them showed something more interesting:

```
       order_id                | delivered_to_customer_at | estimated_delivery_at | seconds_late
 812f59f34238daae0b90419914cecbc1 | 2017-12-12 00:03:36   | 2017-12-12 00:00:00   | 216
 0eae0847dbceff8611d706710c724ee2 | 2017-12-12 00:04:03   | 2017-12-12 00:00:00   | 243
```

Every estimate was at midnight. Measuring the whole column:

| | Count | Distinct times of day |
|---|---|---|
| Estimates | 99,441 | **1** — `00:00:00` |
| Actual deliveries | 96,476 | 96,476 with real times |

The estimate is a **date** stored in a timestamp column. It never had a time of
day to be late against. Comparing instants was judging the customer's delivery
against a precision the promise never made — and **1,292 orders** delivered on the
promised day, at 00:03 for instance, were being counted as late.

## Decision

```sql
case
    when delivered_to_customer_at is not null
        then delivered_to_customer_at::date - estimated_delivery_at::date
end as days_late
```

Negative is early, `0` is on the promised day, positive is days late.

`is_late` is derived from the same subtraction, so the flag and the number cannot
drift apart — which is the invariant the test now holds.

Unrelated but fixed at the same time: `delivery_days` is no longer rounded in the
fact table. Rounding a duration before comparing it is what turned six real
deliveries into "0.00 days late" and made the test fire. Rounding belongs in the
presentation layer, where nothing is ever compared against it again.

## Consequences

- **The headline number changes.** The late rate moves from 8.11% to **6.77%**
  (6,535 of 96,476). Every figure in the report uses the whole-day definition.
- **Costs:** one more concept to explain — `days_late` is not the same as the exact
  elapsed time between the two timestamps. Someone comparing against a raw
  timestamp difference will get a slightly different answer, and the reason is
  written here rather than discovered.
- **Buys:** lateness now matches the promise the customer was actually given. A
  customer told "by the 12th" who receives their parcel at 00:03 on the 12th was
  not let down, and no useful decision follows from pretending otherwise.
- **The general lesson, worth more than the fix:** the numbers moved because a test
  failed. `dbt run` would have compiled all of this cleanly and shipped the wrong
  definition.
