-- Satisfaction by delivery outcome. This is the headline table of the project.
--
-- Buckets are defined by lateness against the ESTIMATE the customer was shown,
-- not by absolute delivery time, because that is the promise the customer
-- experienced and reacted to. A 20-day delivery promised in 25 days is a kept
-- promise; a 5-day delivery promised in 4 is a broken one.
--
-- Lateness is counted in whole days (`days_late`), because every estimate in
-- the source is stored as a date at midnight — so the promise never had a time
-- of day to be late against.
--
-- "never delivered" includes orders cancelled, unavailable, or still in transit
-- at the end of the snapshot. They are kept as their own bucket instead of being
-- filtered out, because for the customer they are the worst outcome of all —
-- dropping them would make the delivery record look better than it is.
--
-- `bucket_order` exists so charts sort by severity rather than alphabetically.

with bucketed as (

    select
        case
            when is_late is null     then 'never delivered'
            when not is_late         then 'on time'
            when days_late <= 7      then 'late: up to 7 days'
            when days_late <= 14     then 'late: 8 to 14 days'
            else 'late: more than 14 days'
        end as delivery_bucket,

        case
            when is_late is null     then 4
            when not is_late         then 0
            when days_late <= 7      then 1
            when days_late <= 14     then 2
            else 3
        end as bucket_order,

        review_score,
        delivery_days

    from {{ ref('fct_orders') }}

)

select
    delivery_bucket,
    min(bucket_order)                                  as bucket_order,
    count(*)                                           as orders,
    round(100.0 * count(*) / sum(count(*)) over (), 2) as pct_of_orders,
    count(*) filter (where review_score is not null)    as reviewed_orders,
    round(avg(review_score), 3)                        as avg_review_score,
    round(
        100.0 * count(*) filter (where review_score <= 2)
        / nullif(count(*) filter (where review_score is not null), 0),
        2
    )                                                  as pct_review_score_le2,
    round(avg(delivery_days), 2)                       as avg_delivery_days

from bucketed
group by delivery_bucket
