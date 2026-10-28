"""Run the TPA Management Report Streamlit application."""

from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
APP_FILE = PROJECT_ROOT / "ui" / "app.py"


if __name__ == "__main__":
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "streamlit", "run", str(APP_FILE)],
            cwd=PROJECT_ROOT,
        )
    )
