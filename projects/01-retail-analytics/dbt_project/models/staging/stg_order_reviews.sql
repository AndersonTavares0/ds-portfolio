-- Review score and free-text comment (Portuguese).
-- Empty comments arrive as empty strings from the loader and are normalised to
-- NULL here, so downstream code can use `is null` instead of guessing.

with source as (

    select * from {{ source('olist_raw', 'order_reviews') }}

),

renamed as (

    select
        review_id,
        order_id,
        {{ safe_integer('review_score') }}                     as review_score,
        nullif(trim(review_comment_title), '')                 as comment_title,
        nullif(trim(review_comment_message), '')               as comment_message,
        {{ safe_timestamp('review_creation_date') }}           as review_created_at,
        {{ safe_timestamp('review_answer_timestamp') }}        as review_answered_at

    from source

)

select * from renamed
