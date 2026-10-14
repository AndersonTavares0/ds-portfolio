# Acknowledgements

## Data

This project uses the **Brazilian E-Commerce Public Dataset by Olist**, published
by [Olist](https://olist.com/) on Kaggle:

- Original source: <https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>
- Mirror used by this repository (anonymous, revision-pinned):
  <https://huggingface.co/datasets/bulutttt/olist-raw-data>
- Pinned revision: `5acf1f37d7197d4979e714721a1ec13a7c3da728`

The dataset contains ~100,000 orders placed on the Olist Store marketplace in
Brazil between 2016 and 2018, split across nine related tables.

### License of the data

The dataset is **not** covered by this repository's MIT license. It is published
for **non-commercial and academic use** (the Kaggle listing states
**CC BY-NC-SA 4.0** — verify and comply with the terms currently published on the
Kaggle page before reusing it).

In practice, this means:

- Always credit Olist (done here).
- Do **not** present derived work as commercial or production-ready.
- Do **not** redistribute the dataset inside this repository — the download
  script fetches it from its original home instead.

## Tooling

- [dbt](https://www.getdbt.com/) — data transformation and testing
- [Quarto](https://quarto.org/) — report publishing
- [uv](https://docs.astral.sh/uv/) — Python environment management
