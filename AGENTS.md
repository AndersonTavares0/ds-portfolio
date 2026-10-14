# AGENTS.md

Instructions for AI coding agents working in this repository. The rules below are
the rules the project actually follows — they are not suggestions, and breaking
one is a bug.

## What this repository is

A data science portfolio. The thesis, stated once:

> In this marketplace, delivery performance drives customer satisfaction and
> retention. I **measured** it (Project 01), **predicted** it (Project 02), and
> **explained the voice of the customer** (Project 03).

Project 01 is a retail analytics pipeline on the Olist Brazilian e-commerce
dataset: raw CSVs → PostgreSQL → dbt → a published report.

The audience is a hiring manager who will give it two minutes. Optimise for
credibility, not for volume of code.

## Layout

| Path | What lives there |
|---|---|
| `tasks.py` | The only entry point, on purpose. Portable and stdlib-only |
| `projects/01-retail-analytics/src/retail/` | Config, dataset manifest, download / validate / load |
| `projects/01-retail-analytics/scripts/` | Thin CLIs over `retail.*` |
| `projects/01-retail-analytics/dbt_project/` | Staging models, marts, macros, tests |
| `site/` | The published website — its own Quarto project, rooted here |
| `site/reports/01-retail-analytics/` | The report and the one-page decision memo |
| `docs/` | Architecture, metric definitions, data dictionary, decision log |
| `docs/CONTRIBUTING.md` | The workflow, and what a complete change looks like |
| `data/` | Downloaded CSVs. Git-ignored. Never committed |

The reasoning behind the code lives in `docs/`. Read the decision log before
changing how something is measured — a choice that looks surprising is usually
there because the data disagreed with the obvious approach.

## Commands

Never invoke the underlying tools directly. Go through the task runner, which
loads `.env` and sets `PYTHONPATH`:

```bash
uv run python tasks.py doctor       # is the environment sane?
uv run python tasks.py db-up        # start PostgreSQL (Docker)
uv run python tasks.py data         # download + validate (~126 MB, once)
uv run python tasks.py load         # CSVs -> the `raw` schema
uv run python tasks.py dbt-build    # models AND tests
uv run python tasks.py test         # Python tests
uv run python tasks.py pipeline     # load -> dbt-build -> test -> render
```

## Hard rules

1. **Never commit data or credentials.** `data/` and `.env` are git-ignored. The
   dataset is CC BY-NC-SA (non-commercial) and must not be redistributed here.
2. **`dbt build`, never `dbt run`.** `build` also runs the tests. A model that
   has never been tested against real data is not finished.
3. **Raw columns stay TEXT.** All casting happens in staging, through the macros
   in `macros/safe_cast.sql`. Never `cast(col as ...)` a raw column directly:
   the loader keeps empty cells as empty strings, so `cast('' as timestamp)`
   raises `invalid input syntax for type timestamp: ""`.
4. **Every model has a description; every key has a test.** `unique` +
   `not_null` for primary keys, `relationships` for foreign keys. A key that is
   not tested is a key you are guessing about.
5. **`customer_unique_id`, never `customer_id`, for anything about customers.**
   `customer_id` is per-order; using it makes every customer look like a
   one-time buyer.
6. **`stg_geolocation` is not deduplicated.** Aggregate before joining or you
   will multiply your rows.
7. **The database host port is 5433, not 5432.** A PostgreSQL installed natively
   on the machine owns 5432 and silently shadows the container's mapping.
8. **Do not silently drop a documented limitation** from a README or a report
   because it makes a result look worse.
9. **Never commit to `main` directly.** Every change arrives by pull request;
   `main` moves only by merging one. A branch is where CI runs before a change
   becomes permanent. That is why every change arrives by pull request. The workflow is in `docs/CONTRIBUTING.md`.
10. **A metric definition lives in `docs/metrics.md`, not in your head.** If a
    change alters what a number means, that document is part of the change.

## Python conventions

- `ruff` with line length 100; `E`, `F`, `W`, `I`, `UP`, `B`, `SIM` enabled.
- Type hints on public functions; docstrings explain *why*, not *what*.
- Project 01 is deliberately **not** an installable package (`[tool.uv] package
  = false`). Packaging arrives in Project 02. Do not add `[build-system]` here.
- Tests must not need the network or a database: use the `files=` override
  parameter that every function in `retail.io` accepts.

## Definition of done

- `uv run python tasks.py dbt-build` → `ERROR=0`
- `uv run ruff check . && uv run ruff format --check .` → clean
- `uv run pytest` → all passing
- Any new model has a description and tested keys
- Any new number in a report is reproducible from the committed SQL
- The change arrived by pull request, and CI passed before it was merged
- A changed metric definition was updated in `docs/metrics.md`
- A change that was a *decision* rather than a fix has a record in `docs/decisions/`

Report a failure instead of routing around it. A silently wrong number is worse
than a red build.

## Project-scoped skills

`.agents/skills/` holds procedures specific to this repository:

- **`run-pipeline`** — bring the stack up, run it, and diagnose the failure modes
  that actually occur here.
- **`add-dbt-model`** — the conventions for adding or changing a model.
