-- Singular test: an order cannot be delivered before it was purchased.
-- Catches impossible timestamps, which would silently distort every
-- delivery-time metric in the reports.

select
    order_id,
    purchased_at,
    delivered_to_customer_at
from {{ ref('stg_orders') }}
where delivered_to_customer_at is not null
  and delivered_to_customer_at < purchased_at
