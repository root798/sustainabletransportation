"""Top-level Streamlit entry point for the CLEAR-ATS v11 dashboard.

Streamlit Community Cloud and most other Streamlit hosts auto-detect a
file named ``streamlit_app.py`` at the repository root. This shim sets
up ``sys.path`` so the v11 dashboard finds all of its dependencies and
then executes the v11 Overview page (which Streamlit's multi-page
navigation extends with ``pages/01_One_Time_Energy.py``,
``pages/02_Utility_Phase_Energy.py``, and
``pages/03_Scenario_Explorer.py``).

Required deploy tree on GitHub (see ``.gitignore`` whitelist):

  streamlit_app.py            <- this file
  requirements.txt
  .streamlit/config.toml
  footprint_model.py          <- engine, imported by v4 core
  configs/                    <- state JSON + UI presets
  scenarios/                  <- per-state scenario trees
  v4_streamlit_app/           <- v4 core (v11/core.py loads it dynamically)
  v11_streamlit_app/          <- the dashboard
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

# Order matters: prepend in REVERSE priority so the v11 dashboard's
# package takes precedence, with the repo root (where ``footprint_model.py``
# lives), the v4 folder (for the dynamic load), and ``src`` (for
# ``clearats``) all reachable for downstream imports.
_PATHS = [
    _HERE,                          # repo root  -> footprint_model
    _HERE / "v4_streamlit_app",     # v4 core    -> dynamically loaded by v11
    _HERE / "src",                  # clearats   -> band plumbing
    _HERE / "v11_streamlit_app",    # v11 first  -> the dashboard
]
for p in _PATHS:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Hand off to the v11 Overview page. Streamlit's multi-page UI picks
# up the sibling ``pages/`` folder automatically.
runpy.run_path(
    str(_HERE / "v11_streamlit_app" / "streamlit_app.py"),
    run_name="__main__",
)
