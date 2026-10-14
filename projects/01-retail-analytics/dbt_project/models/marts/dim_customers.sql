-- One row per person.
--
-- `customer_unique_id` is the grain, not `customer_id`. `customer_id` is
-- assigned per order, so a dimension keyed on it would hold 99,441 rows for
-- 96,096 real people, and every repeat-customer count built on it would be zero
-- while looking perfectly reasonable.
--
-- City and state come from the customer's most recent order. People move, and
-- the latest address is the better guess at where they are now; taking `min` or
-- `max` over the strings would instead pick an answer alphabetically, which is
-- meaningless.

with order_customers as (

    select
        o.order_id,
        o.purchased_at,
        c.customer_unique_id,
        c.city,
        c.state

    from {{ ref('stg_orders') }} o
    join {{ ref('stg_customers') }} c on o.customer_id = c.customer_id

),

ranked as (

    select
        *,
        row_number() over (
            partition by customer_unique_id
            order by purchased_at desc, order_id desc
        ) as rn

    from order_customers

)

select
    customer_unique_id,
    count(*)          as order_count,
    min(purchased_at) as first_order_at,
    max(purchased_at) as last_order_at,
    max(case when rn = 1 then city  end) as city,
    max(case when rn = 1 then state end) as state

from ranked
group by customer_unique_id
