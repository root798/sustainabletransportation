"""Panel 2 — Accumulative Energy Cost (utility phase).

Consolidates Scenario Explorer + Utility Phase Analysis + State Results +
Turning Points + Uncertainty Analysis + Data & Provenance footer into one
panel with a preset-driven uncertainty selector. See
`audits/uncertainty_governance/PANEL_REORGANIZATION_PLAN.md`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (  # noqa: E402
    BASE_YEAR, DEFAULT_HORIZON, POLICY_LABELS, POLICY_ORDER, REGION_LABELS,
    REGION_ORDER, REGION_NOTES, UNCERTAINTY_PRESETS,
    apply_controls, apply_uncertainty_preset, available_policies,
    band_metadata, compute_turning_metrics, controls_from_config,
    fmt_count, fmt_emissions, fmt_energy, label,
    load_quantiles, load_runtime_config, load_saturation_metadata,
    load_uncertainty_preset, mc_sample_count, quantile_path,
    region_paper_safety, rgba, run_simulation, runtime_diagnostics, scale,
)

st.set_page_config(page_title="Panel 2 — Accumulative Energy Cost", page_icon="C", layout="wide")
st.title("Panel 2 — Accumulative Energy Cost")
st.caption(
    "Utility-phase annual energy and CO\u2082 emissions, with preset-driven "
    "Monte-Carlo bands. Central trajectories are live deterministic; bands are "
    "the baseline MC p05\u2013p95 on the ATS total."
)

# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
sb = st.sidebar
sb.title("Panel 2 controls")

show_quarantined = sb.toggle("Show quarantined regions", value=False,
                             help="U.S. Average is quarantined from paper-facing quantitative use; "
                                  "enable only for exploratory review.")
visible_regions = [r for r in REGION_ORDER if (show_quarantined or region_paper_safety(r).get("paper_safe", True))]
region = sb.selectbox("Region", visible_regions, format_func=lambda r: REGION_LABELS[r])

preset_name = sb.selectbox(
    "Uncertainty preset",
    list(UNCERTAINTY_PRESETS),
    index=list(UNCERTAINTY_PRESETS).index("medium"),
    format_func=lambda p: {"low": "Low (evidence-anchored)",
                            "medium": "Medium (paper-safe)",
                            "high": "High (exploratory)"}.get(p, p),
)
preset_obj = load_uncertainty_preset(preset_name, region)

policies = available_policies(region)
policy = sb.selectbox("Policy", policies, format_func=lambda p: POLICY_LABELS.get(p, p))

horizon = sb.slider("Simulation horizon (years from 2024)",
                    min_value=10, max_value=120, value=DEFAULT_HORIZON, step=1)

# ----------------------------------------------------------------------
# Preset banner
# ----------------------------------------------------------------------
if not preset_obj["paper_safe"]:
    st.warning(
        f"\u26a0\ufe0f **Preset: {preset_obj['label']}** \u2014 exploratory; "
        "not paper-safe for headline figure bands. Deterministic central "
        "trajectories are unchanged across presets (see Methods M14)."
    )
else:
    st.success(
        f"Preset: **{preset_obj['label']}** \u2014 paper-safe. Deterministic "
        "central trajectories are preset-invariant; only prior widths change."
    )

safety = region_paper_safety(region)
if not safety.get("paper_safe", True):
    st.error(f"\u26a0\ufe0f {safety.get('note', '')}")

# ----------------------------------------------------------------------
# Live deterministic simulation at baseline controls
# ----------------------------------------------------------------------
cfg = load_runtime_config(region, policy)
cv = controls_from_config(cfg, region, policy)
runtime_cfg = apply_controls(cfg, cv)
runtime_cfg = apply_uncertainty_preset(runtime_cfg, preset_name, region)
df = run_simulation(runtime_cfg, horizon)

df["Cumulative Energy (kWh)"] = df["ATS Total Power (kWh)"].cumsum()
df["Cumulative Emissions (kg CO2)"] = df["ATS Emissions (kg CO2)"].cumsum()

turning = compute_turning_metrics(df)
_horizon_end = int(df["Year"].max()) if not df.empty else None

# ----------------------------------------------------------------------
# Uncertainty band availability
# ----------------------------------------------------------------------
# MEDIUM: overlay committed quantile CSV (baseline only).
# LOW / HIGH: overlay the MEDIUM CSV as a "reference only" band with a
# caption explaining the preset band has not yet been regenerated.
qf = None
band_caption = ""
if policy == "baseline":
    qf = load_quantiles(region, "baseline")
    if qf is not None:
        if preset_name == "medium":
            band_caption = ("Band: baseline MC p05\u2013p95 from the committed quantile CSV "
                            "(N = 200, seed 42).")
        else:
            band_caption = (
                f"Preset **{preset_obj['label']}** has not yet been MC-regenerated on disk; "
                "the shaded band shown is the committed **MEDIUM** reference band. Run "
                "`python footprint_model.py --mc 200 --seed 42 --scenarios {region} --policy baseline` "
                "under the chosen preset to generate the matching quantile CSV."
            )
else:
    band_caption = ("No paper-safe MC for non-baseline policies (Methods M14); "
                    "only the deterministic central trajectory is shown.")

# ----------------------------------------------------------------------
# Turning-point metric strip
# ----------------------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Peak emissions (deterministic)", fmt_emissions(turning["peak_emissions"]),
          f"Peak year {turning['peak_year']}")
turning_yr = turning.get("turning_year")
if turning_yr:
    m2.metric("Turning year (deterministic)", str(turning_yr),
              help="First post-peak year with emissions \u2264 50 % of peak (deterministic central trajectory).")
else:
    m2.metric("Turning year (deterministic)", "Not reached in horizon")
near = df.loc[df["Year"] == min(BASE_YEAR + 6, BASE_YEAR + horizon)]
if not near.empty:
    m3.metric(f"ATS energy ({int(near['Year'].iloc[0])})",
              fmt_energy(float(near.iloc[0]["ATS Total Power (kWh)"])))
    m4.metric(f"ATS emissions ({int(near['Year'].iloc[0])})",
              fmt_emissions(float(near.iloc[0]["ATS Emissions (kg CO2)"])))

# ----------------------------------------------------------------------
# Shared x-range
# ----------------------------------------------------------------------
yrs = df["Year"]
_xmin, _xmax = int(yrs.min()), int(yrs.max())
_xrange = [_xmin, _xmax]


def _legend_below(bottom_margin: int = 140, font_size: int = 10) -> dict:
    return dict(
        height=480,
        legend=dict(orientation="h", x=0.5, y=-0.28,
                    xanchor="center", yanchor="top",
                    font=dict(size=font_size)),
        margin=dict(l=60, r=40, t=60, b=bottom_margin),
    )


def _paper_safe_marker(fig, target_year: int = 2075):
    if _xmax <= target_year:
        return
    fig.add_vline(x=target_year, line_dash="longdash", line_color="#808080",
                  line_width=1.5,
                  annotation_text=f"{target_year} paper target-reach",
                  annotation_position="top right",
                  annotation_font_size=9, annotation_font_color="#505050")
    fig.add_vrect(x0=target_year, x1=_xmax, fillcolor="#808080", opacity=0.05, line_width=0)


def _add_band(fig, metric: str, kind: str, color: str):
    if qf is None:
        return
    bm = band_metadata(qf, metric)
    if not bm["available"] or bm["degenerate"]:
        return
    _, _, factor = scale(qf[f"{metric}_p05"], kind)
    s05 = qf[f"{metric}_p05"] / factor
    s95 = qf[f"{metric}_p95"] / factor
    fig.add_trace(go.Scatter(
        x=list(qf.index) + list(qf.index[::-1]),
        y=list(s05) + list(s95[::-1]),
        fill="toself", fillcolor=rgba(color, 0.18),
        line=dict(width=0),
        name="Baseline MC p05\u2013p95 (ATS total)",
        hoverinfo="skip",
    ))


# ----------------------------------------------------------------------
# Annual energy + emissions charts (stacked decomposition, lines hidden)
# ----------------------------------------------------------------------
ch1, ch2 = st.columns(2)

with ch1:
    fig_e = go.Figure()
    _, eunit, e_factor = scale(df["ATS Total Power (kWh)"], "energy")
    for col, color in [("ECAV Power (kWh)", "#1f77b4"),
                       ("ICECAV Power (kWh)", "#ff7f0e"),
                       ("STI Power (kWh)", "#2ca02c")]:
        fig_e.add_trace(go.Scatter(
            x=yrs, y=df[col] / e_factor, mode="lines",
            name=col.replace(" Power (kWh)", " (share of total)"),
            stackgroup="energy", line=dict(color=color, width=0),
            fillcolor=rgba(color, 0.45),
        ))
    _add_band(fig_e, "ATS Total Power (kWh)", "energy", "#636EFA")
    fig_e.add_trace(go.Scatter(
        x=yrs, y=df["ATS Total Power (kWh)"] / e_factor,
        mode="lines", name="ATS total (live deterministic)",
        line=dict(color="#111", width=3, dash="dash"),
    ))
    if qf is not None and "ATS Total Power (kWh)_p50" in qf.columns:
        fig_e.add_trace(go.Scatter(
            x=qf.index, y=qf["ATS Total Power (kWh)_p50"] / e_factor,
            mode="lines", name="ATS total (MC p50, baseline)",
            line=dict(color="#636EFA", width=1.5, dash="dot"),
        ))
    _paper_safe_marker(fig_e)
    fig_e.update_layout(title="Annual ATS energy demand", xaxis_title="Year",
                        yaxis_title=eunit, hovermode="x unified",
                        **_legend_below())
    fig_e.update_xaxes(range=list(_xrange), autorange=False)
    st.plotly_chart(fig_e, use_container_width=True)

with ch2:
    fig_em = go.Figure()
    _, emunit, em_factor = scale(df["ATS Emissions (kg CO2)"], "emissions")
    for col, color in [("ECAV Emissions (kg CO2)", "#1f77b4"),
                       ("ICECAV Emissions (kg CO2)", "#ff7f0e"),
                       ("STI Emissions (kg CO2)", "#2ca02c")]:
        fig_em.add_trace(go.Scatter(
            x=yrs, y=df[col] / em_factor, mode="lines",
            name=col.replace(" Emissions (kg CO2)", " (share of total)"),
            stackgroup="emissions", line=dict(color=color, width=0),
            fillcolor=rgba(color, 0.45),
        ))
    _add_band(fig_em, "ATS Emissions (kg CO2)", "emissions", "#EF553B")
    fig_em.add_trace(go.Scatter(
        x=yrs, y=df["ATS Emissions (kg CO2)"] / em_factor,
        mode="lines", name="ATS total (live deterministic)",
        line=dict(color="#111", width=3, dash="dash"),
    ))
    if qf is not None and "ATS Emissions (kg CO2)_p50" in qf.columns:
        fig_em.add_trace(go.Scatter(
            x=qf.index, y=qf["ATS Emissions (kg CO2)_p50"] / em_factor,
            mode="lines", name="ATS total (MC p50, baseline)",
            line=dict(color="#EF553B", width=1.5, dash="dot"),
        ))
    _paper_safe_marker(fig_em)
    fig_em.update_layout(title="Annual ATS CO\u2082 emissions", xaxis_title="Year",
                         yaxis_title=emunit, hovermode="x unified",
                         **_legend_below())
    fig_em.update_xaxes(range=list(_xrange), autorange=False)
    st.plotly_chart(fig_em, use_container_width=True)

if band_caption:
    st.caption(band_caption)

# ----------------------------------------------------------------------
# Cumulative overlay
# ----------------------------------------------------------------------
with st.expander("Cumulative ATS energy and emissions (running sum from 2024)"):
    cc1, cc2 = st.columns(2)
    with cc1:
        fig_ce = go.Figure()
        s, cu, _ = scale(df["Cumulative Energy (kWh)"], "energy")
        fig_ce.add_trace(go.Scatter(x=yrs, y=s, mode="lines",
                                    name="Cumulative ATS energy",
                                    line=dict(color="#1f77b4", width=2)))
        _paper_safe_marker(fig_ce)
        fig_ce.update_layout(title="Cumulative ATS energy demand",
                             xaxis_title="Year", yaxis_title=cu.replace("/yr", ""),
                             hovermode="x unified", **_legend_below())
        fig_ce.update_xaxes(range=list(_xrange), autorange=False)
        st.plotly_chart(fig_ce, use_container_width=True)
    with cc2:
        fig_cem = go.Figure()
        s, cu, _ = scale(df["Cumulative Emissions (kg CO2)"], "emissions")
        fig_cem.add_trace(go.Scatter(x=yrs, y=s, mode="lines",
                                     name="Cumulative ATS emissions",
                                     line=dict(color="#d62728", width=2)))
        _paper_safe_marker(fig_cem)
        fig_cem.update_layout(title="Cumulative ATS CO\u2082 emissions",
                              xaxis_title="Year", yaxis_title=cu.replace("/yr", ""),
                              hovermode="x unified", **_legend_below())
        fig_cem.update_xaxes(range=list(_xrange), autorange=False)
        st.plotly_chart(fig_cem, use_container_width=True)

# ----------------------------------------------------------------------
# Subsystem breakdown (former Utility Phase Analysis) — expander
# ----------------------------------------------------------------------
with st.expander("Subsystem decomposition (9 channels)"):
    fig_sub = go.Figure()
    sub_cols = [
        ("ECAV Computing Power (kWh)", "#1f77b4"),
        ("ECAV Sensing Power (kWh)", "#17becf"),
        ("ECAV Communication Power (kWh)", "#aec7e8"),
        ("ICECAV Computing Power (kWh)", "#ff7f0e"),
        ("ICECAV Sensing Power (kWh)", "#ffbb78"),
        ("ICECAV Communication Power (kWh)", "#ffd92f"),
        ("STI Computing Power (kWh)", "#2ca02c"),
        ("STI Sensing Power (kWh)", "#98df8a"),
        ("STI Communication Power (kWh)", "#c5e0b4"),
    ]
    max_val = max(float(df[c].max()) for c, _ in sub_cols if c in df.columns)
    _, su, sub_factor = scale(pd.Series([max_val]), "energy")
    for col, color in sub_cols:
        if col in df.columns:
            fig_sub.add_trace(go.Scatter(
                x=yrs, y=df[col] / sub_factor, mode="lines",
                name=col.replace(" Power (kWh)", ""),
                line=dict(color=color, width=1.5),
            ))
    _paper_safe_marker(fig_sub)
    fig_sub.update_layout(title="Subsystem annual energy",
                          xaxis_title="Year", yaxis_title=su,
                          hovermode="x unified",
                          **_legend_below(bottom_margin=180, font_size=9))
    fig_sub.update_xaxes(range=list(_xrange), autorange=False)
    st.plotly_chart(fig_sub, use_container_width=True)
    st.caption(
        "Hardware efficiency doubling prior applies to ECAV, ICECAV, and STI "
        "computing; it does NOT apply to sensing or communication. Level mix "
        "(`cav_levels`, `sti_levels`) weights the per-level power tables."
    )

# ----------------------------------------------------------------------
# Cross-region comparison (former State Results) — expander
# ----------------------------------------------------------------------
with st.expander("Cross-region comparison (California and Ohio)"):
    cr_regions = [r for r in ["california", "ohio"] if r in visible_regions]
    colors = {"california": "#1f77b4", "ohio": "#ff7f0e"}
    fig_cr = go.Figure()
    fig_cr_em = go.Figure()
    for r in cr_regions:
        rcfg = load_runtime_config(r, "baseline")
        rcv = controls_from_config(rcfg, r, "baseline")
        rdf = run_simulation(apply_controls(rcfg, rcv), horizon)
        s, unit, _ = scale(rdf["ATS Total Power (kWh)"], "energy")
        fig_cr.add_trace(go.Scatter(x=rdf["Year"], y=s, mode="lines",
                                    name=REGION_LABELS[r],
                                    line=dict(color=colors[r], width=2)))
        s2, unit2, _ = scale(rdf["ATS Emissions (kg CO2)"], "emissions")
        fig_cr_em.add_trace(go.Scatter(x=rdf["Year"], y=s2, mode="lines",
                                       name=REGION_LABELS[r],
                                       line=dict(color=colors[r], width=2)))
    fig_cr.update_layout(title="Annual ATS energy \u2014 CA vs OH (baseline)",
                         xaxis_title="Year", yaxis_title=unit,
                         hovermode="x unified", **_legend_below())
    fig_cr_em.update_layout(title="Annual ATS CO\u2082 \u2014 CA vs OH (baseline)",
                            xaxis_title="Year", yaxis_title=unit2,
                            hovermode="x unified", **_legend_below())
    for f in (fig_cr, fig_cr_em):
        f.update_xaxes(range=list(_xrange), autorange=False)
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_cr, use_container_width=True)
    c2.plotly_chart(fig_cr_em, use_container_width=True)
    st.caption(
        "Both series are live deterministic outputs at baseline controls. "
        "U.S. Average is quarantined from this comparison."
    )

# ----------------------------------------------------------------------
# Uncertainty details (former Uncertainty Analysis) — expander
# ----------------------------------------------------------------------
with st.expander("Uncertainty details \u2014 quantile support matrix"):
    rows = []
    for r in REGION_ORDER:
        for p in POLICY_ORDER:
            qp = quantile_path(r, p)
            qf_r = load_quantiles(r, p) if qp.exists() else None
            bm = band_metadata(qf_r, "ATS Emissions (kg CO2)")
            sc = mc_sample_count(r, p)
            sf = region_paper_safety(r)
            if not sf.get("paper_safe", True):
                paper = "QUARANTINED (region)"
            elif p != "baseline":
                paper = "Exploratory (not paper-safe: non-baseline MC)"
            else:
                paper = "Yes"
            rows.append({
                "Region": REGION_LABELS[r],
                "Policy": POLICY_LABELS.get(p, p),
                "Quantile CSV": "Yes" if qp.exists() else "No",
                "Band non-zero": "Yes" if bm["available"] and not bm["degenerate"] else "No",
                "MC runs": sc or "\u2014",
                "Paper-safe": paper,
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        f"Active preset: **{preset_obj['label']}**. Paper-safe MC uses the "
        "baseline policy only under MEDIUM (see METHODS_ALIGNMENT \u00a7M14)."
    )

# ----------------------------------------------------------------------
# Provenance footer
# ----------------------------------------------------------------------
with st.expander("Provenance and runtime diagnostics"):
    st.caption(REGION_NOTES.get(region, ""))
    st.dataframe(pd.DataFrame(runtime_diagnostics(runtime_cfg, region, policy)),
                 use_container_width=True, hide_index=True)
    st.markdown(
        f"""
**Active preset:** `{preset_obj['preset']}` \u2014 paper-safe: **{preset_obj['paper_safe']}**
**Preset description:** {preset_obj['description']}

**Quantile CSV:** `{quantile_path(region, policy).relative_to(quantile_path(region, policy).parents[1])}` \u2014 {'present' if quantile_path(region, policy).exists() else 'missing'}
**MC runs (baseline CSV):** {mc_sample_count(region, 'baseline') or 'n/a'}

Sidecar metadata, saturation flags, and the interpretation boundary are read
from `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json`.
"""
    )

st.divider()
st.caption(
    "Panel 2 is the main utility-phase panel. Preset selection never re-centres "
    "priors; deterministic central trajectories are preset-invariant. Non-baseline "
    "policy Monte-Carlo bands (if any) remain exploratory and are not paper-safe."
)
