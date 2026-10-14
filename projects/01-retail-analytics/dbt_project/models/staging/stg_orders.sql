-- Order lifecycle and status. One row per order.
-- All raw columns are TEXT, so every cast is explicit and reviewable here.
-- Empty timestamps (e.g. an order that was never approved) become NULL.

with source as (

    select * from {{ source('olist_raw', 'orders') }}

),

renamed as (

    select
        order_id,
        customer_id,
        order_status,

        {{ safe_timestamp('order_purchase_timestamp') }}      as purchased_at,
        {{ safe_timestamp('order_approved_at') }}             as approved_at,
        {{ safe_timestamp('order_delivered_carrier_date') }}  as handed_to_carrier_at,
        {{ safe_timestamp('order_delivered_customer_date') }} as delivered_to_customer_at,
        {{ safe_timestamp('order_estimated_delivery_date') }} as estimated_delivery_at

    from source

)

select * from renamed
