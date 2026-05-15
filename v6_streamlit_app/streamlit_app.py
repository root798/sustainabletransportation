"""CLEAR-ATS v6 dashboard — landing page.

v6 inherits v5 simulator and visual language. Adds: epistemic / aleatoric
terminology overlay; six discrete policy scenarios (3 CA + 3 OH) replacing
v5 continuous F23-F27 sampling; three new visualization pages (Sobol Fig.5,
Distribution Overlay Fig.4, Avoided vs Residual Fig.3) inspired by
Khayambashi et al. 2025; always-visible factor legend in the sidebar.

v5 dashboard at v5_streamlit_app/ remains untouched and runnable.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from sidebar_legend import render_sidebar_legend  # noqa: E402

st.set_page_config(
    page_title="CLEAR-ATS v6",
    page_icon="C",
    layout="wide",
)

render_sidebar_legend()

st.title("CLEAR-ATS: Clean Energy Automated Road Transport System")
st.caption(
    "Dashboard v6. Inherits v5 simulator, palette, and pages. Adds policy-"
    "scenario architecture, three Khayambashi-2025-inspired visualizations, "
    "and aleatoric / epistemic terminology overlay. v5 remains runnable at "
    "`v5_streamlit_app/streamlit_app.py`."
)

st.markdown(
    """
This dashboard projects the **utility-phase** annual energy demand and
CO\u2082 emissions of Connected Autonomous Vehicles (CAV), Smart Traffic
Infrastructure (STI), and their integrated Automated Transport System (ATS)
for California and Ohio from 2024 onward.

### Pages

| Page | Purpose |
|------|---------|
| **Scenario Explorer** | Primary interactive page — v5 four-block layout preserved exactly. v6 additions: a **policy-scenario picker** at the top of Block 1 (CA-Committed / CA-Aggressive / CA-Delayed; OH-Status-Quo / OH-IRA-Accelerated / OH-Stalled) that snaps F23-F27 sliders to legislated targets. |
| **One-Time Energy** | Production + logistics phase. Inherited from v5; adds the v6 sidebar legend. |
| **System Boundary** | Scope disclosure. Inherited from v5; adds the v6 sidebar legend. |
| **Sobol Sensitivity Analysis** *(v6)* | Total-order Sobol indices via SALib (or RF importance fallback). Inspired by Khayambashi et al. 2025 Fig. 5. |
| **Distribution Overlay** *(v6)* | KDE / violin distributions across multiple policy scenarios for the same target. Inspired by Khayambashi et al. 2025 Fig. 4. |
| **Avoided vs Residual** *(v6)* | Stacked subsystem emissions + residual / avoided companion bar relative to a reference scenario. Inspired by Khayambashi et al. 2025 Fig. 3. |
| **Factor Legend** *(v6)* | Full F-number glossary with class (aleatoric / epistemic), layer (L1 / L2 / L3), and the why-this-class explanation. Includes v6 introductions F29 / F30 / F31. |

### v6 architecture in brief

- **Aleatoric vs epistemic terminology overlay.** L1 + L2 are aleatoric (bounded measurement / vendor variance, do not compound with time). L3 is epistemic (knowledge-incompleteness; compounds). v6 adds this as an honest mapping in `configs/parameter_labels.json::metadata`. v5 calculations and palette unchanged.
- **Six discrete policy scenarios** in `configs/policy_scenarios.json`. Each fixes F23-F26 to legislated / documented values; F27 (hardware doubling) remains the genuinely exogenous epistemic factor sampled within every scenario, alongside v6 introductions F29 / F30 / F31.
- **Six v6 committed bundles** under `results/<region>__policy-<sid>__v6_*.csv` (80 MC samples each; v5 bundles untouched).
- **Always-visible sidebar legend** populated from `configs/parameter_labels.json::metadata` so readers never need to flip back to Block 4 to recall what F10 means.

### Reproducibility

v6 reuses the v5 simulator (`footprint_model.py`) bit-exact. Bundle regeneration:

```bash
python v6_streamlit_app/scripts/build_v6_bundles.py --n-runs 80
```

For a paper-grade Sobol on a chosen target:

```bash
streamlit run v6_streamlit_app/streamlit_app.py
# → Sobol Sensitivity Analysis page → set N base = 1024 or 2048 → Recompute
```

### v5 stays untouched

- `v5_streamlit_app/` — unchanged. Launch with `streamlit run v5_streamlit_app/streamlit_app.py`.
- v5 committed bundles in `results/` — unchanged.
- `footprint_model.py` simulator — unchanged.
"""
)

st.caption(
    "See `reports/summaries/V6_CONSTRUCTION_STATUS.md` for what changed and "
    "`audits/v6/V6_VALIDATION.md` for the assertion pass/fail. Reviewer "
    "pre-mortem: `reports/V6_REVIEWER_PREMORTEM.md`."
)
