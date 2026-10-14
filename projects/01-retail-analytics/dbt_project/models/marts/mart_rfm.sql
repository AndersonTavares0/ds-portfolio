-- RFM segmentation: one row per person. Recency, Frequency, Monetary, each
-- scored 1-5, plus a segment label.
--
-- WHY THE SCORES ARE EASY TO GET BACKWARDS, AND WHY THAT MATTERS:
--   * Recency is days SINCE the last order, so SMALLER is better. Ordering
--     DESCENDING puts the least recent customer first, which lands them in
--     bucket 1 — so `r_score = 5` means "most recent". Order ascending instead
--     and the segmentation still runs, still produces segments, and quietly
--     ranks your best customers as your worst. There is no error message.
--   * Frequency and Monetary are ordered ascending, so bucket 5 is the best.
--
-- `f_score` is close to worthless in this dataset, and the report says so rather
-- than presenting a segment chart as though it meant something: 96.9% of people
-- ordered exactly once, so almost everybody lands in the same bucket and `ntile`
-- splits that tied mass arbitrarily. It is kept because the flatness IS the
-- finding — but it must not be presented as a discriminating signal.
--
-- The snapshot date is the day after the last order in the data, so no customer
-- can have a negative recency.

with customer_orders as (

    select
        customer_unique_id,
        max(purchased_at)::date as last_order_date,
        count(*)                as frequency,
        sum(order_value)        as monetary

    from {{ ref('fct_orders') }}
    group by customer_unique_id

),

snapshot as (

    select max(purchased_at)::date + 1 as snapshot_date
    from {{ ref('fct_orders') }}

),

with_recency as (

    select
        co.customer_unique_id,
        co.last_order_date,
        co.frequency,
        round(co.monetary, 2)                     as monetary,
        s.snapshot_date - co.last_order_date      as recency_days

    from customer_orders co
    cross join snapshot s

),

scored as (

    select
        *,
        ntile(5) over (order by recency_days desc) as r_score,
        ntile(5) over (order by frequency asc)     as f_score,
        ntile(5) over (order by monetary asc)      as m_score

    from with_recency

)

select
    customer_unique_id,
    last_order_date,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,

    case
        when r_score >= 4 and m_score >= 4 then 'Champions'
        when r_score >= 4 and f_score <= 2 then 'New / promising'
        when r_score <= 2 and f_score >= 3 then 'At risk (was valuable)'
        when r_score <= 2 and m_score <= 2 then 'Lost / low value'
        else 'Others'
    end as rfm_segment

from scored
