#!/usr/bin/env python3
"""Portable task runner for the ds-portfolio monorepo.

WHY THIS EXISTS INSTEAD OF A Makefile
-------------------------------------
`make` is not installed on Windows and this project is written on Windows while
being developed on Fedora. Python is already a hard dependency, so a Python
task runner is the one thing that behaves identically on both. It uses only the
standard library, so it runs *before* any dependency is installed.

USAGE
-----
    uv run python tasks.py <task>
    python tasks.py                 # list every task

EXAMPLES
--------
    uv run python tasks.py setup      # deps + database + data   (run once)
    uv run python tasks.py pipeline   # load -> dbt build -> tests -> render
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "projects" / "01-retail-analytics"
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"
DBT_DIR = PROJECT / "dbt_project"

# The website is its own Quarto project with its own root, so it can be rendered
# and published without the rest of the repository in reach. Every Quarto
# command therefore runs with `cwd=SITE`.
SITE = ROOT / "site"
# The Portuguese pages are a second render of the same project into their own
# directory (see `site/_quarto-pt.yml`); `render` copies the result into
# `_site/pt`, which is where those sources live, so URLs are unchanged.
BUILD_PT = SITE / ".build-pt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Minimal `.env` loader, so this script works with zero dependencies.

    Real values already present in the environment always win.
    """
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def child_env() -> dict[str, str]:
    """Environment for child processes: `.env` loaded, `retail` importable."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def run(cmd: list[str], *, check: bool = True, cwd: Path | None = None) -> int:
    printable = " ".join(str(part) for part in cmd)
    print(f"\n$ {printable}", flush=True)
    result = subprocess.run(cmd, cwd=cwd or ROOT, env=child_env())
    if check and result.returncode != 0:
        raise SystemExit(f"\n[FAILED] exit code {result.returncode}: {printable}")
    return result.returncode


def require(executable: str, install_hint: str) -> None:
    if shutil.which(executable) is None:
        raise SystemExit(f"[MISSING] `{executable}` not found on PATH.\n  -> {install_hint}")


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
def task_doctor() -> None:
    """Report which required tools are available."""
    tools = [
        ("python", [sys.executable, "--version"]),
        ("uv", ["uv", "--version"]),
        ("docker", ["docker", "--version"]),
        ("dbt", ["dbt", "--version"]),
        ("quarto", ["quarto", "--version"]),
    ]
    for name, cmd in tools:
        if shutil.which(cmd[0]) is None:
            print(f"[missing] {name}")
            continue
        result = subprocess.run(cmd, capture_output=True, text=True)
        text = (result.stdout or result.stderr).strip().splitlines()
        print(f"[ok]      {name:<7} {text[0] if text else ''}")


def task_setup() -> None:
    """First-time setup: install deps, start the database, download the data."""
    require("uv", "install uv: https://docs.astral.sh/uv/getting-started/installation/")
    run(["uv", "sync"])
    task_db_up()
    task_data()


def task_data() -> None:
    """Download and validate the Olist dataset into `data/raw/`."""
    run([sys.executable, str(SCRIPTS / "download_data.py")])


def task_db_up() -> None:
    """Start the PostgreSQL service and wait until it is healthy."""
    require("docker", "install Docker: https://docs.docker.com/get-docker/")
    run(["docker", "compose", "up", "-d", "--wait", "db"])


def task_db_down() -> None:
    """Stop the PostgreSQL service (data is preserved in the volume)."""
    run(["docker", "compose", "down"])


def task_db_reset() -> None:
    """Destroy the database volume and recreate an empty database."""
    run(["docker", "compose", "down", "-v"])
    task_db_up()


def task_load() -> None:
    """Load the raw CSVs into the `raw` schema of PostgreSQL."""
    run([sys.executable, str(SCRIPTS / "load_raw.py")])


def task_charts() -> None:
    """Regenerate the report charts from the marts.

    Needs a built database, which is why it is not part of `render`. The PNGs it
    writes are committed, so publishing the site never touches the database.
    """
    run([sys.executable, str(SCRIPTS / "make_charts.py")])


def task_dbt_build() -> None:
    """Build every dbt model and run every dbt test."""
    run(
        [
            "dbt",
            "build",
            "--project-dir",
            str(DBT_DIR),
            "--profiles-dir",
            str(DBT_DIR),
        ]
    )


def task_dbt_docs() -> None:
    """Generate the dbt documentation site."""
    run(
        [
            "dbt",
            "docs",
            "generate",
            "--project-dir",
            str(DBT_DIR),
            "--profiles-dir",
            str(DBT_DIR),
        ]
    )


def task_test() -> None:
    """Run the Python test suite."""
    run(["pytest"])


def task_lint() -> None:
    """Check formatting and lint rules without changing files."""
    run(["ruff", "check", "."])
    run(["ruff", "format", "--check", "."])


def task_fmt() -> None:
    """Auto-fix lint issues and format the code."""
    run(["ruff", "check", "--fix", "."])
    run(["ruff", "format", "."])


def task_render() -> None:
    """Render the bilingual Quarto website into `site/_site/`."""
    require("quarto", "install Quarto: https://quarto.org/docs/get-started/")
    # Two builds of one project, because Quarto allows exactly one navbar per
    # website and there is no per-directory override. They cannot share an
    # output directory: a render empties the directory it writes to, and the
    # profile with no page at the site root also emits a redirect `index.html`
    # that would replace the English home page.
    run(["quarto", "render", "--profile", "en"], cwd=SITE)
    run(["quarto", "render", "--profile", "pt"], cwd=SITE)
    source = BUILD_PT / "pt"
    destination = SITE / "_site" / "pt"
    shutil.rmtree(destination, ignore_errors=True)
    shutil.copytree(source, destination)
    print(f"copied {source.relative_to(SITE)} -> {destination.relative_to(SITE)}")


def task_preview() -> None:
    """Live-preview the Quarto website."""
    require("quarto", "install Quarto: https://quarto.org/docs/get-started/")
    run(["quarto", "preview"], cwd=SITE)


def task_publish() -> None:
    """Publish the already-rendered site to the `gh-pages` branch."""
    require("quarto", "install Quarto: https://quarto.org/docs/get-started/")
    # `--no-render` publishes `_site` as `task_render` built it; letting Quarto
    # render here would produce the English build only.
    run(["quarto", "publish", "gh-pages", "--no-render"], cwd=SITE)


def task_pipeline() -> None:
    """The full reproducible pipeline, in order."""
    task_load()
    task_dbt_build()
    task_charts()
    task_test()
    task_render()


def task_clean() -> None:
    """Remove caches and build artefacts (never touches `data/`)."""
    targets = [
        ROOT / ".pytest_cache",
        ROOT / ".ruff_cache",
        SITE / "_site",
        BUILD_PT,
        SITE / ".quarto",
        DBT_DIR / "target",
        DBT_DIR / "dbt_packages",
        DBT_DIR / "logs",
    ]
    for path in targets:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            print(f"removed {path.relative_to(ROOT)}")
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    print("clean.")


TASKS: dict[str, tuple[str, object]] = {
    "doctor": ("Report which required tools are installed", task_doctor),
    "setup": ("Install deps + start database + download data (run once)", task_setup),
    "data": ("Download and validate the Olist dataset", task_data),
    "db-up": ("Start the PostgreSQL service", task_db_up),
    "db-down": ("Stop the PostgreSQL service", task_db_down),
    "db-reset": ("Destroy the database volume and recreate it", task_db_reset),
    "load": ("Load raw CSVs into the `raw` schema", task_load),
    "charts": ("Regenerate the report charts from the marts", task_charts),
    "dbt-build": ("Build and test all dbt models", task_dbt_build),
    "dbt-docs": ("Generate the dbt docs site", task_dbt_docs),
    "test": ("Run the Python test suite", task_test),
    "lint": ("Check lint + formatting", task_lint),
    "fmt": ("Auto-fix lint + format", task_fmt),
    "render": ("Render the Quarto website", task_render),
    "preview": ("Live-preview the Quarto website", task_preview),
    "publish": ("Publish the site to the `gh-pages` branch", task_publish),
    "pipeline": ("load -> dbt build -> tests -> render", task_pipeline),
    "clean": ("Remove caches and build artefacts", task_clean),
}


def main(argv: list[str]) -> int:
    load_dotenv()

    if len(argv) != 1 or argv[0] in {"-h", "--help", "help", "list"}:
        print(__doc__.strip().split("USAGE")[0].strip())
        print("\nTasks:\n")
        width = max(len(name) for name in TASKS)
        for name, (description, _) in TASKS.items():
            print(f"  {name:<{width}}  {description}")
        print("\nUsage: uv run python tasks.py <task>\n")
        return 0

    name = argv[0]
    if name not in TASKS:
        print(f"unknown task: {name!r}\nRun `python tasks.py` to list tasks.", file=sys.stderr)
        return 2

    _, func = TASKS[name]
    func()  # type: ignore[operator]
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
