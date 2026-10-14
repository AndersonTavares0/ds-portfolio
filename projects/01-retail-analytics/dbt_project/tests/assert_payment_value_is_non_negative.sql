-- Singular test: a payment can never be negative.
-- A singular test FAILS when it returns any row, so the query selects the
-- offending rows rather than counting them.

select
    order_id,
    payment_sequential,
    payment_value
from {{ ref('stg_order_payments') }}
where payment_value < 0
