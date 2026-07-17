import os
from pathlib import Path


APP_NAME = "SIGD-ST"
APP_VERSION = "0.6.0"
APP_STATE = "ALFA"

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"
EXPEDIENTES_STORAGE_DIR = STORAGE_DIR / "expedientes"


def get_database_url() -> str | None:
    return os.getenv("SIGD_ST_DATABASE_URL")
