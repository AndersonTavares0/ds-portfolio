-- One row per payment method used on an order.
-- An order can have several rows (e.g. a voucher plus a credit card), so summing
-- `payment_value` per order is the correct way to get the order total.

with source as (

    select * from {{ source('olist_raw', 'order_payments') }}

),

renamed as (

    select
        order_id,
        {{ safe_integer('payment_sequential') }}   as payment_sequential,
        payment_type,
        {{ safe_integer('payment_installments') }} as payment_installments,
        {{ safe_numeric('payment_value') }}        as payment_value

    from source

)

select * from renamed
