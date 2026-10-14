-- Customer location attached to each order.
-- NOTE: `customer_id` is per-order; `customer_unique_id` is the real person.
-- Repeat-purchase analysis must use `customer_unique_id`.

with source as (

    select * from {{ source('olist_raw', 'customers') }}

),

renamed as (

    select
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix as zip_code_prefix,
        customer_city            as city,
        customer_state           as state

    from source

)

select * from renamed
