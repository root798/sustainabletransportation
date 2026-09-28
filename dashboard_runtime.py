"""Refresh presentation modules once per UI release, retaining model caches."""
from pathlib import Path
import importlib
import sys
from threading import Lock


ROOT = Path(__file__).resolve().parent
RUNTIME_RELEASE = "2026.09.28.8"
_release = None
_lock = Lock()
_UI_MODULES = {
    "dashboard_navigation": "dashboard_navigation.py",
    "dashboard_ui": "dashboard_ui.py",
    # atlas_io contains the registered panel-to-interval mapping as well as
    # loaders.  Keeping an older import across a Cloud hot reload can otherwise
    # pair new chart code with a stale metric mapping.
    "atlas_io": "national_atlas/atlas_io.py",
    "charts": "national_atlas/charts.py",
    "pathway_charts": "national_atlas/pathway_charts.py",
    "style": "national_atlas/style.py",
}


def prepare_ui_release(release: str) -> None:
    """An updated entrypoint must not reuse pre-deployment UI imports.

    Streamlit can rerun the entrypoint in a surviving process. Only our known
    presentation modules are invalidated, once; data, model modules and the
    user's session state are untouched. Existing in-flight references remain
    valid while the next render imports the updated code.
    """
    global _release
    with _lock:
        if _release == release:
            return
        for name, relative in _UI_MODULES.items():
            module = sys.modules.get(name)
            source = getattr(module, "__file__", None)
            if source and Path(source).resolve() == ROOT / relative:
                sys.modules.pop(name, None)
        importlib.invalidate_caches()
        _release = release
