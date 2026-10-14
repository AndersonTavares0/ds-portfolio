<!--
This file is the pull request body. Do not retype it — load it:

    gh pr create --template .github/PULL_REQUEST_TEMPLATE.md

Then fill in the sections and tick the boxes you actually ran. GitHub loads this
same file automatically when a pull request is opened through the web interface,
so the body is the same either way.

Two rules:

  * Tick a box only if the command ran.
  * If something was not run, say so under "Not run" rather than leaving a box
    unticked. An empty box and a box that explains itself are different answers.
-->

## What this changes

<!-- One paragraph. What is different after this merges? -->

## Why

<!-- The problem, not the solution. If a test failed or a number moved, say so. -->

## How it was verified

Run these through `tasks.py`. Never call `dbt`, `pytest` or `ruff` directly: the
task runner is what loads `.env` and sets `PYTHONPATH`.

- [ ] `uv run python tasks.py dbt-build` — `ERROR=0`
- [ ] `uv run python tasks.py test`
- [ ] `uv run python tasks.py lint`
- [ ] The claims above were checked against the database, not against the code

**Not run, and why:**

<!-- "It was only a documentation change" is a valid answer. Silence is not. -->

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
