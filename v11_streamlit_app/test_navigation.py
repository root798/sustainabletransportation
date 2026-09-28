"""Regression checks for the shared Streamlit entrypoints.

Run from the repository root with:
    python -m unittest v11_streamlit_app.test_navigation
"""
from pathlib import Path
import importlib
import sys
import types
import unittest
from unittest.mock import patch

import numpy as np
from streamlit.testing.v1 import AppTest

import dashboard_navigation as navigation


class NavigationTests(unittest.TestCase):
    def test_entrypoints_do_not_enable_legacy_page_discovery(self):
        # Streamlit checks this before executing the entrypoint. An adjacent
        # pages/ directory would intercept the first deep link on cold start.
        for parent in (navigation.ROOT, navigation.ROOT / "v11_streamlit_app"):
            self.assertFalse((parent / "pages").exists())

    def test_legacy_core_cache_cannot_shadow_v11(self):
        stale_core = types.ModuleType("core")
        stale_core.__file__ = str(navigation.ROOT / "v4_streamlit_app/core.py")
        old_path = list(sys.path)
        try:
            with patch.dict(sys.modules, {"core": stale_core}):
                sys.path.insert(0, str(navigation.ROOT / "v4_streamlit_app"))
                with patch.object(navigation.runpy, "run_path") as runner:
                    navigation.scenario_explorer()
                    self.assertEqual(
                        Path(sys.modules["core"].__file__).resolve(),
                        navigation.ROOT / "v11_streamlit_app/core.py",
                    )
                    self.assertTrue(hasattr(sys.modules["core"], "CAV_LEVEL_TEMPLATES"))
                    runner.assert_called_once_with(
                        str(navigation.ROOT / "v11_streamlit_app/views/03_Scenario_Explorer.py"),
                        run_name="__main__",
                    )
        finally:
            sys.path[:] = old_path

    def test_both_entrypoints_open_without_errors(self):
        for relative in ("streamlit_app.py", "v11_streamlit_app/streamlit_app.py"):
            with self.subTest(entrypoint=relative):
                app = AppTest.from_file(str(navigation.ROOT / relative), default_timeout=90).run()
                self.assertEqual([error.message for error in app.exception], [])
                self.assertTrue(any("Scenario Explorer" in title.value for title in app.title))

    def test_scenario_band_cache_tracks_settings_hash(self):
        directories = [
            str(navigation.ROOT / "v11_streamlit_app"),
            str(navigation.ROOT / "src"),
            str(navigation.ROOT),
        ]
        old_path = list(sys.path)
        try:
            sys.path[:] = directories + [
                path for path in sys.path if path not in directories
            ]
            sys.modules["core"] = importlib.import_module(
                "v11_streamlit_app.core"
            )
            page = (
                navigation.ROOT
                / "v11_streamlit_app/views/03_Scenario_Explorer.py"
            )
            app = AppTest.from_file(str(page), default_timeout=180).run(
                timeout=180
            )
            self.assertEqual([error.message for error in app.exception], [])

            first_hash = app.session_state["residual_hash"]
            first_band = app.session_state["residual_band"]
            self.assertIsNotNone(first_band)
            metric = next(iter(first_band.by_metric))
            first_trajectories = (
                first_band.for_metric(metric).trajectories.copy()
            )

            cav_target = next(
                slider for slider in app.slider
                if slider.label == "CAV target fraction by 2075"
            )
            cav_target.set_value(0.15)
            app.run(timeout=180)
            self.assertEqual([error.message for error in app.exception], [])

            second_hash = app.session_state["residual_hash"]
            second_band = app.session_state["residual_band"]
            self.assertNotEqual(first_hash, second_hash)
            self.assertFalse(np.array_equal(
                first_trajectories,
                second_band.for_metric(metric).trajectories,
            ))
        finally:
            sys.path[:] = old_path


if __name__ == "__main__":
    unittest.main()
