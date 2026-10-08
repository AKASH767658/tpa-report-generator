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


DOWNLOAD_DIR = Path.home() / "Downloads"

# Save output on the computer of the person running the EXE
OUTPUT_DIR = Path.home() / "Desktop" / "graylog_outputs"


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