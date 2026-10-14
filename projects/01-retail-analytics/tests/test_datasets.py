"""Tests for the dataset manifest.

These are pure unit tests: no network, no database, no downloaded data. They
guard the one place where the dataset contract is declared, so a typo in a file
name or a silently reordered manifest fails CI instead of failing later.
"""

from __future__ import annotations

import pytest
from retail.datasets import OLIST_FILES, TOTAL_BYTES, by_table, resolve_url


def test_manifest_has_the_nine_published_files() -> None:
    assert len(OLIST_FILES) == 9


def test_filenames_are_unique() -> None:
    filenames = [spec.filename for spec in OLIST_FILES]
    assert len(filenames) == len(set(filenames))


def test_table_names_are_unique() -> None:
    tables = [spec.table for spec in OLIST_FILES]
    assert len(tables) == len(set(tables))


def test_every_entry_is_complete() -> None:
    for spec in OLIST_FILES:
        assert spec.filename.endswith(".csv"), spec.filename
        assert spec.size_bytes > 0, spec.filename
        assert spec.min_rows > 0, spec.filename
        assert spec.description, spec.filename


def test_total_bytes_matches_the_sum_of_entries() -> None:
    assert sum(spec.size_bytes for spec in OLIST_FILES) == TOTAL_BYTES


def test_resolve_url_pins_the_requested_revision() -> None:
    url = resolve_url("olist_orders_dataset.csv", "deadbeef")
    assert url.startswith("https://huggingface.co/")
    assert "/resolve/deadbeef/" in url
    assert url.endswith("olist_orders_dataset.csv")


def test_by_table_finds_the_orders_table() -> None:
    assert by_table("orders").filename == "olist_orders_dataset.csv"


def test_by_table_rejects_an_unknown_table() -> None:
    with pytest.raises(KeyError):
        by_table("not_a_real_table")
