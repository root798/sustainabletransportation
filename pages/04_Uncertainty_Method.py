"""Final-page shim for the original v11 uncertainty-framework overview."""
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
    str(_HERE / "v11_streamlit_app" / "streamlit_app.py"),
    run_name="__main__",
)
