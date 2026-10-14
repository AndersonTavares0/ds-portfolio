-- One row per item inside an order.

with source as (

    select * from {{ source('olist_raw', 'order_items') }}

),

renamed as (

    select
        order_id,
        {{ safe_integer('order_item_id') }}        as order_item_id,
        product_id,
        seller_id,
        {{ safe_timestamp('shipping_limit_date') }} as shipping_limit_at,

        {{ safe_numeric('price') }}         as price,
        {{ safe_numeric('freight_value') }} as freight_value,
        {{ safe_numeric('price') }}
            + {{ safe_numeric('freight_value') }} as item_total

    from source

)

select * from renamed
