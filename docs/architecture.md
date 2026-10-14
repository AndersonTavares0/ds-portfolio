# Architecture

## The shape of the repository

```
ds-portfolio/
├── .agents/                      agent procedures scoped to this repository
├── .github/
│   ├── ISSUE_TEMPLATE/           what a useful report looks like
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/                CI and publishing
├── data/                         raw CSVs — git-ignored, with a README explaining the source
├── docs/                         governance, metrics, dictionary, decisions, contributing
├── projects/
│   └── 01-retail-analytics/
│       ├── dbt_project/          staging views and mart tables
│       ├── scripts/              thin entry points (download, load, charts)
│       ├── src/retail/           the data layer as importable modules
│       └── tests/                Python tests, no network and no database required
├── site/                         the published narrative — its own Quarto project
│   ├── reports/01-retail-analytics/  the report and the one-page decision memo
│   └── _quarto.yml, index.qmd, about.qmd, styles.css
├── AGENTS.md                     the rules an agent (or a person) works to here
├── README.md                     portfolio landing page
├── docker-compose.yml            PostgreSQL, and nothing else
├── pyproject.toml                dependencies and tool configuration
├── tasks.py                      the task runner — works the same on Windows and Linux
└── uv.lock                       pinned dependency versions
```

The website is its own Quarto project, rooted at `site/`. Two things follow.
The repository root stays a short list of entry points and one folder per
purpose, and the governance files — `docs/`, `AGENTS.md`, `CONTRIBUTING.md` —
are out of the website's reach **by construction**, so they cannot be published
by accident. An earlier layout kept the Quarto project at the repository root
and depended on an explicit `render:` list to keep those pages off the site;
that was a guarantee held up by a config list, and this is a guarantee held up
by the filesystem. The publish workflow only needs to be told where the project
root now is: `path: site` in the publish action.

## How data moves

```
    Kaggle / Hugging Face mirror
              │
              │  scripts/download_data.py
              │  · revision pinned, so the bytes never change under you
              │  · validated by exact byte size and minimum row count
              ▼
        data/raw/*.csv                                    9 files, ~126 MB
              │
              │  scripts/load_raw.py
              │  · every column loaded as TEXT
              │  · chunked, so 126 MB does not need 126 MB of RAM
              ▼
    PostgreSQL   schema: raw                              9 tables, all TEXT
              │
              │  dbt
              ▼
  analytics_staging   stg_*        views  — cast, rename, normalise
              │
              ▼
  analytics_marts     dim_*, fct_*, mart_*   tables — what the report queries
              │
              ▼
      Quarto reports → GitHub Pages
```

## Why it is separated this way

**Raw is kept raw.** Every column in `raw` is TEXT. Casting, renaming and
normalising happen in the staging layer, in one visible place, covered by tests.
It also stops the silent corruption that happens when a zip-code prefix like
`01001` is inferred as the integer `1001` and every geographic join quietly
returns nothing. See [decision 0001](decisions/0001-raw-columns-stay-text.md).

**Docker runs the database and nothing else.** Python, dbt and Quarto run
natively. Containerising the whole stack would make the environment harder to
inspect and slower to iterate on, in exchange for reproducibility that
`uv.lock` already provides for dependencies and `docker-compose.yml` provides
for the database.

**The database is the only stateful thing.** It lives in a named volume, so
`db-down` stops it without losing the 126 MB load, and `db-reset` deletes it
when a genuinely clean start is needed.

**The task runner is Python, not `make`.** `make` is not present on a stock
Windows machine, and this repository is authored on Windows and run on Fedora.
`tasks.py` is pure standard library, so it works before any dependency is
installed, and it exists to serve `retail.io` rather than replace it — the
functions are the interface, the scripts are thin wrappers, and the runner is a
fourth way in that also knows about `.env` and `PYTHONPATH`.

**Tests do not need the network or a database.** Every function in `retail.io`
takes a `files=` override, so the download and validation logic is exercised
against synthetic fixtures. The suite runs in CI on a machine that has never
seen a CSV from Olist.

## Where the boundaries are enforced

| Boundary | Enforced by |
|---|---|
| No credentials or data in git | `.gitignore`, and `data/` is ignored except its README |
| Raw stays TEXT | The loader, plus the safe-cast macros being the only casts in staging |
| Keys are keys | `unique` + `not_null` on every primary key, `relationships` on foreign keys |
| Values are valid | `accepted_values` on statuses, payment types and scores |
| Business rules hold | Singular tests in `dbt_project/tests/` |
| No silent breakage | CI runs lint, tests and a full `dbt build` on every pull request |

The organising principle throughout: **make the wrong thing loud.** A test that
can only fail when something is genuinely broken is worth more than ten that
pass no matter what.
