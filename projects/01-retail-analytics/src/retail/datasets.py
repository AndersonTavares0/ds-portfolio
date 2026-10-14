"""The dataset manifest: one source of truth for what the raw layer contains.

Every other module (download, validation, loading, tests) reads from here, so
there is exactly one place to change if the dataset ever changes.

The `size_bytes` values were read from the pinned revision's manifest via the
Hugging Face API. They are used as a cheap integrity check: a truncated or
half-finished download has the wrong size and is caught immediately, without
hashing 126 MB.
"""

from __future__ import annotations

from dataclasses import dataclass

# Original publication (has the authoritative license; requires a Kaggle login).
ORIGIN_URL = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"

# Anonymous, revision-pinned mirror used by this repository.
DATASET_REPO = "bulutttt/olist-raw-data"
RESOLVE_TEMPLATE = "https://huggingface.co/datasets/{repo}/resolve/{revision}/{filename}"

SCHEMA_URL = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/README.md"


@dataclass(frozen=True)
class OlistFile:
    """One CSV in the published dataset, and where it lands in PostgreSQL."""

    filename: str
    table: str
    size_bytes: int
    min_rows: int
    description: str


# `min_rows` is a conservative lower bound (roughly 95-99% of the published
# counts). It exists to catch truncated files, not to hard-code the dataset.
OLIST_FILES: tuple[OlistFile, ...] = (
    OlistFile(
        "olist_customers_dataset.csv",
        "customers",
        9_033_957,
        99_000,
        "Customer id and location per order.",
    ),
    OlistFile(
        "olist_geolocation_dataset.csv",
        "geolocation",
        61_273_883,
        1_000_000,
        "Zip-code-prefix to lat/lng (the one genuinely large table).",
    ),
    OlistFile(
        "olist_order_items_dataset.csv",
        "order_items",
        15_438_671,
        112_000,
        "One row per item within an order.",
    ),
    OlistFile(
        "olist_order_payments_dataset.csv",
        "order_payments",
        5_777_138,
        103_000,
        "One row per payment method used on an order.",
    ),
    OlistFile(
        "olist_order_reviews_dataset.csv",
        "order_reviews",
        14_451_670,
        99_000,
        "Review score and free-text comment (Portuguese).",
    ),
    OlistFile(
        "olist_orders_dataset.csv",
        "orders",
        17_654_914,
        99_000,
        "Order lifecycle timestamps and status — the spine of the model.",
    ),
    OlistFile(
        "olist_products_dataset.csv",
        "products",
        2_379_446,
        32_000,
        "Product attributes, including physical dimensions.",
    ),
    OlistFile(
        "olist_sellers_dataset.csv",
        "sellers",
        174_703,
        3_000,
        "Seller id and location.",
    ),
    OlistFile(
        "product_category_name_translation.csv",
        "product_category_name_translation",
        2_613,
        70,
        "Portuguese to English product category names.",
    ),
)

TOTAL_BYTES = sum(item.size_bytes for item in OLIST_FILES)


def resolve_url(filename: str, revision: str) -> str:
    """Build the download URL for one file at a pinned revision."""
    return RESOLVE_TEMPLATE.format(repo=DATASET_REPO, revision=revision, filename=filename)


def by_table(table: str) -> OlistFile:
    for item in OLIST_FILES:
        if item.table == table:
            return item
    raise KeyError(f"unknown table: {table!r}")
