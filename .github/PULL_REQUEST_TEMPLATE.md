<!--
Paste this template into the PR description. Keep the headings — they exist
because the answers to them are what a reviewer (including future you) needs.
-->

## What this changes

<!-- One paragraph. What is different after this merges? -->

## Why

<!-- The problem, not the solution. If a test failed or a number moved, say so. -->

## How it was verified

- [ ] `uv run python tasks.py dbt-build` — `ERROR=0`
- [ ] `uv run python tasks.py test`
- [ ] `uv run python tasks.py lint`
- [ ] The claim above was checked against the database, not against the code

<!-- If dbt-build was NOT run, say why. "It was only a docs change" is a valid
     answer. Silence is not. -->

## Evidence

<!--
The numbers. Before and after where a number changed, the query or model it came
from, and the row count that proves it ran against real data rather than an
empty table.

Example:
    late rate        8.11% (7,827 / 96,476)  ->  6.77% (6,535 / 96,476)
    reason           lateness moved from timestamps to whole days
    source           mart_delivery_performance, mart_late_delivery_by_state
-->

## Checklist

- [ ] No data or credentials in the diff
- [ ] New models are described and their keys are tested
- [ ] Any new cast goes through `safe_cast.sql`, not a bare `cast(...)`
- [ ] If a metric definition changed, `docs/metrics.md` changed with it
- [ ] If this was a decision rather than a fix, there is a record in `docs/decisions/`
- [ ] Documented limitations were not silently removed
