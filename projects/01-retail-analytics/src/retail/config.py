"""Runtime configuration.

Everything comes from environment variables, with `.env` as a fallback. That
keeps local development, `tasks.py` and GitHub Actions all configured by the
same mechanism.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:  # Allows running before `uv sync` has installed anything.
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]


# src/retail/config.py -> src/retail -> src -> 01-retail-analytics -> projects -> repo root
PROJECT_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = PROJECT_DIR.parents[1]
DATA_DIR = REPO_ROOT / "data" / "raw"

# The dataset revision is pinned so the pipeline stays reproducible even if the
# upstream dataset is updated. See `datasets.py` and `.env.example`.
DEFAULT_OLIST_REVISION = "5acf1f37d7197d4979e714721a1ec13a7c3da728"


@dataclass(frozen=True)
class Settings:
    """Resolved configuration for one run of the pipeline."""

    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_user: str = "portfolio"
    postgres_password: str = "portfolio"
    postgres_db: str = "olist"
    olist_revision: str = DEFAULT_OLIST_REVISION
    data_dir: Path = DATA_DIR

    @property
    def database_url(self) -> str:
        """SQLAlchemy URL for the PostgreSQL instance in docker-compose.yml."""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return default if value is None or value == "" else value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load `.env` (once) and build the settings object."""
    if load_dotenv is not None:
        load_dotenv(REPO_ROOT / ".env")

    return Settings(
        postgres_host=_env("POSTGRES_HOST", "localhost"),
        postgres_port=int(_env("POSTGRES_PORT", "5433")),
        postgres_user=_env("POSTGRES_USER", "portfolio"),
        postgres_password=_env("POSTGRES_PASSWORD", "portfolio"),
        postgres_db=_env("POSTGRES_DB", "olist"),
        olist_revision=_env("OLIST_REVISION", DEFAULT_OLIST_REVISION),
        data_dir=Path(_env("DATA_DIR", str(DATA_DIR))),
    )
