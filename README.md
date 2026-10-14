# Retail Analytics Portfolio

[![CI](https://github.com/AndersonTavares0/ds-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/AndersonTavares0/ds-portfolio/actions/workflows/ci.yml)
[![Live report](https://img.shields.io/badge/live-report-1f6feb)](https://AndersonTavares0.github.io/ds-portfolio/)

Analytics on the Olist Brazilian e-commerce dataset: 99,441 orders placed between September 2016 and October 2018, across nine related tables. Three projects on one dataset, each shipping a written analysis, a one-page decision memo, and a statement of what the data cannot support.

The thread through all three is one finding: **late delivery is the strongest signal of customer dissatisfaction in this marketplace.** An order that arrives late averages 2.27 stars out of 5. One that arrives on time averages 4.29. Project 01 measures that. Project 02 predicts it from what is known at the moment of purchase. Project 03 reads the 99,000 Portuguese reviews customers wrote about the rest of the experience.

## Start here

- [The report](https://AndersonTavares0.github.io/ds-portfolio/reports/01-retail-analytics/01-business-analytics.html) is the full analysis, with figures.
- [The decision memo](https://AndersonTavares0.github.io/ds-portfolio/reports/01-retail-analytics/00-executive-memo.html) is the same argument on one page.
- [Em português](https://AndersonTavares0.github.io/ds-portfolio/pt/) has both pages translated.

## Projects

| # | Project | Question it answers | Status |
|---|---|---|---|
| 01 | Retail analytics | Which levers actually move satisfaction and repeat purchase? | Published |
| 02 | Late-delivery prediction | At purchase time, can we tell which orders will arrive late? | In progress |
| 03 | Voice of the customer | What do 99,000 Portuguese reviews complain about? | Planned |

## What Project 01 found

- **Revenue.** 99,441 orders worth R$ 16.0M, an average order of R$ 160.99. November 2017 is the largest month at R$ 1.19M, on Black Friday. 2016 holds 329 orders across three months, a launch period rather than a quiet year.
- **Repeat purchase is 3.12%.** 2,997 of 96,096 customers ever placed a second order, and 96.88% placed exactly one. Month-one cohort retention is 0.48%, flat near 0.2% afterwards. There is almost no repeat-purchase habit to lose, so the usual retention playbook does not apply. This is an acquisition business.
- **Late delivery is 6.77%.** 6,535 of 96,476 deliveries arrived after the promised date. Those orders average 2.27 stars against 4.29 for on-time orders, and past a week late about 80% of reviewers give one or two stars.
- **The promised date is conservative.** The average order arrives 11.18 days early and only 6.77% miss. Expectation management may matter as much as speed.

The report recommends investigating Rio de Janeiro, where 12.10% of 12,353 deliveries are late against São Paulo's 4.49%. At São Paulo's rate, roughly 940 Rio orders a year would not be late, and the observed review behaviour implies about 370 fewer one- and two-star reviews. It labels that an association rather than a forecast, because the data holds states and not distances, and no cost or margin figures.

## How it is built

Raw CSVs from a revision-pinned mirror, loaded into PostgreSQL with every column kept as text, modelled with dbt, tested at every layer, and written up in Quarto.

```
Hugging Face mirror, revision pinned
  -> download_data.py       9 CSVs, ~126 MB, verified by exact byte size
  -> load_raw.py            every column TEXT, chunked
  -> PostgreSQL             schema: raw
  -> dbt staging            analytics_staging, views: cast and rename
  -> dbt marts              analytics_marts, tables: 80 data tests
  -> make_charts.py         figures, committed so publishing needs no database
  -> Quarto                 site/
```

Three decisions are worth knowing before reading the code. Each one is recorded with its evidence in [`docs/decisions/`](docs/decisions/).

- **Raw columns stay text.** Letting pandas infer types turns a zip-code prefix of `01001` into the integer `1001`, quietly. Every cast goes through three macros that treat an empty string as NULL, because empty CSV cells arrive as empty strings and `cast('' as timestamp)` raises.
- **Aggregate to the order before joining.** Order items, payments and reviews are each finer-grained than an order. Joining them directly multiplies rows, so an order with four items and three payments would count twelve times in every total. The SQL would compile and nothing would fail.
- **Lateness is measured in whole days.** The promised date carries no time of day: all 99,441 of them are midnight. The actual delivery time does, across 96,476 distinct values. Comparing the two to the second misclassified 1,292 orders.

## Reproducing it

You need [uv](https://docs.astral.sh/uv/), Docker and [Quarto](https://quarto.org/) on the PATH. Python and dbt come from `uv`.

```bash
git clone https://github.com/AndersonTavares0/ds-portfolio.git
cd ds-portfolio
cp .env.example .env
uv run python tasks.py doctor      # check the toolchain
uv run python tasks.py setup       # dependencies, database, dataset
uv run python tasks.py pipeline    # load, build, charts, tests, render
```

The website is then in `site/_site/`. Every command goes through [`tasks.py`](tasks.py), which is plain Python rather than a `Makefile` because `make` is not on Windows and this repository is written on Windows and run on Linux.

The dataset is 126 MB and is not committed. It comes from a Hugging Face mirror of the original Kaggle release, pinned to one revision so the numbers cannot move underneath you, and validated by exact byte size plus a minimum row count. CI needs neither the dataset nor a database: it runs ruff and the Python tests, and the site is published from committed figures.

## Repository map

```
projects/01-retail-analytics/   the analysis
  dbt_project/                  staging models, mart models, 80 data tests, 7 singular tests
  src/retail/                   the data layer: config, dataset manifest, download and load
  scripts/                      download_data.py, load_raw.py, make_charts.py
  tests/                        Python tests, no network and no database
site/                           what gets published, as its own Quarto project
  index.qmd, about.qmd          the landing pages
  reports/01-retail-analytics/  the report and the decision memo
  pt/                           the same pages in Portuguese
  theme/                        a light and a dark palette over one set of rules
docs/                           how and why
  metrics.md                    the definition of every number in the report
  decisions/                    why the obvious approach was wrong, six times
  data-dictionary.md            every column, in every layer
  architecture.md               the map, and where the boundaries are enforced
data/                           the input, downloaded and never committed
tasks.py                        every command
AGENTS.md                       the rules this repository works to
```

One folder is one purpose. `site/` is what gets published, `projects/` is the analysis that produces it, `docs/` is how and why, and `data/` is the input.

## What this repository demonstrates

| Skill | Where to look |
|---|---|
| SQL and dimensional modelling | `projects/01-retail-analytics/dbt_project/models/` |
| Data quality as code | `projects/01-retail-analytics/dbt_project/models/**/schema.yml`, `.../dbt_project/tests/` |
| Python data engineering | `projects/01-retail-analytics/src/retail/` |
| Reproducible pipelines | `tasks.py`, `.github/workflows/` |
| Testing without a database | `projects/01-retail-analytics/tests/` |
| Communicating a result | `site/reports/01-retail-analytics/` |

## Documentation

| | |
|---|---|
| [Architecture](docs/architecture.md) | the map, and why it is separated this way |
| [Metrics](docs/metrics.md) | what every number in the report means |
| [Data dictionary](docs/data-dictionary.md) | every column, in every layer |
| [Decisions](docs/decisions/) | six decisions, and the evidence that forced each |
| [Contributing](docs/CONTRIBUTING.md) | the workflow this repository follows |

The decision log is the one to read first. It records what was measured, what the obvious approach was, and why the obvious approach was wrong.

## Licence

Code is MIT. The Olist dataset is not: it is CC BY-NC-SA 4.0, non-commercial, and is not redistributed here. See [acknowledgements](docs/acknowledgements.md).

## Contact

- GitHub: [AndersonTavares0](https://github.com/AndersonTavares0)
- LinkedIn: [andersonlimatavares](https://www.linkedin.com/in/andersonlimatavares)
- Email: anderson.g.tavares@gmail.com
