"""Existing Streamlit Cloud entrypoint for the CLEAR-ATS dashboard."""
import importlib
from pathlib import Path
import sys

_REPO_DIR = Path(__file__).resolve().parent.parent
if str(_REPO_DIR) not in sys.path:
    sys.path.insert(0, str(_REPO_DIR))

import dashboard_runtime as _dashboard_runtime

if getattr(_dashboard_runtime, "RUNTIME_RELEASE", None) != "2026.09.28.8":
    _dashboard_runtime = importlib.reload(_dashboard_runtime)

_dashboard_runtime.prepare_ui_release("2026.09.28.8")
from dashboard_navigation import main

main()
