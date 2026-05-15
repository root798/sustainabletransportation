"""Uncertainty Analysis — Monte Carlo quantile details."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (
    REGION_LABELS, REGION_ORDER, POLICY_LABELS, POLICY_ORDER,
    available_policies, load_quantiles, mc_sample_count,
    band_metadata, interpretation_boundary, scale, rgba,
    quantile_path, load_runtime_config, controls_from_config,
    apply_controls, run_simulation, DEFAULT_HORIZON, fmt_emissions,
    load_saturation_metadata, region_paper_safety,
)

st.set_page_config(page_title="Uncertainty Analysis", page_icon="C", layout="wide")
st.title("Uncertainty Analysis")
st.caption(
    "Monte Carlo parameter sampling produces p05/p50/p95 quantile bands. "
    "Only baseline policies have precomputed MC support. "
    "Bands are **scenario-conditioned ranges**, not forecast confidence intervals. "
    "Post-boundary years are scenario envelopes, not point projections."
)
st.warning(
    "\u26a0\ufe0f **Paper-safe MC scope = baseline only** (see METHODS_ALIGNMENT §M14). "
    "Policy patches (`aggressive` / `conservative`) deep-merge over deterministic means "
    "but do **not** re-centre the underlying `data_uncertainty` distributions, so any MC band "
    "computed under a non-baseline policy is scientifically inconsistent with its deterministic "
    "trajectory. Aggressive / conservative MC quantile files (if present) are exploratory only "
    "and must NOT be cited in paper figures, captions, or main-text claims. "
    "Aggressive / conservative policies may still be discussed via their deterministic paths."
)

# --- Support matrix ---
st.subheader("Quantile support matrix")
rows = []
for r in REGION_ORDER:
    for p in POLICY_ORDER:
        qp = quantile_path(r, p)
        exists = qp.exists()
        qf = load_quantiles(r, p) if exists else None
        bm = band_metadata(qf, "ATS Emissions (kg CO2)")
        sc = mc_sample_count(r, p)
        ib = interpretation_boundary(qf)
        safety = region_paper_safety(r)
        # Paper-safe MC requires both the region to be paper-safe AND the policy
        # to be baseline (see METHODS_ALIGNMENT §M14 on baseline-only MC scope).
        region_safe = safety.get("paper_safe", True)
        if not region_safe:
            paper_safe_label = "QUARANTINED (region)"
        elif p != "baseline":
            paper_safe_label = "Exploratory (not paper-safe: non-baseline MC)"
        else:
            paper_safe_label = "Yes"
        rows.append({
            "Region": REGION_LABELS[r],
            "Policy": POLICY_LABELS.get(p, p),
            "Quantile file": "Yes" if exists else "No",
            "Band non-zero": "Yes" if bm["available"] and not bm["degenerate"] else "No",
            "MC runs": sc or "\u2014",
            "Interp. boundary": ib.get("year") or "\u2014",
            "Paper-safe": paper_safe_label,
        })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# --- Detailed view ---
st.subheader("Detailed uncertainty view")
region = st.selectbox("Region", REGION_ORDER, format_func=lambda r: REGION_LABELS[r])

# Paper-safety banner for the selected region
_safety = region_paper_safety(region)
if not _safety.get("paper_safe", True):
    st.error(f"\u26a0\ufe0f {_safety.get('note', '')}")

qf = load_quantiles(region, "baseline")

if qf is None:
    st.warning(f"No quantile file found for {REGION_LABELS[region]} baseline.")
    st.stop()

bm_e = band_metadata(qf, "ATS Total Power (kWh)")
bm_em = band_metadata(qf, "ATS Emissions (kg CO2)")
ib = interpretation_boundary(qf)
sc = mc_sample_count(region, "baseline")
sat_meta = load_saturation_metadata(region, "baseline")

st.info(f"MC sample count: **{sc or '?'}**. Interpretation boundary: **{ib.get('year') or 'none'}**. "
        f"Boundary reason: {ib.get('reason', '')}")

# Deterministic median for overlay
cfg = load_runtime_config(region, "baseline")
cv = controls_from_config(cfg, region, "baseline")
df = run_simulation(apply_controls(cfg, cv), DEFAULT_HORIZON)
horizon_end = int(df["Year"].max()) if not df.empty else None


def _apply_boundary_and_saturation(fig, qf, metric_base):
    """Draw interpretation-boundary line, post-boundary shading, and saturation marker."""
    bnd_yr = ib.get("year")
    if bnd_yr:
        fig.add_vline(x=bnd_yr, line_dash="dot", line_color="red", line_width=2,
                      annotation_text="Interpretation\nboundary",
                      annotation_position="top left",
                      annotation_font_color="red", annotation_font_size=10)
        if horizon_end and horizon_end > bnd_yr:
            fig.add_vrect(
                x0=bnd_yr, x1=horizon_end,
                fillcolor="red", opacity=0.06, line_width=0,
                annotation_text="Scenario envelope (post-boundary)",
                annotation_position="top right",
                annotation_font_size=9, annotation_font_color="red",
            )
    # Saturation overlay on this specific metric
    fields = (sat_meta or {}).get("fields") or {}
    entry = fields.get(metric_base)
    if entry and entry.get("first_saturation_year"):
        sy = entry["first_saturation_year"]
        fig.add_vline(x=sy, line_dash="dash", line_color="#8c564b", line_width=1.5,
                      annotation_text=f"Saturation {sy}\n(cap artefact)",
                      annotation_position="bottom right",
                      annotation_font_color="#8c564b", annotation_font_size=9)


c1, c2 = st.columns(2)
with c1:
    fig = go.Figure()
    if bm_e["available"] and not bm_e["degenerate"]:
        s05, eu, fac = scale(qf["ATS Total Power (kWh)_p05"], "energy")
        s95 = qf["ATS Total Power (kWh)_p95"] / fac
        s50 = qf["ATS Total Power (kWh)_p50"] / fac
        fig.add_trace(go.Scatter(
            x=list(qf.index) + list(qf.index[::-1]),
            y=list(s05) + list(s95[::-1]),
            fill="toself", fillcolor=rgba("#636EFA", 0.2), line=dict(width=0),
            name="p05\u2013p95", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=qf.index, y=s50, mode="lines",
                                 name="p50 (median)", line=dict(color="#636EFA", width=2)))
    _apply_boundary_and_saturation(fig, qf, "ATS Total Power (kWh)")
    fig.update_layout(title="ATS energy demand \u2014 uncertainty", xaxis_title="Year",
                      yaxis_title=eu if bm_e["available"] else "kWh/yr", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig2 = go.Figure()
    if bm_em["available"] and not bm_em["degenerate"]:
        s05, emu, fac = scale(qf["ATS Emissions (kg CO2)_p05"], "emissions")
        s95 = qf["ATS Emissions (kg CO2)_p95"] / fac
        s50 = qf["ATS Emissions (kg CO2)_p50"] / fac
        fig2.add_trace(go.Scatter(
            x=list(qf.index) + list(qf.index[::-1]),
            y=list(s05) + list(s95[::-1]),
            fill="toself", fillcolor=rgba("#EF553B", 0.2), line=dict(width=0),
            name="p05\u2013p95", hoverinfo="skip"))
        fig2.add_trace(go.Scatter(x=qf.index, y=s50, mode="lines",
                                  name="p50 (median)", line=dict(color="#EF553B", width=2)))
    _apply_boundary_and_saturation(fig2, qf, "ATS Emissions (kg CO2)")
    fig2.update_layout(title="ATS emissions \u2014 uncertainty", xaxis_title="Year",
                       yaxis_title=emu if bm_em["available"] else "kg CO\u2082/yr",
                       hovermode="x unified")
    st.plotly_chart(fig2, use_container_width=True)

# Saturation summary for the selected region
st.subheader("Saturation diagnostics")
if sat_meta.get("missing"):
    st.warning(
        "Saturation-metadata sidecar not found for this scenario. "
        "Post-saturation band-collapse annotations will be absent. "
        f"Run `python footprint_model.py --scenarios {region} --policy baseline --mc 200 --seed 42` to regenerate."
    )
else:
    rows = []
    for field, entry in (sat_meta.get("fields") or {}).items():
        rows.append({
            "Field": field,
            "First saturation year": entry.get("first_saturation_year") or "\u2014 no saturation detected",
            "Reason": entry.get("reason", ""),
            "Max band width (abs)": f"{entry.get('max_width', 0.0):.3g}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "**Cap-artefact caveat**: a non-null `first saturation year` means every MC sample has hit a modelling "
        "cap (1.0 for fractions). The post-saturation band collapses to zero width because of the cap, NOT "
        "because uncertainty has been reduced. Do not cite post-saturation narrow bands as evidence of "
        "predictability."
    )

st.subheader("Sampled parameters")
st.markdown("""
The following parameters are sampled in Monte Carlo runs (defined in `data_uncertainty`
sections of each scenario file):

