"""Download, validate and load the raw Olist dataset.

The flow this module implements:

    download_dataset()  ->  data/raw/*.csv         (anonimo, revision-pinned)
    validate_dataset()  ->  bytes + row counts     (cheap integrity check)
    load_raw_schema()   ->  PostgreSQL `raw` schema (every column as TEXT)

Every raw column is loaded as TEXT on purpose. Type casting belongs in the dbt
`staging` layer, where it is visible, tested and reviewable. Loading as TEXT
also avoids the classic silent corruption where a zip-code prefix like `01001`
becomes the integer `1001`.
"""

from __future__ import annotations

import csv
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from sqlalchemy import Text, create_engine, text
from sqlalchemy.engine import Engine

from retail.config import Settings, get_settings
from retail.datasets import OLIST_FILES, OlistFile, resolve_url

DEFAULT_SCHEMA = "raw"
DOWNLOAD_TIMEOUT = 120  # seconds, per request


def _use_os_certificate_store() -> bool:
    """Make Python trust the operating system's certificate store.

    `requests` verifies TLS against the `certifi` bundle, which only contains
    public roots. Behind a TLS-inspecting proxy or antivirus, that bundle does
    not know the intercepting root certificate and every download fails with
    `CERTIFICATE_VERIFY_FAILED`. `truststore` hands verification to the OS
    store, which *does* know it — and on Fedora that is the correct default
    anyway.

    Returns True when the OS store is in use.
    """
    try:
        import truststore
    except ImportError:  # pragma: no cover - dependency is declared
        return False

    # truststore renamed this in 0.10: `inject_ssl_context` -> `inject_into_ssl`.
    # Accept both so a lock-file refresh cannot silently break the downloader.
    for function_name in ("inject_into_ssl", "inject_ssl_context"):
        function = getattr(truststore, function_name, None)
        if function is not None:
            function()
            return True
    return False  # pragma: no cover - only if the API changes again


USING_OS_CERTIFICATE_STORE = _use_os_certificate_store()


class DatasetValidationError(RuntimeError):
    """Raised when downloaded files do not match the manifest."""


class DownloadError(RuntimeError):
    """Raised when a file cannot be downloaded."""


@dataclass(frozen=True)
class FileStatus:
    """The result of checking one file against its manifest entry."""

    spec: OlistFile
    path: Path
    present: bool
    actual_size: int | None
    rows: int | None

    @property
    def size_ok(self) -> bool:
        return self.actual_size == self.spec.size_bytes

    @property
    def rows_ok(self) -> bool:
        return self.rows is not None and self.rows >= self.spec.min_rows

    @property
    def ok(self) -> bool:
        return self.present and self.size_ok and self.rows_ok


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def human_bytes(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:,.0f} {unit}" if unit == "B" else f"{size:,.1f} {unit}"
        size /= 1024
    return f"{size:,.1f} TB"


