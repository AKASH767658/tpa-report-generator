import os
import sys
from pathlib import Path

from dotenv import load_dotenv


# Project paths are resolved from the repository root so the app works from
# PowerShell, Streamlit, tests, and a packaged executable.
if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

BASE_DIR = PROJECT_ROOT


# Load .env from the same folder as the EXE
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)


def _resolve_path(value, default):
    path = Path(value or default).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


GRAYLOG_URL = os.getenv("GRAYLOG_URL")
GRAYLOG_USERNAME = os.getenv("GRAYLOG_USERNAME")
GRAYLOG_PASSWORD = os.getenv("GRAYLOG_PASSWORD")
SPAI_PROD_DASHBOARD_URL = os.getenv("SPAI_PROD_DASHBOARD_URL")
INFRA_POSTGRES_DBNAME = os.getenv("INFRA_POSTGRES_DBNAME")
INFRA_POSTGRES_PASS = os.getenv("INFRA_POSTGRES_PASS")
INFRA_POSTGRES_HOST = os.getenv("INFRA_POSTGRES_HOST")
INFRA_POSTGRES_USER = os.getenv("INFRA_POSTGRES_USER")


DATA_PATH = _resolve_path(os.getenv("DATA_PATH"), "data")
DATA_PATH.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR = DATA_PATH

# Resolve the Desktop as configured by Windows. On this computer it is
# redirected to OneDrive, so Path.home() / "Desktop" is not the visible
# Desktop folder. Fall back to the normal local Desktop when OneDrive is not
# configured.
_desktop_candidates = [
    os.getenv("OneDrive"),
    os.getenv("OneDriveCommercial"),
    os.getenv("OneDriveConsumer"),
]
DESKTOP_DIR = next(
    (
        Path(candidate) / "Desktop"
        for candidate in _desktop_candidates
        if candidate and (Path(candidate) / "Desktop").is_dir()
    ),
    Path.home() / "Desktop",
)

# Graylog CSV downloads and report input files share one configured location.
OUTPUT_DIR = DATA_PATH

BRANDING_DIR = PROJECT_ROOT / "ui" / "assets" / "branding"
BRANDING_CONFIG_FILE = BRANDING_DIR / "branding.json"


# Clear error if configuration is missing
if not GRAYLOG_URL:
    raise RuntimeError(
        "GRAYLOG_URL is missing. Please check the .env file."
    )

if not GRAYLOG_USERNAME:
    raise RuntimeError(
        "GRAYLOG_USERNAME is missing. Please check the .env file."
    )

if not GRAYLOG_PASSWORD:
    raise RuntimeError(
        "GRAYLOG_PASSWORD is missing. Please check the .env file."
    )
