"""
Page 05 — Uncertainty Analysis

Explains the 3-layer uncertainty framework, shows uncertainty band widths,
compares DU-REGIONMEAN vs DU-INJECTED variants, and provides honest
statement about what the Monte Carlo does and does NOT cover.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from data_contracts.load_results import load_quantile_csv, load_uncertainty_inputs, DATA_ROOT
from data_contracts.provenance import render_provenance_tag

st.set_page_config(
    page_title="Uncertainty Analysis — CLEAR-ATS v2",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_p(df, base, suffix):
    col = f"{base}_{suffix}"
    return df[col] if df is not None and col in df.columns else None


# ---------------------------------------------------------------------------
# Page title
# ---------------------------------------------------------------------------

st.title("Uncertainty Analysis")
st.markdown(
    """
This page documents what is uncertain in the model, how that uncertainty is quantified,
and what the Monte Carlo simulation does and does **not** cover.
"""
)

st.error(
    "**Important caveat:** Monte Carlo sampling in this model covers **parameter uncertainty** "
    "within a fixed model structure. Structural model uncertainty — such as alternative "
    "adoption curve shapes, different vehicle retirement models, or alternative subsystem "
    "energy architectures — is **NOT included** in the uncertainty bands shown here. "
    "The p05–p95 bands represent parametric uncertainty only."
)

# ---------------------------------------------------------------------------
# Section 1 — 3-Layer Framework
# ---------------------------------------------------------------------------

st.header("1. Three-Layer Uncertainty Framework")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Layer 1: Data Uncertainty")
    st.markdown(
        """
**What:** Uncertainty in measured or reported input data.

**Parameters:**
- Grid emission factors (e_clean, e_fossil, e_gasoline)
- Initial EV fleet share (ev_share)
- Initial grid cleanliness (f_clean)
- Total cars (total_cars)
- Total intersections (total_intersections)

**Distribution types:** Lognormal (emission factors), Beta (fractions), Truncated-Normal (counts)

**Confidence:** Medium — based on published values with known reporting variability.
"""
    )

with col2:
    st.subheader("Layer 2: Model Uncertainty")
    st.markdown(
        """
**What:** Uncertainty in per-unit consumption rates used in the simulation model.

**Parameters:**
- ECAV power rates per subsystem per autonomy level (L3/L4/L5)
- ICECAV power factor vs ECAV (fixed at 1.6 in deterministic run)
- STI power rates per subsystem per deployment tier (Basic/Semi/Highly)

**Distribution types:** Lognormal (CV=0.1 for all consumption rates)

**Confidence:** Medium — derived from published AV hardware benchmarks (2019–2023).
"""
    )

with col3:
    st.subheader("Layer 3: Scenario Uncertainty")
    st.markdown(
        """
**What:** Uncertainty in future growth rates and policy trajectories.

**Parameters:**
- EV adoption growth rate (ev)
- Clean energy growth rate (clean_energy)
- Hardware efficiency doubling time (efficiency_doubling)
- Total vehicle fleet growth (total_car_increase)

**Distribution types:** Lognormal (σ=0.2–0.4)

