"""Tests for validation and row counting.

The interesting case here is `test_count_rows_handles_quoted_newlines`: the real
Olist review file contains free-text comments that span several physical lines
inside a quoted CSV field. Naive line counting overcounts those rows, which
would make the validator reject a perfectly good download. That behaviour is
pinned by a test so it cannot regress.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from retail.config import Settings
from retail.datasets import OlistFile
from retail.io import (
    DatasetValidationError,
    count_rows,
    inspect_file,
    validate_dataset,
)


def write_csv(path: Path, rows: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "value"])
        for index in range(rows):
            writer.writerow([index, f"value-{index}"])


def spec_for(path: Path, *, min_rows: int = 1) -> OlistFile:
    return OlistFile(
        filename=path.name,
        table=path.stem,
        size_bytes=path.stat().st_size,
        min_rows=min_rows,
        description="test fixture",
    )


def settings_for(data_dir: Path) -> Settings:
    return Settings(data_dir=data_dir)


# ---------------------------------------------------------------------------
# count_rows
# ---------------------------------------------------------------------------
def test_count_rows_counts_data_rows_only(tmp_path: Path) -> None:
    path = tmp_path / "simple.csv"
    write_csv(path, 5)
    assert count_rows(path) == 5


def test_count_rows_handles_quoted_newlines(tmp_path: Path) -> None:
    path = tmp_path / "reviews.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "comment"])
        writer.writerow([1, "first line\nsecond line"])  # one row, two lines
        writer.writerow([2, "plain"])

    assert count_rows(path) == 2

    # The naive approach that this function exists to avoid:
    naive = sum(1 for _ in path.open(encoding="utf-8")) - 1
    assert naive == 3
    assert naive != count_rows(path)


def test_count_rows_reads_a_file_with_no_data_rows(tmp_path: Path) -> None:
    path = tmp_path / "header_only.csv"
    write_csv(path, 0)
    assert count_rows(path) == 0


# ---------------------------------------------------------------------------
# inspect_file
# ---------------------------------------------------------------------------
def test_inspect_file_reports_a_missing_file(tmp_path: Path) -> None:
    spec = OlistFile("nope.csv", "nope", 10, 1, "missing")
    status = inspect_file(spec, tmp_path)
    assert not status.present
    assert not status.ok
    assert status.actual_size is None


def test_inspect_file_accepts_a_matching_file(tmp_path: Path) -> None:
    path = tmp_path / "ok.csv"
    write_csv(path, 3)
    status = inspect_file(spec_for(path, min_rows=3), tmp_path)
    assert status.ok
    assert status.rows == 3


# ---------------------------------------------------------------------------
# validate_dataset
# ---------------------------------------------------------------------------
def test_validate_passes_on_a_complete_dataset(tmp_path: Path) -> None:
    specs = []
    for name in ("orders.csv", "customers.csv"):
        path = tmp_path / name
        write_csv(path, 4)
        specs.append(spec_for(path, min_rows=4))

    statuses = validate_dataset(settings_for(tmp_path), files=specs)
    assert len(statuses) == 2
    assert all(status.ok for status in statuses)


def test_validate_raises_when_a_file_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "present.csv"
    write_csv(path, 2)
    present = spec_for(path, min_rows=1)
    absent = OlistFile("absent.csv", "absent", 1_000, 1, "gone")

    with pytest.raises(DatasetValidationError, match="absent.csv"):
        validate_dataset(settings_for(tmp_path), files=[present, absent])


def test_validate_raises_on_a_truncated_file(tmp_path: Path) -> None:
    path = tmp_path / "truncated.csv"
    write_csv(path, 2)
    # Claim a size the file cannot have -> a half-finished download.
    spec = OlistFile(path.name, "truncated", path.stat().st_size + 5_000, 1, "truncated")

    with pytest.raises(DatasetValidationError):
        validate_dataset(settings_for(tmp_path), files=[spec])


def test_validate_raises_when_there_are_too_few_rows(tmp_path: Path) -> None:
    path = tmp_path / "short.csv"
    write_csv(path, 3)
    spec = spec_for(path, min_rows=100)  # size is fine, row count is not

    with pytest.raises(DatasetValidationError):
        validate_dataset(settings_for(tmp_path), files=[spec])


def test_validate_can_report_without_raising(tmp_path: Path) -> None:
    absent = OlistFile("absent.csv", "absent", 1_000, 1, "gone")
    statuses = validate_dataset(settings_for(tmp_path), files=[absent], strict=False)
    assert [status.ok for status in statuses] == [False]
