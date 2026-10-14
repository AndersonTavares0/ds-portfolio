-- A cohort's acquisition month must retain 100% of the cohort: every customer
-- definitionally ordered in the month they were acquired.
--
-- If this fails, the cohort logic is broken — not the business. It is the one
-- invariant that separates "retention is genuinely terrible" from "retention was
-- computed wrong", and without it a bug that halves every retention number would
-- still produce a chart that looks like a finding.
--
-- A singular test fails when it returns rows, so this selects the offenders.

select
    cohort_month,
    month_offset,
    cohort_customers,
    active_customers,
    retention_pct

from {{ ref('mart_cohort_retention') }}
where month_offset = 0
  and retention_pct <> 100
