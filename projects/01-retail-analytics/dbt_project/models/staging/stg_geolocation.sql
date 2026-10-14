-- Zip-code-prefix to coordinates.
--
-- This table has MANY duplicate rows per zip prefix (~1M rows for ~19k
-- prefixes) and the city spelling is inconsistent. It is kept unfiltered here
-- so the duplication is visible; any consumer that needs one coordinate per
-- prefix must aggregate first (see the geo dimension added with the marts).

with source as (

    select * from {{ source('olist_raw', 'geolocation') }}

),

renamed as (

    select
        geolocation_zip_code_prefix                as zip_code_prefix,
        {{ safe_numeric('geolocation_lat', 10, 8) }} as latitude,
        {{ safe_numeric('geolocation_lng', 10, 8) }} as longitude,
        geolocation_city                           as city,
        geolocation_state                          as state

    from source

)

select * from renamed
