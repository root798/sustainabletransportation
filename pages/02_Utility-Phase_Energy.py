"""Root-level shim that delegates to the v11 page (see 01 for rationale)."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
for p in (_HERE, _HERE / "v4_streamlit_app", _HERE / "src",
          _HERE / "v11_streamlit_app"):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

runpy.run_path(
    str(_HERE / "v11_streamlit_app" / "pages"
        / "02_Utility-Phase_Energy.py"),
    run_name="__main__",
)
