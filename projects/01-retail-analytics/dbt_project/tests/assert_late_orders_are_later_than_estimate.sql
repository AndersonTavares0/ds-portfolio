-- The `is_late` flag and `days_late` number must agree, in both directions.
--
-- This test earned its place: the first version of it failed with 6 rows, and
-- the cause was real. `days_late` had been rounded to 2 decimal places before
-- the comparison, so six deliveries 216-349 seconds after a midnight deadline
-- rounded to `0.00` while the flag, computed from the same timestamps, said
-- "late". Chasing that led to a better finding than the fix itself: every
-- estimate in the source is a date at midnight, so lateness belongs in whole
-- days. The flag and the number now come from one subtraction and cannot drift.
--
-- A singular test fails when it returns rows, so this selects the offenders.

select
    order_id,
    days_late,
    is_late
from {{ ref('fct_orders') }}
where
    -- flagged late, but the number says otherwise
    (is_late is true  and (days_late is null or days_late <= 0))
    -- flagged on time, but the number says otherwise
    or (is_late is false and (days_late is null or days_late > 0))
    -- a number with no flag at all
    or (days_late is not null and is_late is null)
