#!/usr/bin/env python3
"""Download and validate the Olist dataset into `data/raw/`.

    uv run python tasks.py data
    uv run python projects/01-retail-analytics/scripts/download_data.py --force

The dataset is fetched from a revision-pinned, anonymous mirror (no Kaggle
credentials required) and then validated against expected file sizes and row
counts. See `data/README.md` for why it is done this way.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make `retail` importable when this file is run directly, before the package
# is installed. Project 02 replaces this bootstrap with real packaging.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retail.config import get_settings  # noqa: E402
from retail.io import (  # noqa: E402
    DatasetValidationError,
    DownloadError,
    download_dataset,
    validate_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="re-download files even if they look complete"
    )
    parser.add_argument(
        "--skip-download", action="store_true", help="only validate what is already on disk"
    )
    args = parser.parse_args()

    settings = get_settings()

    if not args.skip_download:
        try:
            download_dataset(settings, force=args.force)
        except DownloadError as error:
            print(f"\n[FAILED] {error}", file=sys.stderr)
            return 1
        print()

    try:
        validate_dataset(settings)
    except DatasetValidationError as error:
        print(f"\n[FAILED] {error}", file=sys.stderr)
        return 1

    print(f"\nDataset ready in {settings.data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
