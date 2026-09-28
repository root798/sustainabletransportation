"""Existing Streamlit Cloud entrypoint for the CLEAR-ATS dashboard."""
from pathlib import Path
import sys

_REPO_DIR = Path(__file__).resolve().parent.parent
if str(_REPO_DIR) not in sys.path:
    sys.path.insert(0, str(_REPO_DIR))

from dashboard_runtime import prepare_ui_release

prepare_ui_release("2026.09.28.6")
from dashboard_navigation import main

main()
