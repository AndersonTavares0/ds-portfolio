-- A longer promised window can never make MORE orders late.
--
-- `late_pct_if_promise_plus3` and `late_pct_if_promise_plus7` are counterfactual
-- columns: the share of orders that would still have missed the promise had the
-- promised window been three or seven days longer. They are computed from
-- `days_late` with a shifted threshold, so they are monotone by construction.
-- This test pins that, because the recommendation rests on those two numbers and
-- a slip in either threshold would move the argument without breaking anything
-- that errors.
--
-- A singular test fails when it returns rows, so this selects the offenders.

select
    lane,
    late_pct,
    late_pct_if_promise_plus3,
    late_pct_if_promise_plus7
from {{ ref('mart_late_delivery_by_lane') }}
where late_pct_if_promise_plus3 > late_pct
   or late_pct_if_promise_plus7 > late_pct_if_promise_plus3
