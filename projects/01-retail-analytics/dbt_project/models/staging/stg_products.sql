-- Product attributes.
-- The source column names contain two original typos: `product_name_lenght`
-- and `product_description_lenght`. They are kept in the source and corrected
-- here, which is exactly what a staging layer is for.
--
-- Several of these attributes are genuinely missing for some products, so the
-- safe casts matter: without them, a missing weight fails the whole build.

with source as (

    select * from {{ source('olist_raw', 'products') }}

),

renamed as (

    select
        product_id,
        product_category_name                            as category_name,
        {{ safe_integer('product_name_lenght') }}        as name_length,
        {{ safe_integer('product_description_lenght') }} as description_length,
        {{ safe_integer('product_photos_qty') }}         as photos_qty,
        {{ safe_integer('product_weight_g') }}           as weight_grams,
        {{ safe_integer('product_length_cm') }}          as length_cm,
        {{ safe_integer('product_height_cm') }}          as height_cm,
        {{ safe_integer('product_width_cm') }}           as width_cm

    from source

)

select * from renamed
