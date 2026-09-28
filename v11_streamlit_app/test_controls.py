"""Runtime regressions for the existing analysis-page controls."""
from pathlib import Path
import sys
import json
import unittest

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "v11_streamlit_app")]
VIEWS = ROOT / "v11_streamlit_app" / "views"


class AnalysisControlTests(unittest.TestCase):
    def test_scenario_reset_runs_before_widgets_are_rendered(self):
        app = AppTest.from_file(str(VIEWS / "03_Scenario_Explorer.py"), default_timeout=90)
        app.session_state["expv5_mc_runs"] = 20
        app.run()
        initial = app.slider(key="expv5_cv_cav_growth_rate").value
        app.slider(key="expv5_cv_cav_growth_rate").set_value(0.1).run()
        self.assertEqual(list(app.exception), [])
        app.button(key="expv5_btn_reset_mit").click().run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.slider(key="expv5_cv_cav_growth_rate").value, initial)

    def test_propulsion_inputs_are_nonnegative_and_accept_zero(self):
        app = AppTest.from_file(str(VIEWS / "02_Utility-Phase_Energy.py"), default_timeout=90).run()
        self.assertEqual(len(app.number_input), 2)
        for widget in app.number_input:
            self.assertEqual(widget.proto.min, 0)
            widget.set_value(0.0)
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual(len(app.get("plotly_chart")), 3)

    def test_one_time_inventory_views_render(self):
        app = AppTest.from_file(str(VIEWS / "01_One-Time_Embodied_Energy.py"), default_timeout=90).run()
        for option in app.radio(key="ot_fig_c_view").options:
            app.radio(key="ot_fig_c_view").set_value(option).run()
            self.assertEqual(list(app.exception), [])
            self.assertEqual(len(app.get("plotly_chart")), 6)

    def test_end_of_life_axis_contains_both_design_bounds(self):
        app = AppTest.from_file(str(VIEWS / "01_One-Time_Embodied_Energy.py"), default_timeout=90).run()
        chart = json.loads(app.get("plotly_chart")[-1].proto.spec)
        limits = chart["layout"]["xaxis"]["range"]
        values = [value for trace in chart["data"] for value in trace["x"]]
        self.assertLess(limits[0], min(values))
        self.assertGreater(limits[1], max(values))
        self.assertEqual(chart["layout"]["uniformtext"], {"minsize": 11, "mode": "hide"})
        for trace in chart["data"]:
            for value, position in zip(trace["x"], trace["textposition"]):
                if value < 0:
                    self.assertEqual(position, "inside")


if __name__ == "__main__":
    unittest.main()
