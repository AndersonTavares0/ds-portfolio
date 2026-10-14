-- Singular test: review scores are the 1-5 star scale, with nothing else.
-- An out-of-range score would either be a data error or a sign that the
-- scoring convention changed upstream.

select
    review_id,
    order_id,
    review_score
from {{ ref('stg_order_reviews') }}
where review_score not between 1 and 5