**Confidence:** Low — future rates are inherently uncertain; distributions are expert-informed.
"""
    )

# ---------------------------------------------------------------------------
# Section 2 — Uncertainty parameter table
# ---------------------------------------------------------------------------

st.header("2. Uncertainty Parameter Table")

df_unc = load_uncertainty_inputs()

if df_unc is not None:
    # Split by layer
    for layer in ["L1", "L2", "L3"]:
        layer_names = {"L1": "Layer 1 — Data Uncertainty", "L2": "Layer 2 — Model Uncertainty",
                       "L3": "Layer 3 — Scenario Uncertainty"}
        layer_df = df_unc[df_unc["Layer"] == layer].copy()
        if layer_df.empty:
            continue
        with st.expander(f"{layer_names[layer]} ({len(layer_df)} parameters)", expanded=(layer == "L1")):
            st.dataframe(layer_df.reset_index(drop=True), use_container_width=True)

    st.caption(
        f"Source: {DATA_ROOT / 'results_notebook' / 'uncertainty_inputs_table.csv'} | "
        "Tier 3 — Parameter distributions are expert/literature-informed, not empirically calibrated."
    )
else:
    st.warning(
        f"uncertainty_inputs_table.csv not found at "
        f"{DATA_ROOT / 'results_notebook' / 'uncertainty_inputs_table.csv'}"
    )

# ---------------------------------------------------------------------------
# Section 3 — Uncertainty bands over time (CA baseline)
# ---------------------------------------------------------------------------

st.header("3. Uncertainty Bands Over Time — California Baseline")

df_ca = load_quantile_csv("california", "baseline")

if df_ca is None:
    st.warning("California baseline data not available.")
else:
    years = df_ca.index.astype(int)

    ats_p50 = get_p(df_ca, "ATS Emissions (kg CO2)", "p50")
    ats_p05 = get_p(df_ca, "ATS Emissions (kg CO2)", "p05")
    ats_p95 = get_p(df_ca, "ATS Emissions (kg CO2)", "p95")

    if ats_p50 is not None and ats_p05 is not None and ats_p95 is not None:
        max_v = ats_p95.max()
        if max_v >= 1e9:
            sc, em_unit = 1e9, "Mt CO\u2082"
        elif max_v >= 1e6:
            sc, em_unit = 1e6, "kt CO\u2082"
        else:
            sc, em_unit = 1.0, "kg CO\u2082"

        fig_bands = go.Figure()

        # p05-p95 shaded band
        fig_bands.add_trace(
            go.Scatter(
                x=list(years) + list(years[::-1]),
                y=list(ats_p05 / sc) + list(ats_p95[::-1] / sc),
                fill="toself",
                fillcolor="rgba(52, 152, 219, 0.15)",
                line=dict(width=0),
                name="p05–p95 band (90% MC interval)",
                hoverinfo="skip",
            )
        )

        fig_bands.add_trace(
            go.Scatter(
                x=years, y=ats_p05 / sc,
                mode="lines",
                name="p05 (5th percentile)",
                line=dict(color="#3498db", width=1, dash="dot"),
            )
        )
        fig_bands.add_trace(
            go.Scatter(
                x=years, y=ats_p95 / sc,
                mode="lines",
                name="p95 (95th percentile)",
                line=dict(color="#3498db", width=1, dash="dot"),
            )
        )
        fig_bands.add_trace(
            go.Scatter(
                x=years, y=ats_p50 / sc,
                mode="lines",
                name="p50 (median)",
                line=dict(color="#e74c3c", width=2),
            )
        )

        fig_bands.update_layout(
            title="ATS Emissions Uncertainty Bands — California Baseline",
            xaxis_title="Year",
            yaxis_title=f"Annual CO\u2082 Emissions ({em_unit})",
            hovermode="x unified",
            template="plotly_dark",
            legend=dict(orientation="h", y=-0.15),
        )

        st.plotly_chart(fig_bands, use_container_width=True)
        st.caption(render_provenance_tag("ATS Emissions"))

    # --- Band width as fraction of median ---
    st.subheader("Relative Uncertainty Band Width")
    st.markdown(
        "Band width = (p95 - p05) / p50. Shows how the relative uncertainty "
        "grows or shrinks over the simulation horizon."
    )

    if ats_p50 is not None and ats_p05 is not None and ats_p95 is not None:
        band_width = (ats_p95 - ats_p05) / ats_p50.replace(0, float("nan"))

        fig_bw = go.Figure()
        fig_bw.add_trace(
            go.Scatter(
                x=years,
                y=band_width,
                mode="lines",
                name="(p95 - p05) / p50",
                line=dict(color="#f39c12", width=2),
                fill="tozeroy",
                fillcolor="rgba(243, 156, 18, 0.1)",
            )
        )

        fig_bw.update_layout(
            title="Relative Uncertainty Band Width — ATS Emissions",
            xaxis_title="Year",
            yaxis_title="(p95 - p05) / p50 (relative width)",
            hovermode="x unified",
            template="plotly_dark",
        )

        st.plotly_chart(fig_bw, use_container_width=True)
        st.caption(
            "Tier 1 — Derived from Monte Carlo quantiles | "
            "Widening band = compounding uncertainty from L3 growth rates. "
            "Peak relative uncertainty typically occurs near or after peak emissions."
        )

# ---------------------------------------------------------------------------
# Section 4 — DU-REGIONMEAN vs DU-INJECTED comparison
# ---------------------------------------------------------------------------

st.header("4. Uncertainty Variant Comparison: DU-REGIONMEAN vs DU-INJECTED")

st.markdown(
    """
Two variants of uncertainty injection were run for the California baseline:

- **DU-REGIONMEAN**: Uncertainty parameters sampled as region-level means
  (all vehicles in a region share the same sampled parameter value).
