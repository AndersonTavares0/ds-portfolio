-- Lateness by delivery lane: where the parcel shipped from, and where it went.
--
-- `mart_late_delivery_by_state` locates lateness by destination, which is
-- enough to see that Rio de Janeiro runs at 12.10% against Sao Paulo's 4.49%.
-- It is not enough to act on, because "Rio is late" invites the wrong
-- explanation. Adding the origin separates the two competing stories:
--
--   * If a handful of sellers were the problem, the badness would travel with
--     the seller, so a seller shipping to Rio and to Sao Paulo would be late in
--     both places at a similar rate.
--   * If the route is the problem, the badness travels with the lane, and the
--     same seller is late far more often on one side of the country.
--
-- The report's answer is the lane. The evidence is in this table: handover to
-- the carrier takes about three days on every lane in the dataset
-- (`avg_handling_days`), so sellers are dispatching on schedule whatever the
-- destination, while `avg_transit_days` ranges from under 4 days to nearly 20.
--
-- Grain is (seller_state, customer_state), covering orders whose items all came
-- from sellers in ONE state. An order with items from sellers in two states has
-- no single lane, so it is left out rather than assigned to whichever state
-- sorted first. That is 65 of 96,476 delivered orders.
--
-- `is_intrastate` is kept because it is the comparison that carries the point:
-- every lane inside a single state sits at or below 4.8%, including Rio's own.
--
-- The two `late_pct_if_promise_plus*` columns are counterfactuals, not
-- observations. They answer how many of these orders would still have missed the
-- promise had the promised window been three (or seven) days longer, which is
-- the question behind the recommendation. The denominator is the same as
-- `late_pct`, so the three can be read against each other directly.
--
-- `delivered_orders` is exposed, not filtered, for the same reason as in the
-- by-state model: a lane with 12 deliveries needs its denominator in view, or it
-- ranks as the worst lane on the strength of three parcels.

with seller_state_per_order as (

    -- The seller's state lives on `stg_sellers`, not on the item line, so it is
    -- joined here. Verified before relying on it: every `seller_id` in the item
    -- table has a matching seller, and no seller has a null state, so
    -- `count(distinct state)` cannot undercount the states in an order.
    select
        i.order_id,
        count(distinct s.state) as seller_state_count,
        min(s.state)            as seller_state

    from {{ ref('stg_order_items') }} i
    join {{ ref('stg_sellers') }}     s on s.seller_id = i.seller_id
    group by i.order_id

),

lanes as (

    select
        s.seller_state,
        o.customer_state,
        s.seller_state || ' -> ' || o.customer_state as lane,
        s.seller_state = o.customer_state           as is_intrastate,

        o.is_late,
        o.days_late,
        o.delivery_days,
        o.review_score,

        -- Both halves of the delivery, kept apart. The sum is the customer's
        -- wait; the split is what says whether the seller or the road is late.
        extract(epoch from (o.handed_to_carrier_at - o.purchased_at)) / 86400.0
            as handling_days,
        extract(epoch from (o.delivered_to_customer_at - o.handed_to_carrier_at)) / 86400.0
            as transit_days,

        o.estimated_delivery_at::date - o.purchased_at::date as promised_days

    from {{ ref('fct_orders') }} o
    join seller_state_per_order s on s.order_id = o.order_id

    where o.delivered_to_customer_at is not null
      and s.seller_state_count = 1

)

select
    seller_state,
    customer_state,
    lane,
    is_intrastate,

    count(*)                                                        as delivered_orders,
    count(*) filter (where is_late)                                 as late_orders,
    round(100.0 * count(*) filter (where is_late) / count(*), 2)    as late_pct,

    round(avg(handling_days), 2)                                    as avg_handling_days,
    round(avg(transit_days), 2)                                     as avg_transit_days,
    round(avg(delivery_days), 2)                                    as avg_delivery_days,

    -- The median says whether the typical parcel is slow. The 90th percentile
    -- says whether the slow ones are very slow. On the Sao Paulo to Rio lane the
    -- median matches a much better lane and only the tail is bad, which is the
    -- whole finding.
    round(percentile_cont(0.5) within group (order by delivery_days)::numeric, 1)
                                                                    as p50_delivery_days,
    round(percentile_cont(0.9) within group (order by delivery_days)::numeric, 1)
                                                                    as p90_delivery_days,

    round(avg(promised_days), 1)                                    as promised_days,
    round(avg(review_score), 3)                                     as avg_review_score,
    round(avg(days_late) filter (where is_late), 1)                 as avg_days_late_when_late,
    count(*) filter (where days_late >= 15)                         as orders_over_2w_late,

    round(100.0 * count(*) filter (where days_late >= 4) / count(*), 2)
                                                                    as late_pct_if_promise_plus3,
    round(100.0 * count(*) filter (where days_late >= 8) / count(*), 2)
                                                                    as late_pct_if_promise_plus7

from lanes
group by seller_state, customer_state, lane, is_intrastate
