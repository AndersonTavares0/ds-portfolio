-- One row per order: who bought, what was paid, what was promised, what actually
-- happened, and how the customer scored it.
--
-- Grain is `order_id`, and that is the entire reason this model exists. The item,
-- payment and review tables are all *finer* than an order:
--   * an order has one row per item (order x product x seller),
--   * an order can be paid with several methods (a voucher plus a credit card),
--   * the source has 99,224 review rows for 98,673 orders.
-- Joining any of them straight onto `stg_orders` multiplies rows and inflates
-- every total, so each is aggregated to one row per order first.
--
-- Revenue is the payment table, the only place an amount actually collected is
-- recorded. Item prices cover goods and freight but say nothing about vouchers
-- or instalments, so both are kept and can be compared against each other.
--
-- One order has no payment row at all, so `order_value` is NULL for it. NULL is
-- kept rather than replaced with 0: a missing amount is not a zero amount.

with orders as (

    select * from {{ ref('stg_orders') }}

),

customers as (

    select * from {{ ref('stg_customers') }}

),

items as (

    select
        order_id,
        count(*)                   as item_count,
        count(distinct product_id) as product_count,
        count(distinct seller_id)  as seller_count,
        sum(price)                 as items_value,
        sum(freight_value)         as freight_value

    from {{ ref('stg_order_items') }}
    group by order_id

),

payments as (

    select
        order_id,
        count(*)           as payment_count,
        sum(payment_value) as order_value

    from {{ ref('stg_order_payments') }}
    group by order_id

),

-- One score per order. 551 orders carry more than one review row, so a choice
-- has to be made and this is it: the LATEST review wins, on the reading that a
-- customer's final word is their real opinion. Taking the maximum instead would
-- systematically flatter the result. `nulls last` keeps rows with no timestamp
-- from winning the ordering by accident.
reviews as (

    select
        order_id,
        review_score

    from (
        select
            order_id,
            review_score,
            row_number() over (
                partition by order_id
                order by review_created_at desc nulls last, review_id desc
            ) as rn

        from {{ ref('stg_order_reviews') }}
    ) ranked
    where rn = 1

),

joined as (

    select
        o.order_id,
        c.customer_unique_id,
        c.city  as customer_city,
        c.state as customer_state,

        o.order_status,
        o.purchased_at,
        o.approved_at,
        o.handed_to_carrier_at,
        o.delivered_to_customer_at,
        o.estimated_delivery_at,

        -- Delivery facts stay NULL when an order was never delivered. NULL is
        -- not the same as zero: it keeps undelivered orders out of the delivery
        -- averages instead of pretending they arrived instantly.
        --
        -- Left unrounded on purpose. Rounding a duration before comparing it is
        -- how a four-minute-late delivery becomes "0.00 days late" and then
        -- contradicts the flag computed from the same two timestamps.
        extract(epoch from (o.delivered_to_customer_at - o.purchased_at)) / 86400.0
            as delivery_days,

        -- Lateness is measured in WHOLE DAYS against the date the customer was
        -- promised, and that is deliberate. Verified against the data: all
        -- 99,441 estimates are stored at exactly 00:00:00 — a date sitting in a
        -- timestamp column — while all 96,476 actual deliveries carry a real
        -- time. Comparing instants would judge the customer against a precision
        -- the promise never had, and would count 1,292 orders that arrived on
        -- the promised day (at 00:03, for instance) as late.
        --
        -- In days: negative is early, 0 is on the promised day, positive is the
        -- number of days late. This is the column the report's headline uses.
        case
            when o.delivered_to_customer_at is not null
                then o.delivered_to_customer_at::date - o.estimated_delivery_at::date
        end as days_late,

        -- The flag and the number are derived from the same date subtraction, so
        -- they cannot drift apart. `assert_late_orders_are_later_than_estimate`
        -- holds that line.
        case
            when o.delivered_to_customer_at is not null
                then o.delivered_to_customer_at::date > o.estimated_delivery_at::date
        end as is_late,

        coalesce(i.item_count, 0)    as item_count,
        coalesce(i.product_count, 0) as product_count,
        coalesce(i.seller_count, 0)  as seller_count,
        coalesce(i.items_value, 0)   as items_value,
        coalesce(i.freight_value, 0) as freight_value,

        coalesce(p.payment_count, 0) as payment_count,
        p.order_value,

        r.review_score

    from orders o
    join customers c on o.customer_id = c.customer_id
    left join items i    on o.order_id = i.order_id
    left join payments p on o.order_id = p.order_id
    left join reviews r  on o.order_id = r.order_id

)

select * from joined
