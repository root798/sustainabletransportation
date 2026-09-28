"""Focused UI regressions for the National Atlas landing map and state flow.

Run from the repository root with::

    python -m unittest national_atlas.test_atlas_ui
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import sys
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
ATLAS_DIR = ROOT / "national_atlas"
for directory in (ATLAS_DIR, ROOT / "src", ROOT):
    value = str(directory)
    if value not in sys.path:
        sys.path.insert(0, value)

from atlas_io import (  # noqa: E402
    expert_central_turning_map_frame,
    load_expert_central,
    load_market_central,
    load_policy_central,
    load_state_scaled,
    market_central_turning_map_frame,
    policy_central_turning_map_frame,
    state_scaled_annual_row,
)
from charts import make_turning_point_map  # noqa: E402
from pathway_charts import make_state_comparison  # noqa: E402


def plot_key(plot) -> str:
    """Older AppTest releases expose Plotly keys only in the element ID."""
    return plot.key or str(plot.proto.id).split("-", 2)[-1]


class AtlasLandingUITests(unittest.TestCase):
    def test_plotly_container_does_not_add_height_outside_the_figure(self):
        theme = (ATLAS_DIR / "assets" / "theme.css").read_text(encoding="utf-8")
        self.assertIn('div[data-testid="stPlotlyChart"] { padding-top: 0; }', theme)
        self.assertNotIn('div[data-testid="stPlotlyChart"] { padding-top: 0.25rem; }', theme)

    def test_delivered_turning_points_recompute_from_annual_series(self):
        """Recompute the published endpoint without using an onset helper."""
        annual = pd.read_csv(
            ATLAS_DIR / "data" / "expert_central_v33_annual.state_scaled.csv",
            float_precision="round_trip",
        )
        delivered = pd.read_csv(
            ATLAS_DIR / "data" / "expert_central_v33_turning.state_scaled.csv",
            float_precision="round_trip",
        )
        self.assertEqual(len(annual), 51 * 51)
        self.assertEqual(annual[["state", "year"]].duplicated().sum(), 0)
        self.assertEqual(annual["state"].nunique(), 51)

        # Definition fixed by the delivered v3.3 analysis: the first year
        # followed by at least five modelled years for which every subsequent
        # annual change in direct CO2 is non-positive (within 1e-7 kg).
        independently_computed = {}
        for state, rows in annual.groupby("state", sort=True):
            rows = rows.sort_values("year")
            years = rows["year"].astype(int).tolist()
            values = rows["normalized_bundle_direct_co2_kg"].astype(float).tolist()
            self.assertEqual(years, list(range(2025, 2076)), state)
            onset = None
            for index, year in enumerate(years):
                if len(years) - 1 - index < 5:
                    break
                if all(
                    values[later + 1] - values[later] <= 1e-7
                    for later in range(index, len(values) - 1)
                ):
                    onset = year
                    break
            independently_computed[state] = onset

        expected_identified = {
            "CA": 2038,
            "CO": 2060,
            "DC": 2035,
            "NM": 2060,
            "NY": 2036,
            "OR": 2039,
            "RI": 2035,
            "VT": 2034,
            "WA": 2041,
        }
        self.assertEqual(
            {state: year for state, year in independently_computed.items() if year is not None},
            expected_identified,
        )
        self.assertIsNone(independently_computed["SD"])
        self.assertEqual(independently_computed["CA"], 2038)

        delivered_by_state = delivered.set_index("state")
        map_by_state = expert_central_turning_map_frame(
            load_expert_central()
        ).set_index("state")
        self.assertEqual(set(independently_computed), set(delivered_by_state.index))
        self.assertEqual(set(independently_computed), set(map_by_state.index))
        for state, onset in independently_computed.items():
            with self.subTest(state=state):
                table_row = delivered_by_state.loc[state]
                map_row = map_by_state.loc[state]
                if onset is None:
                    self.assertEqual(
                        table_row["turning_status"], "RIGHT_CENSORED_THROUGH_2075"
                    )
                    self.assertTrue(pd.isna(table_row["sustained_nonincrease_onset_year"]))
                    self.assertFalse(bool(map_row["has_turning_point"]))
                    self.assertTrue(pd.isna(map_row["onset_year"]))
                    self.assertEqual(map_row["onset_label"], "none by 2075")
                else:
                    self.assertEqual(table_row["turning_status"], "IDENTIFIED")
                    self.assertEqual(
                        int(table_row["sustained_nonincrease_onset_year"]), onset
                    )
                    self.assertTrue(bool(map_row["has_turning_point"]))
                    self.assertEqual(int(map_row["onset_year"]), onset)
                    self.assertEqual(map_row["onset_label"], str(onset))

    def test_comparison_basis_note_is_wrapped_and_matches_its_scope(self):
        expert = load_expert_central()
        scaled = load_state_scaled()
        for scope in ("state_scaled", "reference"):
            figure = make_state_comparison(
                expert, ["CA", "OH"], "emissions", deployment_scope=scope,
                state_scaled=scaled if scope == "state_scaled" else None,
            )
            note = next(
                annotation.text for annotation in figure.layout.annotations
                if annotation.yshift == -46
            )
            self.assertTrue(all(len(line) <= 44 for line in note.split("<br>")), note)
            plain_note = note.replace("<br>", " ")
            if scope == "state_scaled":
                self.assertIn("CAV only; STI excluded", plain_note)
                self.assertNotIn("STI shown", note)
            else:
                self.assertIn("2,988 STI units", plain_note)

    def test_landing_map_hover_is_compact(self):
        expert = load_expert_central()
        frame = expert_central_turning_map_frame(expert)
        figure = make_turning_point_map(
            frame, "turning_point", "CA", scenario="expert"
        )

        hover_templates = [
            str(trace.hovertemplate)
            for trace in figure.data
            if trace.name != "Selected state" and trace.hovertemplate
        ]
        self.assertTrue(hover_templates)
        for template in hover_templates:
            with self.subTest(template=template):
                self.assertLessEqual(len(template), 160)
                self.assertNotIn("deterministic scenario", template.lower())
                self.assertNotIn("vehicle policy", template.lower())
                self.assertNotIn("grid policy", template.lower())
                self.assertIn("Turning point:", template)

    def test_turning_map_hover_contract_across_colours_and_scenarios(self):
        expert_frame = expert_central_turning_map_frame(load_expert_central())
        policy_frame = policy_central_turning_map_frame(load_policy_central())
        market_frame = market_central_turning_map_frame(load_market_central())
        cases = (
            (expert_frame, "turning_point", "expert", "Delivered central"),
            (expert_frame, "vehicle", "expert", "Delivered central"),
            (expert_frame, "grid", "expert", "Delivered central"),
            (policy_frame, "vehicle", "policy", "Policy-registered"),
            (market_frame, "grid", "market", "Market-trend"),
        )
        for frame, color_by, scenario, scenario_label in cases:
            with self.subTest(color_by=color_by, scenario=scenario):
                figure = make_turning_point_map(
                    frame, color_by, "CA", scenario=scenario
                )
                hover_rows = {}
                for trace in figure.data:
                    if trace.name == "Selected state":
                        continue
                    template = str(trace.hovertemplate)
                    self.assertLessEqual(len(template), 160, template)
                    self.assertIn("Turning point:", template)
                    self.assertIn(scenario_label, template)
                    self.assertNotIn("vehicle policy", template.lower())
                    self.assertNotIn("grid policy", template.lower())
                    self.assertIsNotNone(trace.customdata)
                    for location, row in zip(trace.locations, trace.customdata):
                        # Only the two values actually rendered by the hover
                        # are allowed; policy classifications must not leak
                        # into Plotly's client-side payload.
                        self.assertEqual(len(row), 2, (location, row))
                        self.assertLessEqual(len(str(row[0])), 32)
                        self.assertLessEqual(len(str(row[1])), len("none by 2075"))
                        hover_rows[str(location)] = tuple(str(value) for value in row)
                self.assertEqual(len(hover_rows), 51)

                if scenario == "expert":
                    self.assertEqual(hover_rows["CA"][1], "2038")
                    self.assertEqual(hover_rows["SD"][1], "none by 2075")
                elif scenario == "market":
                    self.assertEqual(hover_rows["CA"][1], "2036")
                    self.assertEqual(hover_rows["OH"][1], "none by 2075")

    def test_state_picker_updates_map_card_and_lower_pathways(self):
        app = AppTest.from_file(
            str(ATLAS_DIR / "streamlit_app.py"), default_timeout=180
        ).run(timeout=180)
        self.assertEqual([error.message for error in app.exception], [])

        pickers = [widget for widget in app.selectbox if widget.label == "State details"]
        self.assertEqual(len(pickers), 1)
        self.assertEqual(pickers[0].value, "CA")
        self.assertTrue(any(
            plot_key(plot).startswith("bundle_triptych_CA_")
            for plot in app.get("plotly_chart")
        ))

        pickers[0].set_value("OH")
        app.run(timeout=180)
        self.assertEqual([error.message for error in app.exception], [])
        self.assertEqual(
            next(widget for widget in app.selectbox if widget.label == "State details").value,
            "OH",
        )

        expert = load_expert_central()
        state_scaled = load_state_scaled()
        map_row = expert_central_turning_map_frame(expert).loc[
            lambda frame: frame["state"] == "OH"
        ].iloc[0]
        co2_kt = (
            float(
                state_scaled_annual_row(state_scaled, "OH", 2050)[
                    "cav_direct_co2_kg_actual_fleet"
                ]
            )
            / 1e6
        )
        card_html = next(
            str(markdown.value)
            for markdown in app.markdown
            if str(markdown.value).startswith('<div class="atlas-state-facts"')
        )
        self.assertIn(
            f'<div class="atlas-fact-value">{escape(str(map_row["onset_label"]))}</div>',
            card_html,
        )
        self.assertIn(f"{co2_kt:,.1f}", card_html)
        self.assertIn(escape(str(map_row["vehicle_class_label"])), card_html)
        self.assertIn(escape(str(map_row["grid_class_label"])), card_html)

        plots = app.get("plotly_chart")
        landing_map = next(
            plot
            for plot in plots
            if plot_key(plot) == "turning_point_map_expert_turning_point_OH"
        )
        map_spec = json.loads(landing_map.proto.spec)
        selected_trace = next(
            trace for trace in map_spec["data"] if trace.get("name") == "Selected state"
        )
        self.assertEqual(selected_trace["locations"], ["OH"])

        self.assertTrue(any(
            plot_key(plot).startswith("bundle_triptych_OH_") for plot in plots
        ))
        self.assertTrue(any(
            plot_key(plot) == "grid_path_OH_expert_central" for plot in plots
        ))
        self.assertTrue(any(
            plot_key(plot) == "electric_path_OH_expert_central" for plot in plots
        ))
        self.assertTrue(any(
            str(caption.value).startswith("Ohio · Delivered-central")
            for caption in app.caption
        ))

        # Map clicks use the pending-state handoff because the picker widget
        # has already been instantiated in the event-producing run. Exercise
        # that exact rerun path as well as the keyboard picker path above.
        app.session_state["_pending_state"] = "TX"
        app.run(timeout=180)
        self.assertEqual([error.message for error in app.exception], [])
        self.assertEqual(
            next(widget for widget in app.selectbox if widget.label == "State details").value,
            "TX",
        )
        tx_plots = app.get("plotly_chart")
        self.assertTrue(any(
            plot_key(plot) == "turning_point_map_expert_turning_point_TX"
            for plot in tx_plots
        ))
        self.assertTrue(any(
            plot_key(plot).startswith("bundle_triptych_TX_") for plot in tx_plots
        ))

        # Small DC remains reachable without a tiny geographic click target.
        next(widget for widget in app.selectbox if widget.label == "State details").set_value("DC")
        app.run(timeout=180)
        self.assertEqual([error.message for error in app.exception], [])
        dc_card = next(
            str(markdown.value) for markdown in app.markdown
            if str(markdown.value).startswith('<div class="atlas-state-facts"')
        )
        self.assertIn('class="atlas-fact-value">2035</div>', dc_card)
        self.assertTrue(any(
            str(caption.value).startswith("DC is supplemental") for caption in app.caption
        ))


if __name__ == "__main__":
    unittest.main()
