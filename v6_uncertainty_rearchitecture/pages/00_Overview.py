"""Page 00 — Overview: taxonomy, interpretation discipline, what-this-band-is-not."""
from __future__ import annotations

import os
import sys

import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_V6_ROOT = os.path.dirname(_HERE)
_REPO_ROOT = os.path.dirname(_V6_ROOT)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from v6_uncertainty_rearchitecture import uncertainty_taxonomy as utax  # noqa: E402

st.set_page_config(page_title="v6 · Overview", layout="wide")

st.title("00 · Taxonomy & Interpretation Discipline")

st.markdown(
    """
This page names every uncertainty object in v6 and states what it is, what it is
not, and when to use it.
    """
)

st.subheader("The four uncertainty categories")
st.markdown(
    """
| Category | Meaning | Treatment | Paper-facing |
| --- | --- | --- | --- |
| **Scenario** | Analyst-chosen pathway family. Not probabilized unless declared. | Select one; re-run pipeline per choice. | Yes. |
| **Epistemic** | Incomplete knowledge of parameters. Frozen per outer draw. | Outer MC loop. | Yes. |
| **Aleatoric** | Irreducible year-to-year variation within a world. | Inner MC loop. | Exploratory. |
| **Structural shock** | Discrete labelled regime break. | Separate named runs. | Yes. |
    """
)

with st.expander("Show current v6 epistemic parameter list (outer loop)"):
    ep = utax.epistemic_paths()
    st.write(f"**{len(ep)} parameters** routed to outer loop:")
    for p in ep:
        st.markdown(f"- `{p}`")

with st.expander("Show current v6 aleatoric parameter list (inner loop)"):
    al = utax.aleatoric_paths()
    st.write(f"**{len(al)} parameters** routed to inner loop:")
    for p in al:
        st.markdown(f"- `{p}`")

st.subheader("What each uncertainty object is / is not")
st.markdown(
    """
| View | Is | Is not |
| --- | --- | --- |
| Deterministic reference | Central trajectory under median inputs. | A forecast. The median of the MC distribution. |
| Within-scenario band | Quantile interval conditional on one scenario. | Total uncertainty. A probabilistic interval unless aleatoric-only. |
| Scenario envelope | Spread across outer epistemic draws / named scenarios. | A confidence interval unless outer draws are probabilized. |
| Benchmark-year distribution | Marginal at a named year. | A time-evolution claim. |
| Sensitivity ranking | Which driver matters for the variance. | How big the uncertainty is. |
| Structural-shock comparison | Discrete named simulations side by side. | Ensemble. Probabilistic. |
| Relative uncertainty | Band width relative to median. | Absolute band width. |
    """
)

st.subheader("Interpretation discipline across horizons")
st.markdown(
    """
| Horizon | Paper allowed to say | Paper NOT allowed to say |
| --- | --- | --- |
| 2024 → interpretation-boundary year (τ=1.5) | "Under scenario X, annual emissions in year Y fall within [p05, p95] with median p50." | "The model predicts annual emissions of p50 in year Y." |
| Interpretation-boundary year → 2092 | "Under scenario X with pathway A, annual emissions evolve along the envelope {…}." Benchmark-year marginals may be reported. | "The forecast for year Y is p50." "Uncertainty has narrowed." |

If late-horizon absolute bands narrow, the figure / paragraph must state the
cause (bounded state, saturation, approach to zero) and reference the
relative-uncertainty view.
    """
)

st.info(
    "Pages 01-07 each carry a one-line subtitle stating which uncertainty category "
    "the view belongs to and what must not be inferred from it."
)
