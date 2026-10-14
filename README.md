# Retail Analytics Portfolio — Olist Brazilian E-Commerce

[![CI](https://github.com/AndersonTavares0/ds-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/AndersonTavares0/ds-portfolio/actions/workflows/ci.yml)
[![Live report](https://img.shields.io/badge/report-live-1f6feb)](https://AndersonTavares0.github.io/ds-portfolio/)

An end-to-end data science portfolio built on the **[Olist Brazilian E-Commerce
dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)** — ~100,000
orders placed on a real Brazilian marketplace between 2016 and 2018, spread across
nine related tables.

Everything here reproduces from a clean clone. Every project ships a narrative
report, a one-page decision memo, and a "Limitations" section that says what the
data cannot support.

---

## The narrative

> In this marketplace, **delivery performance drives customer satisfaction and
> retention**. I *measured* it, I *predicted* it, and I *explained the voice of
> the customer*.

Three projects, one argument — not three disconnected notebooks.

---

## Projects

| # | Project | The question | Stack | Status |
|---|---------|--------------|-------|--------|
| **01** | [**Retail Analytics**](./projects/01-retail-analytics) | Which levers actually move customer satisfaction and repeat purchase? | PostgreSQL · dbt · SQL · Python · Quarto | ✅ published |
| 02 | Late-Delivery Prediction | At purchase time, can we tell which orders will arrive late? | scikit-learn · pandas | 🚧 in progress |
| 03 | Voice of the Customer | What do 99k Portuguese reviews actually complain about? | NLP · topic modelling | 🚧 planned |

### Project 01 at a glance

- **Data layer:** nine raw CSVs loaded verbatim into PostgreSQL, then modelled with
  dbt into a tested star schema (`staging` → `marts`).
- **Analysis:** RFM segmentation, monthly cohort retention, delivery-performance
  decomposition, payment behaviour.
- **Deliverables:** a long-form report, a one-page decision memo, and data tests
  that fail the build when the data stops making sense.

---

## What this repository demonstrates

| Skill | Where to look |
|---|---|
| **SQL / analytical modelling** | `projects/01-retail-analytics/dbt_project/models/` |
| **Data quality as code** | `.../dbt_project/models/**/schema.yml`, `.../dbt_project/tests/` |
| **Python engineering** | `projects/01-retail-analytics/src/retail/`, `tasks.py` |
| **Automated testing** | `projects/01-retail-analytics/tests/`, `pytest` |
| **CI/CD** | `.github/workflows/` |
| **Reproducibility** | pinned dataset revision, `uv.lock`, `tasks.py pipeline` |
| **Communication** | `site/reports/01-retail-analytics/` (report + decision memo) |

---

## Documentation

The reasoning lives in [`docs/`](./docs/) rather than buried in code comments:

| | |
|---|---|
| [Architecture](./docs/architecture.md) | How the pieces fit, and why they are separated this way |
| [Metrics](./docs/metrics.md) | What every number means — and, more usefully, what it does not mean |
| [Data dictionary](./docs/data-dictionary.md) | Every table and column, with its grain and its caveats |
| [Decisions](./docs/decisions/README.md) | Why the code looks the way it does, including the times the data changed the design |
| [Contributing](./docs/CONTRIBUTING.md) | The workflow - every change arrives by pull request |

The decision log is the one worth reading first. It records what was measured, what
the obvious approach was, and why the obvious approach was wrong. The clearest
example: lateness was being measured to the second against a deadline that only
ever had a date, which misclassified 1,292 orders — and `dbt run` would have
shipped it silently.

---

## Reproducing it

**Prerequisites:** [uv](https://docs.astral.sh/uv/getting-started/installation/),
[Docker](https://docs.docker.com/get-docker/), and
[Quarto](https://quarto.org/docs/get-started/) on your `PATH`.

```bash
git clone https://github.com/AndersonTavares0/ds-portfolio.git
cd ds-portfolio
cp .env.example .env                  # defaults work out of the box

uv run python tasks.py doctor         # confirm the required tools are present
uv run python tasks.py setup          # deps + database + dataset download
uv run python tasks.py pipeline       # load -> dbt build -> tests -> render
```

The website is then in `_site/`; open `_site/index.html`.

Run `uv run python tasks.py` with no arguments to list every task.

> The dataset is **never committed**. It is downloaded from a revision-pinned,
> anonymous mirror and validated against expected file sizes. See
> `data/README.md`.

---

## Repository layout

```
ds-portfolio/
├── tasks.py                  # portable task runner (works without `make`)
├── docker-compose.yml        # the PostgreSQL service — the only container
├── pyproject.toml            # deps + ruff/pytest configuration
├── site/                     # the published website — its own Quarto project
│   ├── _quarto.yml           # site configuration
│   ├── index.qmd / about.qmd # site pages
│   └── reports/              # narrative report + decision memo
├── projects/
│   └── 01-retail-analytics/
│       ├── dbt_project/      # staging -> marts, with tests
│       ├── scripts/          # download_data.py, load_raw.py, make_charts.py
│       ├── src/retail/       # reusable Python
│       └── tests/            # pytest
├── docs/                     # architecture, metrics, dictionary, decisions
├── data/                     # git-ignored dataset
├── .github/                  # workflows + issue and pull-request templates
└── AGENTS.md                 # the rules this repository is worked to
```

Each top-level folder is one purpose: `site/` is what gets published,
`projects/` is the analysis that produces it, `docs/` is how and why,
`data/` is the input, and `.github`/`.agents` are configuration.

---

## License

Code: [MIT](./LICENSE).
Data: © Olist, used under its own (non-commercial) license — see
[docs/acknowledgements.md](./docs/acknowledgements.md).

## Contact

- GitHub: [AndersonTavares0](https://github.com/AndersonTavares0)
- LinkedIn: [andersonlimatavares](https://www.linkedin.com/in/andersonlimatavares)
- Email: `anderson.g.tavares@gmail.com`
