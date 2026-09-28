"""Top-level Streamlit entry point for the CLEAR-ATS dashboard.

Streamlit Community Cloud and most other Streamlit hosts auto-detect a
file named ``streamlit_app.py`` at the repository root. This shim makes
the 50-state + District of Columbia National Atlas the landing page.
Streamlit's legacy multi-page navigation keeps the existing v11 pages
unchanged and adds the former uncertainty-framework landing page last.

Required deploy tree on GitHub (see ``.gitignore`` whitelist):

  streamlit_app.py            <- this file
  requirements.txt
  .streamlit/config.toml
  footprint_model.py          <- engine, imported by v4 core
  configs/                    <- state JSON + UI presets
  scenarios/                  <- per-state scenario trees
  v4_streamlit_app/           <- v4 core (v11/core.py loads it dynamically)
  national_atlas/             <- National Atlas landing page + reviewed data
  v11_streamlit_app/          <- existing dashboard pages
  src/clearats/               <- band plumbing for the Scenario Explorer
  results/*_quantiles.csv     <- cached MC quantiles (offline fallback)

Why ``v4_streamlit_app`` must be on the path
--------------------------------------------
``v11_streamlit_app/core.py`` dynamically loads ``v4_streamlit_app/core.py``
via ``importlib.util.spec_from_file_location`` (lines 44-57 of that
file). It resolves the v4 location as
``V4_DIR = v11_streamlit_app/../v4_streamlit_app``, which works only if
``v4_streamlit_app/`` is a sibling of ``v11_streamlit_app/``. On
Streamlit Community Cloud's ``/mount/src/<repo>/`` mount that is exactly
the layout — provided ``v4_streamlit_app/`` is tracked in git (it is,
via the whitelist in ``.gitignore``). The previous v10 deploy hit a
FileNotFoundError here because the slim ``clean_release_v10/`` bundle
omitted ``v4_streamlit_app/``; this root entry point + the updated
``.gitignore`` together prevent that on the v11 deploy.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# The National Atlas is deliberately isolated in its own directory so its
# chart/style modules cannot shadow the existing v11 page modules.
_PATHS = [
    _HERE,
    _HERE / "national_atlas",
]
for p in _PATHS:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Hand off to the National Atlas landing page. Streamlit's multi-page UI
# continues to pick up the existing sibling ``pages/`` folder automatically.
runpy.run_path(
    str(_HERE / "national_atlas" / "streamlit_app.py"),
    run_name="__main__",
)
