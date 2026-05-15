"""v6 dashboard entry point.

This is the landing page. It does NOT show a default band — the reader must
choose which uncertainty object to see. Every page on the sidebar reports
exactly which uncertainty layers it is displaying.
"""
from __future__ import annotations

import os
import sys

import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


st.set_page_config(
    page_title="CLEAR-ATS v6 — Layered Uncertainty Architecture",
    layout="wide",
)

st.title("CLEAR-ATS v6 — Layered Uncertainty Architecture")
st.caption(
    "Non-destructive upgrade to v5. Inspired by the 2025 Nature Communications Puerto Rico "
    "energy-transition paper. v3, v4, v5 remain runnable and unchanged."
)

st.markdown(
    """
## What this dashboard is

v6 re-frames CLEAR-ATS uncertainty into **four explicit layers** and presents each as
its own object with a named interpretation. The default view is intentionally
**not** a single long-horizon band. You must pick which object you want to see.

### The four layers

| Layer | Meaning | Where it lives |
| --- | --- | --- |
| **Scenario** | Externally specified pathway family (policy / shock). Analyst picks one. Not probabilized. | Page 06 (Structural Shocks). Policy selection on every other page. |
| **Epistemic** | Incomplete knowledge about parameters that would not vary year-to-year within a pathway. Outer MC loop. | Pages 03 (Envelope), 04 (Benchmark Year), 05 (Sensitivity), 07 (Relative). |
| **Aleatoric** | Irreducible short-horizon variation conditional on an outer world. Inner MC loop. | Page 02 (Within-Scenario Band). |
| **Structural shock** | Discrete, labelled regime break. Not probabilized. | Page 06. |

### What each page does

- **01 · Deterministic Reference Path** — Stage 1 central trajectory under median inputs. Not a forecast; not the median of the MC distribution.
- **02 · Within-Scenario Conditional Band** — Inner-loop spread at a chosen outer epistemic world. Conditional. Lower bound to total uncertainty.
- **03 · Scenario Envelope** — Spread across outer epistemic draws. Answers *what if the world is different*.
- **04 · Benchmark-Year Distributions** — Conditional marginal at 2030, 2035, 2045, 2055, 2075. Histogram + violin. Not a time-evolution claim.
- **05 · Sensitivity Analysis** — Total-order Sobol / surrogate-importance rankings. Answers *which driver controls each output*.
- **06 · Structural Shocks** — Deterministic baseline vs five labelled shocks. Discrete comparison, not ensemble.
- **07 · Relative Uncertainty** — (p95 − p05)/|p50| and p95/p50 alongside absolute band. Prevents "band narrows therefore prediction improves" misreading.

### How to generate the data

```bash
python v6_uncertainty_rearchitecture/scripts/run_nested_mc.py \\
    --regions california ohio --policy baseline \\
    --n-outer 40 --n-inner 20 --years 68 --seed 42
python v6_uncertainty_rearchitecture/scripts/run_sensitivity.py --regions california ohio
```

Outputs land in `v6_uncertainty_rearchitecture/results/`.
Scale up to `n_outer = 200, n_inner = 20` for manuscript-grade.
    """
)

st.info(
    "The sidebar holds the seven uncertainty-object pages. Pick one to inspect. "
    "Every page names its category and states what the reader must not infer."
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("v6 version", "6.0.0-demo")
with col2:
    st.metric("Regions", "CA, OH")
with col3:
    st.metric("Default n_outer × n_inner", "40 × 20")

st.caption(
    "See `reports/UNCERTAINTY_ARCHITECTURE_VNEXT.md` for the methods memo and "
    "`reports/OLD_VS_NEW_UNCERTAINTY_OBJECTS.md` for the v5→v6 comparison."
)
