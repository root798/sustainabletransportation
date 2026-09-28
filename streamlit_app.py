"""Local entrypoint; shares navigation with the deployed Cloud entrypoint."""
from dashboard_runtime import prepare_ui_release

prepare_ui_release("2026.09.28.3")
from dashboard_navigation import main

main()
