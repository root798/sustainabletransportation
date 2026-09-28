"""Regression checks for the shared Streamlit entrypoints.

Run from the repository root with:
    python -m unittest v11_streamlit_app.test_navigation
"""
from pathlib import Path
import hashlib
import importlib
import json
import re
import sys
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np
from streamlit.testing.v1 import AppTest

import dashboard_navigation as navigation
from dashboard_ui import PAGE_INFO


PAGE_ORDER = (
    "home",
    "one_time",
    "utility",
    "scenario",
    "atlas",
    "uncertainty",
)


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
                self.assertEqual([title.value for title in app.title], ["CLEAR-ATS Dashboard"])
                registry = app.session_state["_clearats_page_registry"]
                self.assertEqual(list(registry), list(PAGE_ORDER))
                self.assertTrue(registry["home"]._default)

    def test_navigation_page_order_and_paths(self):
        app = AppTest.from_file(
            str(navigation.ROOT / "streamlit_app.py"), default_timeout=90
        ).run()
        self.assertEqual([error.message for error in app.exception], [])

        registry = app.session_state["_clearats_page_registry"]
        self.assertEqual(list(registry), list(PAGE_ORDER))
        self.assertEqual(
            [registry[key].title for key in PAGE_ORDER],
            [PAGE_INFO[key]["title"] for key in PAGE_ORDER],
        )
        paths = [registry[key].url_path for key in PAGE_ORDER]
        self.assertEqual(paths, [PAGE_INFO[key]["path"] for key in PAGE_ORDER])
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(registry["scenario"].url_path, "Scenario_Explorer")
        self.assertLess(PAGE_ORDER.index("scenario"), PAGE_ORDER.index("atlas"))
        self.assertEqual(PAGE_ORDER[-1], "uncertainty")

    def test_home_cards_link_to_every_registered_destination(self):
        app = AppTest.from_file(
            str(navigation.ROOT / "streamlit_app.py"), default_timeout=90
        ).run()
        self.assertEqual([error.message for error in app.exception], [])

        expected_keys = PAGE_ORDER[1:]
        expected_paths = [str(PAGE_INFO[key]["path"]) for key in expected_keys]
        expected_labels = [str(PAGE_INFO[key]["title"]) for key in expected_keys]
        links = app.get("page_link")
        self.assertEqual([link.proto.page for link in links], expected_paths)
        self.assertEqual([link.proto.label for link in links], expected_labels)

        for link in links:
            # The exact destination paths above are public link properties.
            # AppTest's private page registry differs between Streamlit versions.
            self.assertTrue(link.proto.page_script_hash)
        self.assertEqual(len({link.proto.page_script_hash for link in links}), len(expected_keys))

        valid_keys = set(PAGE_INFO)
        for key, info in PAGE_INFO.items():
            related = tuple(info["related"])
            self.assertNotIn(key, related)
            self.assertTrue(set(related).issubset(valid_keys))

    def test_manuscript_assets_match_manifest_and_svg_crop(self):
        assets = navigation.ROOT / "dashboard_assets"
        manifest = json.loads(
            (assets / "manuscript_figure_sources.json").read_text(
                encoding="utf-8"
            )
        )
        expected_crop = {
            2: (785.084, 321.611),
            3: (1714.08, 753.12),
        }
        self.assertEqual(
            [record["figure"] for record in manifest["figures"]], [2, 3]
        )

        for record in manifest["figures"]:
            with self.subTest(figure=record["figure"]):
                pdf = assets / record["pdf"]
                svg = assets / record["svg"]
                self.assertTrue(pdf.is_file())
                self.assertTrue(svg.is_file())
                self.assertEqual(
                    hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    record["sha256"],
                )

                root = ET.parse(svg).getroot()
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                width_match = re.fullmatch(
                    r"([0-9]+(?:\.[0-9]+)?)pt", root.attrib.get("width", "")
                )
                height_match = re.fullmatch(
                    r"([0-9]+(?:\.[0-9]+)?)pt", root.attrib.get("height", "")
                )
                self.assertIsNotNone(width_match)
                self.assertIsNotNone(height_match)
                width = float(width_match.group(1))
                height = float(height_match.group(1))
                view_box = [
                    float(value) for value in root.attrib["viewBox"].split()
                ]
                self.assertEqual(len(view_box), 4)
                self.assertEqual(view_box[:2], [0.0, 0.0])
                self.assertGreater(width, 0.0)
                self.assertGreater(height, 0.0)
                expected_width, expected_height = expected_crop[record["figure"]]
                self.assertAlmostEqual(width, expected_width, places=3)
                self.assertAlmostEqual(height, expected_height, places=3)
                self.assertAlmostEqual(view_box[2], width, places=6)
                self.assertAlmostEqual(view_box[3], height, places=6)

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
