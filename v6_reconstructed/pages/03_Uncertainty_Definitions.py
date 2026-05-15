"""v6 page 03 — Uncertainty Definitions.

Inherits v5 visual tone. Calculations are not invoked here; this is a
documentation page that maps the existing L1 / L2 / L3 layer objects to
epistemic / aleatoric vocabulary inspired by the 2025 Nature Communications
Puerto Rico energy-transition paper, in a way that does NOT contradict how
the v5 calculations actually behave.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from figure_style import NATURE_LAYER  # noqa: E402

st.set_page_config(page_title="Uncertainty Definitions",
                   page_icon="C", layout="wide")

st.title("Uncertainty Definitions")
st.caption(
    "Maps the existing CLEAR-ATS layer objects (L1 / L2 / L3) to "
    "epistemic and aleatoric vocabulary. Calculations are unchanged from v5; "
    "only the names and explanations are improved."
)

st.info(
    "Hard rule for this page: any label below must be honest about how the "
    "v5 code actually computes the layer. We do not relabel a mixed-source "
    "layer as a 'pure' epistemic or aleatoric object."
)

st.subheader("Compact taxonomy table")

st.markdown(
    """
| Current layer | Current role in v5 | Improved label (v6) | Uncertainty type | Interpretation |
|---|---|---|---|---|
| **L1** | Evidence-anchored emission-factor uncertainty (e_clean, e_fossil, e_gasoline). Distributions are tight; the band stays narrow. | *Within-scenario residual / aleatoric-style variability — emission factors* | Aleatoric-style residual (close to irreducible at decision time) | Captures short-horizon variability that does not scale with how far into the future you look. Late-horizon narrowing of L1 width is a saturation effect, not improved predictive skill. |
| **L2** | Load-model residual uncertainty (subsystem scale factors, ICEV overhead, cohort decay). Lognormal-ish priors with elicitation-tightened σ in v5.1.7. | *Within-scenario residual / aleatoric-style variability — load model* | Aleatoric-style residual + a small epistemic component (some priors are weakly identified) | Treat as the within-scenario conditional band. Reviewer-defensible reading is "given the chosen pathway, this is the residual annual variability". Not a forecast confidence interval. |
| **L3** | Pathway / trajectory parameter uncertainty (CAV target, STI target, BEV growth, clean-grid growth, hardware doubling time, fleet growth, service life). Drives the largest long-horizon divergence. | *Pathway / epistemic uncertainty (long-horizon driver)* | Epistemic | This is the layer responsible for the wide late-horizon spread. It does NOT mean the future is unknowable; it means the answer depends on which pathway the world ends up on. Mitigate by reporting benchmark-year marginals and named scenarios, not by widening a single band. |
| **Scenario family** | Three policy patches (baseline / aggressive / conservative). Analyst selects one. | *Scenario uncertainty* (kept as in v5) | Scenario (not probabilized) | Comparing scenarios is not the same as a confidence interval. v5 already separates this. |
| **Structural shock** | Five discrete labelled JSONs (`scenarios/shocks/*.json`). | *Structural-shock uncertainty* (kept as in v5) | Discrete labelled scenario family | Plot side-by-side with baseline. Never blend into baseline quantile CSVs. |
    """
)

st.subheader("Per-layer interpretation block")

st.markdown(
    """
- **L1 / L2 — within-scenario residual / aleatoric-style variability.**
  These layers describe how much the annual ATS output can vary *within a
  pathway you have already chosen*. The band can narrow at late horizons
  because emissions are bounded below — that is a saturation artefact,
  not improved certainty. Read this band as a **conditional** interval.

- **L3 — pathway / epistemic uncertainty (long-horizon driver).**
  This layer is what produces the wide spread you see at late horizons. The
  spread is large because future BEV growth, future clean-grid growth,
  future CAV / STI deployment targets, and hardware efficiency learning
  rates are *not yet known*. The right way to mitigate L3 is **not** to
  widen a band; it is to report **benchmark-year marginals** at named
  milestone years and to compare **named pathway scenarios** explicitly.

- **Scenario uncertainty.** Selecting baseline vs aggressive vs conservative
  is a discrete analyst choice. The spread between scenarios is *not*
  a 95% confidence interval — it is the model's response to a different
  set of pathway assumptions.

- **Structural-shock uncertainty.** Five discrete labelled scenarios in
  `scenarios/shocks/*.json`. Compared visually to baseline; never blended
  into the probabilistic quantile bundles.
    """
)

st.subheader("What this means for reading the existing v5 figures")

st.markdown(
    """
- The **emissions band** in the Scenario Explorer (Figure A) is a
  *within-scenario* object. Inside the interpretation-boundary year it can
  carry a quantitative reading; outside that year, treat it as a
  conditional envelope and prefer the benchmark-year distributions
  (page 05).
- The **driver bar chart** (Figure B) ranks parameters by how much they
  widen the within-scenario band — a useful sensitivity view, but not the
  same as global Sobol decomposition. v6 page 06 adds an L3-focused view
  using the existing `PARAMETER_CONTRIBUTION_EXPERIMENT.csv` data.
- The **layer summary** (Figure C) is the L1 vs L2 vs L3 contribution
  decomposition. v6 simply gives those layers more honest English names
  via this page.
    """
)

st.subheader("Layer colour mapping (kept identical to v5)")

palette = pd.DataFrame(
    [
        {"Layer": "L1", "Hex": NATURE_LAYER["L1"], "v6 label": "Within-scenario residual / emission-factor variability"},
        {"Layer": "L2", "Hex": NATURE_LAYER["L2"], "v6 label": "Within-scenario residual / load-model variability"},
        {"Layer": "L3", "Hex": NATURE_LAYER["L3"], "v6 label": "Pathway / epistemic uncertainty (long-horizon driver)"},
    ]
)

cols = st.columns([1, 1, 4])
for layer, hex_color in NATURE_LAYER.items():
    cols[0].markdown(f"<div style='background:{hex_color};width:30px;height:18px;'></div>",
                     unsafe_allow_html=True)
    cols[1].markdown(f"**{layer}**")
    cols[2].markdown(palette.loc[palette["Layer"] == layer, "v6 label"].values[0])

st.dataframe(palette, use_container_width=True, hide_index=True)

st.caption(
    "Reference: see `reports/UNCERTAINTY_NAMING_AND_INTERPRETATION_V6.md` "
    "for the full naming-decision rationale and `audits/uncertainty_governance/`"
    " for the per-parameter contribution data."
)
