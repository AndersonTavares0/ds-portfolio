# Project 01 — Retail Analytics on Olist

**Question.** Which levers actually move customer satisfaction and repeat purchase
in this marketplace?

**Status.** Data layer complete; analysis in progress.

---

## The argument

Olist is a marketplace: it does not own inventory, it connects sellers to buyers.
That makes **delivery performance** the product's core promise. This project
measures how that promise holds up, and what happens to the customer when it
does not.

Four questions, each answered with SQL against a tested model:

1. **Where does revenue come from?** Order volume, basket size, and the
   seasonality of a Brazilian marketplace (including the November spike).
2. **Who are the customers?** RFM segmentation over
   `customer_unique_id` — not `customer_id`, which is per-order and would make
   every customer look like a one-time buyer.
3. **Do they come back?** Monthly cohort retention. The headline finding is
   brutal: repeat purchase is close to nonexistent in this dataset.
4. **Does delivery performance explain satisfaction?** Delivery-time
   distributions, late-delivery rate, and the relationship between
   `review_score` and lateness.

Deliverables: the [report](../../site/reports/01-retail-analytics/01-business-analytics.qmd)
and a [one-page decision memo](../../site/reports/01-retail-analytics/00-executive-memo.qmd).

---

## Architecture

```
raw CSVs (126 MB, git-ignored)
        │  scripts/load_raw.py      ← every column loaded as TEXT
        ▼
PostgreSQL  schema: raw
        │  dbt
        ▼
analytics_staging   stg_*    views  — cast, rename, normalise
        │
        ▼
analytics_marts     dim_*, fct_*, mart_*   tables — what a business user queries
```

**Why every raw column is TEXT.** Casting belongs in one visible, reviewable,
tested place. It also prevents the classic silent bug where the zip-code prefix
`01001` becomes the integer `1001` and every geographic join quietly breaks.

---

## Layout

| Path | What it is |
|---|---|
| `scripts/download_data.py` | Downloads the nine CSVs from a revision-pinned mirror and validates them |
| `scripts/load_raw.py` | Loads the CSVs into the `raw` schema, all columns as TEXT |
| `src/retail/config.py` | Settings resolved from environment variables / `.env` |
| `src/retail/datasets.py` | The dataset manifest — expected files, sizes, row minimums |
| `src/retail/io.py` | Download, validate, load, verify |
| `dbt_project/models/staging/` | One typed, renamed view per raw table |
| `dbt_project/models/marts/` | The star schema |
| `dbt_project/tests/` | Singular tests for business rules SQL cannot express declaratively |
| `tests/` | Python tests for the data layer |
| `site/` | The published report and decision memo (Quarto project at the repository root of the site) |

---

## Running it

```bash
uv run python tasks.py db-up      # start PostgreSQL
uv run python tasks.py data       # download + validate (once, ~126 MB)
uv run python tasks.py load       # into the `raw` schema
uv run python tasks.py dbt-build  # models + tests
uv run python tasks.py test       # Python tests
```

Or the whole thing: `uv run python tasks.py pipeline`.

---

## Data quality

Data quality is enforced, not assumed:

| Layer | Check | Fails the build when... |
|---|---|---|
| Download | exact byte size per file | a download is truncated |
| Download | minimum row count per file | a file is a partial export |
| dbt | `unique` / `not_null` on primary keys | keys stop being keys |
| dbt | `accepted_values` on `order_status`, `payment_type` | a new category appears |
| dbt | singular tests | a payment is negative, a delivery predates its purchase, a review score falls outside 1–5 |
| pytest | manifest and validator behaviour | the contract in `datasets.py` is broken |

---

## Limitations

Stated now, before the numbers, because they shape how the numbers should be read:

- **The dataset is a snapshot (2016-09 to 2018-10), not a live feed.** Anything
  about 2018 holiday behaviour is one observation, not a trend.
- **`customer_unique_id` is the closest thing to a person, and it is imperfect**
  — it is derived, so a customer who changes their details may appear twice.
- **Reviews are self-selected.** Only customers who chose to leave a review
  appear; their satisfaction is not the satisfaction of the population.
- **No cost, margin, or return data.** "Revenue" throughout means gross
  merchandise value as recorded in the payment table.
- **Delivery timestamps can be missing** for orders that were not delivered, and
  those orders are excluded from delivery-time statistics rather than imputed.
