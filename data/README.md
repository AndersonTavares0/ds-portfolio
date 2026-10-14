# `data/` — not versioned

The dataset is **~126 MB** and is deliberately **not committed** to this
repository. `data/*` is git-ignored; only this file and `.gitkeep` are tracked.

## How the data gets here

```bash
uv run python tasks.py data      # download + validate into data/raw/
```

`projects/01-retail-analytics/scripts/download_data.py` downloads the nine Olist
CSVs from a **revision-pinned** mirror on the Hugging Face Hub and then validates
them.

Why this way:

- **No credentials.** Unlike the Kaggle API, the mirror needs no `kaggle.json`.
  Nobody cloning this repository has to own a Kaggle account to reproduce it.
- **Immutable provenance.** The revision is pinned in `.env`
  (`OLIST_REVISION`). If the upstream dataset is updated, your numbers do not
  silently change.
- **Cheap validation.** Each file is checked against its expected **byte size**
  (taken from the mirror's own manifest) plus a **minimum row count**. That
  catches truncated and half-finished downloads without downloading anything
  twice.

## Layout

```
data/
├── raw/            # the nine CSVs, exactly as published (all columns as text)
└── README.md       # this file
```

## Licensing

The data is © Olist and is published for **non-commercial / academic use**. It is
**not** covered by this repository's MIT license. See `../docs/acknowledgements.md`
before reusing it, and check the license currently stated on the
[Kaggle listing](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
