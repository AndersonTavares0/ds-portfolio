-- An order with no delivery timestamp must have no delivery duration either.
--
-- This guards the NULL-versus-zero decision. If `delivery_days` were ever
-- coalesced to 0 for undelivered orders, roughly 3,000 cancelled or in-transit
-- orders would enter the delivery averages as instant deliveries and pull the
-- mean down. The number would look better and mean less.
--
-- A singular test fails when it returns rows, so this selects the offenders.

select
    order_id,
    order_status,
    delivered_to_customer_at,
    delivery_days
from {{ ref('fct_orders') }}
where delivered_to_customer_at is null
  and delivery_days is not null
