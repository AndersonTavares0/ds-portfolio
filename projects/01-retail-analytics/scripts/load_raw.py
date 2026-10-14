#!/usr/bin/env python3
"""Load the raw Olist CSVs into the PostgreSQL `raw` schema.

    uv run python tasks.py load
    uv run python projects/01-retail-analytics/scripts/load_raw.py --source tests/fixtures/sample

Every column is loaded as TEXT; casting happens in the dbt `staging` layer.
The `--source` flag exists so CI can load a small committed fixture instead of
the full 126 MB dataset.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retail.config import get_settings  # noqa: E402
from retail.io import build_engine, load_raw_schema, verify_row_counts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="directory containing the CSV files (default: data/raw)",
    )
    parser.add_argument("--schema", default="raw", help="target PostgreSQL schema (default: raw)")
    parser.add_argument("--chunk-size", type=int, default=5_000, help="rows per insert batch")
    args = parser.parse_args()

    settings = get_settings()
    try:
        loaded = load_raw_schema(
            settings,
            source_dir=args.source,
            schema=args.schema,
            chunk_size=args.chunk_size,
        )
    except FileNotFoundError as error:
        print(f"\n[FAILED] {error}", file=sys.stderr)
        return 1

    engine = build_engine(settings)
    actual = verify_row_counts(engine, loaded, schema=args.schema)

    print(f"\nLoaded {len(loaded)} table(s) into schema '{args.schema}':")
    mismatched = 0
    for table, expected in loaded.items():
        got = actual.get(table)
        flag = "ok" if got == expected else f"MISMATCH (db says {got})"
        if got != expected:
            mismatched += 1
        print(f"  {schema_dot(args.schema)}{table:<38}{expected:>10,} rows   {flag}")

    return 1 if mismatched else 0


def schema_dot(schema: str) -> str:
    return f"{schema}."


if __name__ == "__main__":
    raise SystemExit(main())
