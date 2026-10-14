-- Revenue by month.
--
-- 2016 is kept, not quietly dropped, and the report labels it: the dataset only
-- really begins in October 2016 — 324 orders that month against 45,101 across
-- the whole of 2017. Trimming it would be silent data cleaning; keeping it with
-- a label is honest, and the report says plainly that the 2017 growth is the
-- start of the operation rather than a sudden surge in demand.
--
-- `revenue_brl` is the amount recorded as paid on the payment table. It includes
-- orders later cancelled or marked unavailable, because a payment was recorded
-- for them. That is roughly 3% of orders, and the report states it rather than
-- letting the reader assume revenue means delivered-and-kept revenue.

select
    date_trunc('month', purchased_at)::date as month,
    count(*)                                as orders,
    count(distinct customer_unique_id)      as active_customers,
    round(sum(order_value), 2)              as revenue_brl,
    round(sum(freight_value), 2)            as freight_brl,
    round(avg(order_value), 2)              as avg_order_value_brl

from {{ ref('fct_orders') }}
group by date_trunc('month', purchased_at)::date
