"""v6 page 04 — Uncertainty Architecture.

A clean three-stage schematic adapted to CLEAR-ATS, inspired by recent
energy-transition uncertainty papers but rendered in the v5 colour
language. Pure visualization; no calculation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from figure_style import (  # noqa: E402
    NATURE_CATEGORICAL,
    NATURE_LAYER,
    plotly_layout_defaults,
    rgba,
)

st.set_page_config(page_title="Uncertainty Architecture",
                   page_icon="C", layout="wide")

st.title("Uncertainty Architecture")
st.caption(
    "Three-stage schematic adapted to CLEAR-ATS. Stage 1: deterministic "
    "reference path (v5 baseline). Stage 2: within-scenario uncertainty + "
    "scenario-conditioned uncertainty. Stage 3: driver identification / "
    "interpretation. v5 calculations and figures are unchanged."
)


def _stage_box(fig: go.Figure, x0: float, x1: float, y0: float, y1: float,
               header: str, body: str, color: str) -> None:
    fig.add_shape(
        type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
        line=dict(color=color, width=2),
        fillcolor=rgba(color, 0.08),
    )
    fig.add_annotation(
        x=(x0 + x1) / 2, y=y1 - 0.06,
        text=f"<b>{header}</b>",
        showarrow=False,
        font=dict(size=14, color=color),
        align="center",
    )
    fig.add_annotation(
        x=(x0 + x1) / 2, y=(y0 + y1) / 2 - 0.05,
        text=body,
        showarrow=False,
        font=dict(size=11, color=NATURE_CATEGORICAL["neutral"]),
        align="center",
    )


def _arrow(fig: go.Figure, x0: float, y0: float, x1: float, y1: float,
           color: str) -> None:
    fig.add_annotation(
        x=x1, y=y1, ax=x0, ay=y0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1.4, arrowwidth=2,
        arrowcolor=color, opacity=0.85,
    )


def build_schematic() -> go.Figure:
    fig = go.Figure()

    # Three stage rectangles
    _stage_box(fig, 0.02, 0.32, 0.20, 0.85,
               "Stage 1 — Deterministic reference",
               "v5 baseline trajectory<br>under median inputs.<br>"
               "Annual ATS emissions,<br>peak year, turning year,<br>"
               "subsystem shares.",
               NATURE_CATEGORICAL["primary"])
    _stage_box(fig, 0.36, 0.66, 0.20, 0.85,
               "Stage 2 — Uncertainty propagation",
               "Within-scenario residual band<br>(L1 / L2 — aleatoric-style)<br>"
               "+ scenario-conditioned envelope<br>(L3 — pathway / epistemic)<br>"
               "+ structural-shock comparison.",
               NATURE_CATEGORICAL["secondary"])
    _stage_box(fig, 0.70, 0.98, 0.20, 0.85,
               "Stage 3 — Driver & interpretation",
               "Top epistemic drivers<br>(parameter contribution)<br>"
               "+ benchmark-year marginals<br>+ relative uncertainty<br>"
               "+ interpretation-boundary year.",
               NATURE_CATEGORICAL["tertiary"])

    # Arrows between stages
    _arrow(fig, 0.32, 0.52, 0.36, 0.52, NATURE_CATEGORICAL["neutral"])
    _arrow(fig, 0.66, 0.52, 0.70, 0.52, NATURE_CATEGORICAL["neutral"])

    # Layer chips
    chip_y = 0.10
    for x, layer, label in [
        (0.18, "L1", "L1 — emission-factor residual"),
        (0.50, "L2", "L2 — load-model residual"),
        (0.84, "L3", "L3 — pathway / epistemic"),
    ]:
        col = NATURE_LAYER[layer]
        fig.add_shape(
            type="rect", x0=x - 0.08, x1=x + 0.08, y0=chip_y - 0.03, y1=chip_y + 0.03,
            line=dict(color=col, width=1.5),
            fillcolor=rgba(col, 0.20),
        )
        fig.add_annotation(
            x=x, y=chip_y, text=f"<b>{layer}</b>",
            showarrow=False, font=dict(size=11, color=col),
        )
        fig.add_annotation(
            x=x, y=chip_y - 0.06, text=label,
            showarrow=False, font=dict(size=10, color=NATURE_CATEGORICAL["neutral"]),
        )

    # Title strip
    fig.add_annotation(
        x=0.5, y=0.94,
        text="<b>CLEAR-ATS uncertainty architecture (v6)</b>",
        showarrow=False, font=dict(size=15, color=NATURE_CATEGORICAL["neutral"]),
    )

    layout = plotly_layout_defaults()
    layout["xaxis"].update({"range": [0, 1], "showgrid": False, "showline": False,
                             "ticks": "", "showticklabels": False, "zeroline": False})
    layout["yaxis"].update({"range": [0, 1], "showgrid": False, "showline": False,
                             "ticks": "", "showticklabels": False, "zeroline": False})
    layout["margin"] = {"t": 24, "b": 24, "l": 24, "r": 24}
    layout["height"] = 460
    fig.update_layout(layout)
    return fig


st.plotly_chart(build_schematic(), use_container_width=True)

st.subheader("Reading the diagram")

st.markdown(
    """
- **Stage 1** is the v5 deterministic baseline trajectory. This is the
  shape the dashboard uses as a reference. It is *not* the median of the
  Monte Carlo distribution; it is the trajectory under median inputs.
- **Stage 2** is where the existing v5 uncertainty objects live:
    - the **within-scenario residual band** in Figure A of the Scenario
      Explorer, carrying L1 + L2 (aleatoric-style residual variability);
    - the **scenario envelope** toggle of Figure A, which additionally
      samples Block 1 trajectory levers (L3 — pathway / epistemic);
    - the **structural-shock** comparison via discrete labelled scenarios
      in `scenarios/shocks/`.
- **Stage 3** is where the new v6 pages add value:
    - **Key Epistemic Drivers** (page 06) ranks the L3 / pathway parameters
      using existing `PARAMETER_CONTRIBUTION_EXPERIMENT.csv` data;
    - **Benchmark-Year Distributions** (page 05) extracts conditional
      marginals at 2035, 2045, 2055, 2075 from existing committed MC
      bundles;
    - **Mitigate Long-Horizon Uncertainty** (page 07) explains how to read
      large L3 spread without claiming false predictability.

The diagram preserves the v5 colour language. Layer chips at the bottom
use the same hex codes as v5 figures so a reader can match the diagram
to the existing Scenario Explorer plots without re-learning a palette.
    """
)
