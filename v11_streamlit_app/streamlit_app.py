"""Cloud-compatible entry point for the CLEAR-ATS National Atlas."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
_REPO_DIR = _APP_DIR.parent

# Streamlit Community Cloud currently launches this file directly. Keep the
# National Atlas isolated while making its modules importable from that saved
# deployment coordinate.
for path in (_REPO_DIR, _REPO_DIR / "national_atlas"):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

runpy.run_path(
    str(_REPO_DIR / "national_atlas" / "streamlit_app.py"),
    run_name="__main__",
)
