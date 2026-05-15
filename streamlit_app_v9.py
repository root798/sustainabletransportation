"""Root entry point for the v9 CLEAR-ATS Streamlit dashboard.

Streamlit Cloud expects a top-level entry script. This file forwards
into ``v9_streamlit_app/streamlit_app.py`` so the v9 multi-page app can
be launched with ``streamlit run streamlit_app_v9.py``. Earlier
versions (v3 / v4 / v5 / v6 / v7 / v8) keep their own entry points and
are not affected.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_V9_DIR = Path(__file__).resolve().parent / "v9_streamlit_app"
if str(_V9_DIR) not in sys.path:
    sys.path.insert(0, str(_V9_DIR))

runpy.run_path(str(_V9_DIR / "streamlit_app.py"), run_name="__main__")