def _spec_list(files: Sequence[OlistFile] | None) -> tuple[OlistFile, ...]:
    return tuple(files) if files else OLIST_FILES


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def download_file(
    spec: OlistFile,
    dest_dir: Path,
    revision: str,
    *,
    force: bool = False,
    timeout: int = DOWNLOAD_TIMEOUT,
) -> Path:
    """Download one CSV, unless a byte-exact copy is already present."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    destination = dest_dir / spec.filename

    if not force and destination.exists() and destination.stat().st_size == spec.size_bytes:
        print(f"  skip  {spec.filename:<42} already complete")
        return destination

    url = resolve_url(spec.filename, revision)
    print(f"  get   {spec.filename:<42} {human_bytes(spec.size_bytes)}")

    partial = destination.with_name(destination.name + ".part")
    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            with partial.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    handle.write(chunk)
    except requests.exceptions.SSLError as error:
        partial.unlink(missing_ok=True)
        raise DownloadError(_tls_help(spec.filename, error)) from error
    except requests.exceptions.RequestException as error:
        partial.unlink(missing_ok=True)
        raise DownloadError(f"could not download {spec.filename} from {url}: {error}") from error

    partial.replace(destination)
    return destination


def _tls_help(filename: str, error: Exception) -> str:
    return (
        f"TLS certificate verification failed while downloading {filename}.\n"
        "\n"
        "This is an environment problem, not a data problem. It means something\n"
        "between this machine and the internet (a corporate proxy, or antivirus\n"
        "such as Kaspersky/ESET/Zscaler) is decrypting HTTPS with its own root\n"
        "certificate, and Python does not trust that root.\n"
        "\n"
        "This downloader already tries the operating system certificate store\n"
        f"via `truststore` (in use: {USING_OS_CERTIFICATE_STORE}). If it still\n"
        "fails, the intercepting root is not installed where Python looks. Pick one:\n"
        "\n"
        "  1. Point Python at the root certificate explicitly\n"
        '       Windows:  setx REQUESTS_CA_BUNDLE "C:\\path\\to\\ca-bundle.crt"\n'
        "       Fedora:   export REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt\n"
        "  2. Install the intercepting root into the system store, then re-run.\n"
        "  3. Temporarily disable TLS inspection for huggingface.co.\n"
        "\n"
        f"Underlying error: {error}"
    )


def download_dataset(
    settings: Settings | None = None,
    *,
    files: Sequence[OlistFile] | None = None,
    force: bool = False,
) -> list[Path]:
    """Download every file in the manifest into `settings.data_dir`."""
    settings = settings or get_settings()
    specs = _spec_list(files)
    print(f"Dataset revision: {settings.olist_revision}")
    print(f"Destination:      {settings.data_dir}")
    return [
        download_file(spec, settings.data_dir, settings.olist_revision, force=force)
        for spec in specs
    ]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def count_rows(path: Path, *, encoding: str = "utf-8") -> int:
    """Count data rows, correctly handling newlines inside quoted fields.

    Naive line counting *overcounts* this dataset: some free-text review
    comments span several physical lines inside a quoted CSV field, so
    `sum(1 for _ in open(path))` reports more rows than exist. `csv.reader`
    understands quoting, and this stays streaming and memory-safe.
    """
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)  # discard the header
        return sum(1 for _ in reader)


def inspect_file(spec: OlistFile, data_dir: Path) -> FileStatus:
    path = data_dir / spec.filename
    if not path.exists():
        return FileStatus(spec, path, present=False, actual_size=None, rows=None)

    size = path.stat().st_size
    rows = None
    if size == spec.size_bytes:
        # Only count rows when the size already matches; otherwise the file is
        # known-bad and reading it wastes time.
        rows = count_rows(path)
    return FileStatus(spec, path, present=True, actual_size=size, rows=rows)


def format_report(statuses: Sequence[FileStatus]) -> str:
    lines = [
        f"{'file':<44}{'size':>12}{'rows':>12}   status",
        "-" * 82,
    ]
    for status in statuses:
        size = human_bytes(status.actual_size) if status.actual_size is not None else "-"
        rows = f"{status.rows:,}" if status.rows is not None else "-"
        if status.ok:
            verdict = "ok"
        elif not status.present:
            verdict = "MISSING"
        elif not status.size_ok:
            verdict = f"WRONG SIZE (expected {human_bytes(status.spec.size_bytes)})"
        else:
            verdict = f"TOO FEW ROWS (expected >= {status.spec.min_rows:,})"
        lines.append(f"{status.spec.filename:<44}{size:>12}{rows:>12}   {verdict}")
    return "\n".join(lines)


def validate_dataset(
    settings: Settings | None = None,
    *,
    files: Sequence[OlistFile] | None = None,
    strict: bool = True,
) -> list[FileStatus]:
    """Check presence, exact byte size and minimum row count for every file."""
    settings = settings or get_settings()
    statuses = [inspect_file(spec, settings.data_dir) for spec in _spec_list(files)]
    print(format_report(statuses))

    failures = [status for status in statuses if not status.ok]
    if failures and strict:
        names = ", ".join(status.spec.filename for status in failures)
        raise DatasetValidationError(
            f"{len(failures)} file(s) failed validation: {names}\n"
            f"Re-run with --force to download again: "
            f"python tasks.py data  (or scripts/download_data.py --force)"
        )
    return statuses


# ---------------------------------------------------------------------------
# Loading into PostgreSQL
# ---------------------------------------------------------------------------
def build_engine(settings: Settings | None = None) -> Engine:
    settings = settings or get_settings()
    return create_engine(settings.database_url, future=True)


def load_raw_schema(
    settings: Settings | None = None,
    *,
    files: Sequence[OlistFile] | None = None,
    source_dir: Path | None = None,
    schema: str = DEFAULT_SCHEMA,
    chunk_size: int = 5_000,
) -> dict[str, int]:
    """Load every CSV into `schema` verbatim, with all columns as TEXT.

    Returns a mapping of `table -> row count`.
    """
    settings = settings or get_settings()
    specs = _spec_list(files)
    source = Path(source_dir) if source_dir else settings.data_dir

    missing = [spec.filename for spec in specs if not (source / spec.filename).exists()]
    if missing:
        raise FileNotFoundError(
            f"missing raw file(s) in {source}: {', '.join(missing)}\n"
            "Run `uv run python tasks.py data` first."
        )

    engine = build_engine(settings)
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

    loaded: dict[str, int] = {}
    for spec in specs:
        frame = pd.read_csv(
            source / spec.filename,
            dtype=str,  # preserve leading zeros and raw formatting
            keep_default_na=False,  # empty cells stay empty strings, not NaN
        )
        print(f"  load  {spec.filename:<42} -> {schema}.{spec.table} ({len(frame):,} rows)")
        frame.to_sql(
            spec.table,
            engine,
            schema=schema,
            if_exists="replace",
            index=False,
            chunksize=chunk_size,
            method="multi",
            dtype={column: Text() for column in frame.columns},
        )
        loaded[spec.table] = len(frame)

    return loaded


def verify_row_counts(
    engine: Engine, expected: dict[str, int], schema: str = DEFAULT_SCHEMA
) -> dict[str, int]:
    """Read back the row count of each loaded table (used as a post-load check)."""
    counts: dict[str, int] = {}
    with engine.connect() as connection:
        for table in expected:
            result = connection.execute(text(f'SELECT count(*) FROM "{schema}"."{table}"'))
            counts[table] = int(result.scalar_one())
    return counts


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI convenience
    """`python -m retail.io` — download then validate."""
    argv = list(sys.argv[1:] if argv is None else argv)
    download_dataset(force="--force" in argv)
    print()
    validate_dataset()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
