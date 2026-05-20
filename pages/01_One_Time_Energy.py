"""Root-level shim that delegates to the v11 page.

Streamlit's multi-page UI scans the ``pages/`` folder that sits NEXT TO
the file you launch Streamlit against — i.e. the root
``streamlit_app.py``. So we keep three thin shims here whose only job is
to add the v11 stack to ``sys.path`` and execute the real page module.
"""
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
    str(_HERE / "v11_streamlit_app" / "pages" / "01_One_Time_Energy.py"),
    run_name="__main__",
)
