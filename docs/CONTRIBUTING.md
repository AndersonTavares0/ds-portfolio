# Contributing

This repository is a portfolio, but it is run like a small production project —
because the habits are the point. These are the habits.

## The workflow

**`main` is never committed to directly.** Every change arrives by pull request,
including changes made by one person working alone. The reason is not ceremony: a
branch is where CI can run before the change is permanent, and a pull request is
where the *why* gets written down somewhere other than in someone's head.

```bash
git switch -c <type>/<short-description>    # e.g. feat/rfm-segmentation
# ... make the change ...
uv run python tasks.py test
uv run python tasks.py lint
uv run python tasks.py dbt-build
git commit -m "feat: add RFM segmentation mart"
git push -u origin HEAD
gh pr create --fill
gh pr merge --merge --delete-branch
```

Branch and commit types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`,
`perf`. A commit that fixes a bug says which bug, and what the symptom was.

## Before opening a pull request

```bash
uv run python tasks.py doctor      # is Docker running, is the data there
uv run python tasks.py dbt-build   # models AND tests — never `dbt run`
uv run python tasks.py test        # pytest
uv run python tasks.py lint        # ruff check + format --check
```

All four should pass. If `dbt-build` reports `ERROR=0` and lint is clean, the pull
request is ready.

**`dbt build`, not `dbt run`.** `dbt run` proves the SQL compiles. `dbt build` runs
the tests, which is what proves the data agrees with what the SQL assumes. The five
errors and one wrong definition this project has already caught were all caught
this way — see [the decision log](docs/decisions/README.md).

## Adding a model

1. Decide the layer. Staging = one view per raw table, cast and rename only,
   no joins and no business logic. Marts = the tables a person queries.
2. Follow the prefix convention: `stg_`, `dim_`, `fct_`, `mart_`.
3. **Never cast a raw column directly.** Use `safe_timestamp`, `safe_integer` or
   `safe_numeric` from `macros/safe_cast.sql`. Empty cells are empty strings, not
   NULL.
4. Describe the model, and test its keys: `unique` + `not_null` on primary keys,
   `relationships` on foreign keys, `accepted_values` on enumerations.
5. If the model encodes a business rule SQL cannot express declaratively, add a
   singular test in `dbt_project/tests/` named `assert_<rule>.sql`. It fails when it
   returns rows, so write it to select the offending rows.
6. Verify the column names against the database, not from memory:

   ```bash
   docker exec ds-portfolio-db psql -U portfolio -d olist -tAc \
     "select column_name from information_schema.columns
      where table_schema='raw' and table_name='orders' order by ordinal_position"
   ```

## Changing a definition

Metric definitions live in [docs/metrics.md](docs/metrics.md). If a change alters
what a number means, that document is part of the change — a number whose
definition is not written down is a number two people will compute differently.

If the change is a *decision* rather than a fix, add a record to
[docs/decisions](docs/decisions/README.md). Do not edit an existing record to
reflect a new decision; add a new one and mark the old one superseded.

## What not to do

- **Do not commit data or credentials.** `data/` and `.env` are ignored. The
  dataset is non-commercial and is not redistributed here.
- **Do not delete a failing test to get a green build.** Decide deliberately
  whether the model or the test is wrong, and say which in the commit message.
- **Do not add `[build-system]` to `pyproject.toml`.** Project 01 is deliberately
  a plain source tree, not an installable package; `retail` is importable via
  `PYTHONPATH`, set by pytest and by the task runner.
- **Do not quietly drop a documented limitation.** If a caveat stops being true,
  change it in the open, in the same pull request.

## Reporting something

Use the [issue templates](../.github/ISSUE_TEMPLATE/). They ask for what is needed
to reproduce a problem — the command, the output, and what success would have
looked like. An issue that says "it doesn't work" costs a round trip to even
understand.
