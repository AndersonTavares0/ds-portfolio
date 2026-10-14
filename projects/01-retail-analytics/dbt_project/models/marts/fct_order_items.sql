-- One row per item in an order, enriched with product, category and seller.
--
-- Grain is (`order_id`, `order_item_id`), which is the documented grain of the
-- source table and the level at which `price` and `freight_value` are recorded.
-- Any total built on top of this model must be a SUM of items, never a count of
-- orders: an order with four items would otherwise count its freight once while
-- counting its goods four times.
--
-- `order_item_key` exists because a composite key cannot be tested by dbt's
-- `unique` test directly, and an untested key is a key you are guessing about.

with items as (

    select * from {{ ref('stg_order_items') }}

),

products as (

    select * from {{ ref('stg_products') }}

),

sellers as (

    select * from {{ ref('stg_sellers') }}

),

translation as (

    select * from {{ ref('stg_product_category_translation') }}

),

orders as (

    select
        order_id,
        customer_unique_id,
        customer_state,
        purchased_at

    from {{ ref('fct_orders') }}

),

joined as (

    select
        i.order_id,
        i.order_item_id,
        i.order_id || '-' || i.order_item_id as order_item_key,

        i.product_id,
        p.category_name,

        -- Three of the 74 categories have no English translation. Falling back
        -- to the Portuguese name keeps the revenue visible; defaulting to
        -- 'unknown' would silently hide it inside a bucket nobody would check.
        coalesce(t.category_name_english, p.category_name) as category_name_english,

        i.seller_id,
        s.state as seller_state,

        o.customer_unique_id,
        o.customer_state,
        o.purchased_at,
        date_trunc('month', o.purchased_at)::date as purchased_month,

        i.price,
        i.freight_value,
        i.item_total

    from items i
    left join products p    on i.product_id = p.product_id
    left join sellers s     on i.seller_id = s.seller_id
    left join translation t on p.category_name = t.category_name
    join orders o           on i.order_id = o.order_id

)

select * from joined
