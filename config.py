import os
import sys
from pathlib import Path

from dotenv import load_dotenv


# Find the folder where the EXE/project is running
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent


# Load .env from the same folder as the EXE
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)


GRAYLOG_URL = os.getenv("GRAYLOG_URL")
GRAYLOG_USERNAME = os.getenv("GRAYLOG_USERNAME")
GRAYLOG_PASSWORD = os.getenv("GRAYLOG_PASSWORD")
INFRA_POSTGRES_DBNAME = os.getenv("INFRA_POSTGRES_DBNAME")
INFRA_POSTGRES_PASS = os.getenv("INFRA_POSTGRES_PASS")
INFRA_POSTGRES_HOST = os.getenv("INFRA_POSTGRES_HOST")
INFRA_POSTGRES_USER = os.getenv("INFRA_POSTGRES_USER")


DOWNLOAD_DIR = Path.home() / "Downloads"

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

# Save output on the computer of the person running the EXE
OUTPUT_DIR = DESKTOP_DIR / "graylog_outputs"


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
