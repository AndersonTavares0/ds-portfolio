# dbt project — Olist

Transforms the `raw` schema (nine CSVs, every column TEXT) into a tested star
schema in `analytics_staging` and `analytics_marts`.

## Running it

Always go through the task runner — it loads `.env` into the environment first,
which dbt does not do by itself:

```bash
uv run python tasks.py dbt-build    # build + test
uv run python tasks.py dbt-docs     # generate the docs site
```

Equivalent direct commands (note both `--project-dir` and `--profiles-dir`):

```bash
dbt build --project-dir projects/01-retail-analytics/dbt_project \
          --profiles-dir projects/01-retail-analytics/dbt_project
```

## Where things live

| Path | Purpose |
|---|---|
| `dbt_project.yml` | Project config; staging is views, marts are tables |
| `profiles.yml` | Postgres connection, read from environment variables |
| `models/staging/` | One view per raw table: cast, rename, normalise |
| `models/staging/schema.yml` | Column contracts and generic tests |
| `models/staging/_olist__sources.yml` | Declares the `raw` schema as dbt sources |
| `models/marts/` | Dimensions, facts and business marts |
| `tests/` | Singular tests for rules SQL cannot express declaratively |

## Conventions

- **Schema naming.** The profile sets `schema: analytics`; `+schema: staging` and
  `+schema: marts` therefore produce `analytics_staging` and `analytics_marts`.
- **Model naming.** `stg_` for staging, `dim_` / `fct_` for the star schema,
  `mart_` for a business-facing result.
- **Every model has a description.** `dbt docs` is the documentation; if it is
  wrong, the documentation is wrong.
- **A key that is not tested is a key you are guessing about.** Primary keys get
  `unique` + `not_null`; foreign keys get `relationships`.

## Notes on the data

- `stg_geolocation` is deliberately **not** deduplicated — there are many rows per
  zip-code prefix. Aggregate before joining, or you will multiply your rows.
- `customer_id` is per-order. `customer_unique_id` is the actual person.
- Raw column typos from the source (`product_name_lenght`) are corrected in
  staging, not in the source declaration, so it stays obvious what upstream
  actually sent.
