-- Monthly cohort retention: one row per (cohort, month offset).
--
-- The cohort is the month of a customer's FIRST order. `month_offset` is how
-- many months later they came back and ordered again. Offset 0 is therefore the
-- acquisition month itself and is 100% by construction — which is exactly what
-- `assert_month_zero_retention_is_full` guards, because an offset-0 retention
-- that is not 100% means the cohort logic is broken, not that the business is.
--
-- Counts are DISTINCT people: a customer who orders twice in one month is one
-- retained customer, not two.
--
-- `date_trunc('month', ...)` is applied to `purchased_at`, so an order is
-- attributed to the month the customer bought, not the month it was delivered.
--
-- `cohort_offset_key` exists so the composite grain can be tested by a `unique`
-- test, which cannot take two columns on its own.

with first_orders as (

    select
        customer_unique_id,
        min(date_trunc('month', purchased_at)::date) as cohort_month

    from {{ ref('fct_orders') }}
    group by customer_unique_id

),

activity as (

    select
        f.customer_unique_id,
        fo.cohort_month,
        date_trunc('month', f.purchased_at)::date as activity_month

    from {{ ref('fct_orders') }} f
    join first_orders fo on f.customer_unique_id = fo.customer_unique_id

),

cohort_activity as (

    select
        cohort_month,
        activity_month,

        -- Whole months between the two month-starts. Counting on the calendar
        -- rather than in days avoids the off-by-one that a 30-day month creates.
        (
            (extract(year  from activity_month) - extract(year  from cohort_month)) * 12
            + (extract(month from activity_month) - extract(month from cohort_month))
        )::int as month_offset,

        count(distinct customer_unique_id) as active_customers

    from activity
    group by cohort_month, activity_month, month_offset

),

cohort_size as (

    select
        cohort_month,
        count(*) as cohort_customers

    from first_orders
    group by cohort_month

)

select
    ca.cohort_month,
    ca.month_offset,
    ca.cohort_month || '-' || ca.month_offset  as cohort_offset_key,
    cs.cohort_customers,
    ca.active_customers,
    round(100.0 * ca.active_customers / cs.cohort_customers, 2) as retention_pct

from cohort_activity ca
join cohort_size cs on ca.cohort_month = cs.cohort_month
