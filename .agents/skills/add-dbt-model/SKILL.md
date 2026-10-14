---
name: add-dbt-model
description: Conventions for adding or changing a dbt model in this repository — which layer a model belongs to, naming, the safe-cast macros, the schema.yml contract, and the tests a new model needs. Use when adding a staging model, a mart, a dimension or fact, a macro, or a dbt test.
---

# Add or change a dbt model

## Which layer does it belong to?

| Layer | Schema | Materialisation | What belongs there |
|---|---|---|---|
| `models/staging/` | `analytics_staging` | view | One model per raw table. Cast, rename, normalise. No joins, no business logic |
| `models/marts/` | `analytics_marts` | table | Dimensions, facts and business marts. What a business user would query |
| `macros/` | — | — | Reusable SQL, e.g. the safe casts |

Prefixes: `stg_`, `dim_`, `fct_`, `mart_`.

If a question can be answered in staging, it usually should not be a mart. If it
needs a join across raw tables, it does not belong in staging.

## Writing the model

1. Follow the shape already used by the nine staging models: a `source` CTE, a
   `renamed` CTE, then `select * from renamed`. One transformation per line, with
   the source column on the left and the output name on the right.
2. **Never `cast()` a raw column directly.** Use the macros in
   `macros/safe_cast.sql` — `safe_timestamp`, `safe_integer`, `safe_numeric` —
   because empty cells arrive as empty strings.
3. Confirm the real column names against the database rather than from memory.
   The raw tables use prefixed names (`customer_zip_code_prefix`,
   `seller_city`, `review_comment_title`):

   ```bash
   docker exec ds-portfolio-db psql -U portfolio -d olist -tAc \
     "select column_name from information_schema.columns \
      where table_schema='raw' and table_name='orders' order by ordinal_position"
   ```

## Declaring the contract

Every model gets a description in `schema.yml`, and every key gets tests:

```yaml
models:
  - name: stg_orders
    description: "One row per order, with the lifecycle timestamps typed."
    columns:
      - name: order_id
        description: "Primary key."
        data_tests:
          - unique
          - not_null
```

Notes that have already cost time here:

- Use `data_tests:` (current dbt), not the older `tests:` key.
- Generic test arguments go under an `arguments:` key. dbt 1.12 warns otherwise,
  and it is a deprecation, not a style preference.
- **Do not use `quote: false` on `accepted_values` for string values.** It
  renders the values as bare identifiers and the test fails with
  `column "credit_card" does not exist`. It is for non-string values only.

## Tests a new model needs

- Primary key: `unique` + `not_null`.
- Foreign key: `relationships` to the model it points at.
- Enumerations: `accepted_values`.
- Business rules SQL cannot express declaratively: a singular test in
  `dbt_project/tests/`, named `assert_<rule>.sql`. A singular test fails when it
  returns **any** row, so write it to select the offending rows.

## Declaring the marts config

`dbt_project.yml` configures only the `staging` block today. Add the `marts`
block together with the first mart model. Declaring a configuration path before
any model uses it makes dbt warn on every run.

## Verify, do not assume

```bash
uv run python tasks.py dbt-build     # models AND tests
```

`dbt run` alone proves the SQL compiles. `dbt build` proves the data agrees with
your assumptions. Expect `ERROR=0`.

If a test fails, decide deliberately whether the model is wrong or the test is
wrong, and say which in the commit message. Do not delete a failing test to get
a green build.