- **DU-INJECTED**: Uncertainty parameters injected at the individual-run level
  (each Monte Carlo run uses an independently sampled parameter set).

The comparison shows whether correlating parameters across units inflates or
deflates apparent uncertainty.
"""
)

df_rm = load_quantile_csv("california", "baseline", "DU-REGIONMEAN")
df_inj = load_quantile_csv("california", "baseline", "DU-INJECTED")
df_base = load_quantile_csv("california", "baseline")

variants_available = []
if df_base is not None:
    variants_available.append(("Default (full MC)", df_base, "#3498db"))
if df_rm is not None:
    variants_available.append(("DU-REGIONMEAN", df_rm, "#2ecc71"))
if df_inj is not None:
    variants_available.append(("DU-INJECTED", df_inj, "#e67e22"))

if len(variants_available) < 2:
    st.info(
        "Only one or zero uncertainty variants are available on disk. "
        "DU-REGIONMEAN and DU-INJECTED variants would appear here if present in "
        f"{DATA_ROOT / 'results_notebook'}"
    )
else:
    fig_var = go.Figure()

    for var_label, df_v, colour in variants_available:
        years_v = df_v.index.astype(int)
        p50_v = get_p(df_v, "ATS Emissions (kg CO2)", "p50")
        p05_v = get_p(df_v, "ATS Emissions (kg CO2)", "p05")
        p95_v = get_p(df_v, "ATS Emissions (kg CO2)", "p95")

        if p50_v is None:
            continue

        max_v = p50_v.max()
        sc_v = 1e9 if max_v >= 1e9 else 1e6 if max_v >= 1e6 else 1.0
        v_unit = "Mt CO\u2082" if sc_v == 1e9 else "kt CO\u2082" if sc_v == 1e6 else "kg CO\u2082"

        if p05_v is not None and p95_v is not None:
            fig_var.add_trace(
                go.Scatter(
                    x=list(years_v) + list(years_v[::-1]),
                    y=list(p05_v / sc_v) + list(p95_v[::-1] / sc_v),
                    fill="toself",
                    line=dict(width=0),
                    showlegend=False,
                    opacity=0.12,
                    hoverinfo="skip",
                )
            )

        fig_var.add_trace(
            go.Scatter(
                x=years_v,
                y=p50_v / sc_v,
                mode="lines",
                name=f"{var_label} (p50)",
                line=dict(color=colour, width=2),
            )
        )

    fig_var.update_layout(
        title="Uncertainty Variant Comparison — California Baseline ATS Emissions",
        xaxis_title="Year",
        yaxis_title=f"Annual CO\u2082 Emissions ({v_unit})",
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.15),
    )

    st.plotly_chart(fig_var, use_container_width=True)
    st.caption(
        "Tier 1 — Direct simulation output. "
        "Differences between variants reveal the impact of spatial correlation "
        "structure in uncertainty parameters."
    )

# ---------------------------------------------------------------------------
# Section 5 — What MC does NOT cover
# ---------------------------------------------------------------------------

st.header("5. What the Monte Carlo Does NOT Cover")

st.markdown(
    """
The Monte Carlo sampling in CLEAR-ATS quantifies **parametric uncertainty** within a
fixed model structure. The following sources of uncertainty are explicitly NOT captured:

| Source of Uncertainty | Status | Notes |
|----------------------|--------|-------|
| Parameter uncertainty in L1/L2/L3 | **Included** | Sampled distributions per run |
| Correlation structure between parameters | Partial | Within-layer only |
| Alternative adoption curve shapes | **NOT included** | Only logistic growth modeled |
| Different vehicle retirement models | **NOT included** | Fixed 12-year cycle assumed |
| Alternative subsystem energy architectures | **NOT included** | Fixed sensing/computing/comm split |
| Market equilibrium or demand response | **NOT included** | No feedback loops |
| Policy implementation uncertainty | Partial | Only via L3 growth rate distribution |
| Technology disruption scenarios | **NOT included** | No discontinuous change modeled |
| End-of-life / manufacturing emissions | **NOT included** | Utility phase only |
| Spatial variation within a region | **NOT included** | Single region-level simulation |

**Bottom line:** The p05–p95 bands shown in this app represent a **lower bound** on
true uncertainty. Structural uncertainty and scope uncertainty are not quantified.
"""
)

st.divider()
st.caption(
    "CLEAR-ATS v2 | Uncertainty Analysis | "
    "Monte Carlo with 3 epistemic layers. Parameter uncertainty only. "
    "Structural model uncertainty is not quantified."
)
