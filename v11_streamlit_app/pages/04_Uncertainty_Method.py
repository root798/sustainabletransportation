"""Final page for the original CLEAR-ATS uncertainty-method overview."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent.parent
_REPO_DIR = _APP_DIR.parent
for path in (_REPO_DIR, _REPO_DIR / "v4_streamlit_app",
             _REPO_DIR / "src", _APP_DIR):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

runpy.run_path(
    str(_APP_DIR / "uncertainty_method.py"),
    run_name="__main__",
)
