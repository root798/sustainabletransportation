"""v6 page 06 — Factor Legend.

Full glossary of every F-number in the registry, with uncertainty class
(aleatoric vs epistemic), layer (L1/L2/L3), short label, and the why_class
explanation. Sourced from ``configs/parameter_labels.json::metadata``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from figure_style import NATURE_LAYER  # noqa: E402
from scenario_definitions import all_metadata, is_visible  # noqa: E402
from sidebar_legend import render_sidebar_legend  # noqa: E402

st.set_page_config(page_title="Factor Legend (v6)", page_icon="C", layout="wide")
render_sidebar_legend()

st.title("Factor Legend")
st.caption(
    "Complete F-number glossary with v6 uncertainty terminology. "
    "Aleatoric = bounded measurement / vendor variance, does NOT compound "
    "with time. Epistemic = knowledge-incompleteness, compounds. "
    "v6 introduces F29 (gasoline price), F30 (deployment lag), F31 "
    "(fleet growth epistemic envelope)."
)

meta = all_metadata()
rows = []
for f, m in meta.items():
    rows.append({
        "F-number": f,
        "Short label": m.get("short_label", ""),
        "Class": m.get("uncertainty_class", ""),
        "Layer": m.get("layer", ""),
        "v5 visible": "yes" if is_visible(f) else "hidden (duplication / placeholder)",
        "v6 introduced?": m.get("introduced_in", ""),
        "Why this class": m.get("why_class", ""),
    })
df = pd.DataFrame(rows)

# Class filter
c1, c2, c3 = st.columns(3)
with c1:
    class_filter = st.multiselect("Filter by class", ["aleatoric", "epistemic"],
                                   default=["aleatoric", "epistemic"])
with c2:
    layer_filter = st.multiselect("Filter by layer",
                                   sorted([l for l in df["Layer"].unique() if l]),
                                   default=sorted([l for l in df["Layer"].unique() if l]))
with c3:
    show_hidden = st.checkbox("Show v5-hidden parameters (duplication / placeholder)",
                              value=False)

f = df[df["Class"].isin(class_filter) & df["Layer"].isin(layer_filter)]
if not show_hidden:
    f = f[f["v5 visible"].str.startswith("yes")]

st.subheader("Glossary")
st.dataframe(f, use_container_width=True, hide_index=True)

st.subheader("Counts by class and layer")
cnt = (df[df["v5 visible"].str.startswith("yes") if not show_hidden else df.index == df.index]
       .groupby(["Class", "Layer"]).size().reset_index(name="count"))
st.dataframe(cnt, use_container_width=True, hide_index=True)

st.subheader("Layer colour mapping (v5 palette, unchanged)")
col1, col2, col3, col4 = st.columns([1, 1, 4, 4])
for layer, hex_color in NATURE_LAYER.items():
    col1.markdown(f"<div style='background:{hex_color};width:30px;height:18px;'></div>",
                  unsafe_allow_html=True)
    col2.markdown(f"**{layer}**")
    col3.markdown(hex_color)
    if layer == "L1":
        col4.markdown("Aleatoric — measured initial state + emission factors")
    elif layer == "L2":
        col4.markdown("Aleatoric — load model & vendor variance")
    elif layer == "L3":
        col4.markdown("Epistemic — long-horizon pathway uncertainty")

st.markdown(
    """
### Notes

- The **uncertainty class** column is the v6 vocabulary. v5 used L1 / L2 / L3
  layer labels only; v6 adds the *aleatoric / epistemic* dimension as an
  honest mapping. See `reports/UNCERTAINTY_NAMING_AND_INTERPRETATION_V6.md`
  for the rationale and the explicit forbidden-vs-required phrasings.
- F23-F26 are tagged epistemic but in v6 **become fixed within each
  policy scenario** (CA-Committed / CA-Aggressive / CA-Delayed; OH analogs).
  Only F27 (hardware doubling), F29 (gasoline price), F30 (deployment lag),
  and F31 (fleet growth envelope) remain sampled within every scenario as
  exogenous epistemic factors.
- F29, F30, F31 are introduced in v6. They are tracked in the per-run
  bundle extras CSVs (`results/<region>__policy-<sid>__v6_extras.csv`)
  and surfaced in the Sobol view (page 03).
- F29 (gasoline price multiplier) and F30 (deployment lag) are recorded
  per run but **not yet wired into the simulator equations** in this
  release; they appear in the registry and extras for future paper-grade
  rewiring. F27 and F31 *are* wired and contribute to the bundle outputs.
    """
)