| Parameter | Distribution | Section |
|-----------|-------------|---------|
| f_clean (initial) | Beta | initial_data |
| ev_share (initial) | Beta | initial_data |
| cav 2075 target fraction | Triangular | growth_rates |
| sti 2075 target fraction | Triangular | growth_rates |
| ev growth rate (annual) | Normal (clipped) | growth_rates |
| clean_energy growth (annual) | Normal (clipped) | growth_rates |
| efficiency doubling time | Triangular | growth_rates |
| fleet growth (annual) | Normal (clipped) | growth_rates |
| retire_year | Integer triangular | growth_rates |
| icecav_power_factor | Triangular | consumption_rates |
| cohort_decay_factor | Triangular | consumption_rates |
| cav_levels (L3/L4/L5 mix) | Dirichlet | consumption_rates |
| sti_levels (Basic/Semi/Highly mix) | Dirichlet | consumption_rates |
| ecav_scale_factors (per-level \u00d7 per-subsystem) | Lognormal \u00d7 Lognormal | consumption_rates |
| sti_scale_factors (per-level \u00d7 per-subsystem) | Lognormal \u00d7 Lognormal | consumption_rates |
| e_clean | Triangular | emission_factors |
| e_fossil | Triangular | emission_factors |
| e_gasoline | Triangular | emission_factors |

Parameters **not** sampled (structural choices, treated as labelled scenarios): adoption-curve form,
efficiency-curve form, efficiency-model mode, energy-model type, efficiency-applied-to-subsystems.
""")

st.caption(
    "**Provenance**: quantile bands are derived from 200 MC simulation runs. "
    "Each run samples from the distributions above and executes a full TransportModel simulation. "
    "Post-boundary values are scenario envelopes, not point projections."
)
