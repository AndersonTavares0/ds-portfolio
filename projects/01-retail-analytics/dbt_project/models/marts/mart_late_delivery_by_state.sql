-- Where lateness actually happens, by the customer's state.
--
-- This model exists to turn the headline ("a late order scores 2.57 instead of
-- 4.30") into something a person can act on ("start here"). A finding that
-- cannot be located is a complaint, not a recommendation.
--
-- `delivered_orders` is the denominator and is exposed rather than filtered,
-- because a state with 12 deliveries and one late order has a 8.3% late rate and
-- nothing to act on. Reporting the count next to the rate is what lets a reader
-- tell those two apart.
--
-- `late_pct` is NULL rather than 0 where nothing was delivered, so a state with
-- no deliveries cannot rank as "perfect" by accident.

select
    customer_state,
    count(*) filter (where delivered_to_customer_at is not null) as delivered_orders,
    count(*) filter (where is_late)                              as late_orders,
    round(
        100.0 * count(*) filter (where is_late)
        / nullif(count(*) filter (where delivered_to_customer_at is not null), 0),
        2
    )                                                            as late_pct,
    round(avg(delivery_days), 2)                                 as avg_delivery_days,
    round(avg(review_score), 3)                                  as avg_review_score

from {{ ref('fct_orders') }}
group by customer_state
