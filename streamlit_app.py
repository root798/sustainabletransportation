"""Local entrypoint; shares navigation with the deployed Cloud entrypoint."""
import importlib

import dashboard_runtime as _dashboard_runtime

if getattr(_dashboard_runtime, "RUNTIME_RELEASE", None) != "2026.09.28.8":
    _dashboard_runtime = importlib.reload(_dashboard_runtime)

_dashboard_runtime.prepare_ui_release("2026.09.28.8")
from dashboard_navigation import main

main()
