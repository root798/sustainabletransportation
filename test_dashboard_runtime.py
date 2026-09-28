"""A new UI deployment cannot retain an earlier navigation/tooltip module."""
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

import dashboard_runtime as runtime


class UIReleaseTests(unittest.TestCase):
    def test_changed_release_refreshes_only_owned_presentation_modules(self):
        charts = types.ModuleType("charts")
        charts.__file__ = str(runtime.ROOT / "national_atlas/charts.py")
        model = types.ModuleType("core")
        model.__file__ = str(runtime.ROOT / "v11_streamlit_app/core.py")
        with patch.dict(sys.modules, {"charts": charts, "core": model}), patch.object(runtime, "_release", "old"):
            runtime.prepare_ui_release("new")
            self.assertNotIn("charts", sys.modules)
            self.assertIs(sys.modules["core"], model)
            sys.modules["charts"] = charts
            runtime.prepare_ui_release("new")
            self.assertIs(sys.modules["charts"], charts)

    def test_foreign_module_with_same_name_is_not_evicted(self):
        module = types.ModuleType("charts")
        module.__file__ = "/unrelated/charts.py"
        with patch.dict(sys.modules, {"charts": module}), patch.object(runtime, "_release", None):
            runtime.prepare_ui_release("new")
            self.assertIs(sys.modules["charts"], module)

    def test_entrypoints_and_visible_release_agree(self):
        for path in ("streamlit_app.py", "v11_streamlit_app/streamlit_app.py", "dashboard_navigation.py"):
            self.assertIn("2026.09.28.6", (runtime.ROOT / path).read_text())


if __name__ == "__main__":
    unittest.main()
