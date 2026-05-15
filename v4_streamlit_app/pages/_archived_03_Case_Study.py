"""Panel 3 — Case Study (rebuttal-ready, interactive).

Focused region view for a single selected region, selectable preset, and
optional structural-shock overlay. Export of a publication-style figure in
the `refstyle` layout. See
`audits/uncertainty_governance/PANEL_REORGANIZATION_PLAN.md`.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (  # noqa: E402
    BASE_YEAR, DEFAULT_HORIZON, POLICY_LABELS, REGION_LABELS, UNCERTAINTY_PRESETS,
    apply_controls, apply_uncertainty_preset, controls_from_config,
    fmt_emissions, fmt_energy, load_quantiles, load_runtime_config,
    load_uncertainty_preset, mc_sample_count, region_paper_safety, rgba,
    run_simulation, scale, compute_turning_metrics,
)

REPO_DIR = APP_DIR.parent
SHOCKS_DIR = REPO_DIR / "results" / "shocks"

_SHOCK_PATTERN = re.compile(
    r"^(?P<region>[^_]+)__(?P<shock>[a-z_]+?)__(?P<severity>mild|moderate|severe)__"
    r"onset-(?P<onset>\d{4})__duration-(?P<duration>\d{2,3})_results\.csv$"
)

st.set_page_config(page_title="Panel 3 — Case Study", page_icon="C", layout="wide")
st.title("Panel 3 — Case Study")
st.caption(
    "Focused region view under a chosen uncertainty preset with optional "
    "structural-shock overlay. Designed for rebuttal-ready screenshots and "
    "figure export."
)

# ----------------------------------------------------------------------
# Controls
# ----------------------------------------------------------------------
col_a, col_b, col_c = st.columns(3)
with col_a:
    region = st.selectbox("Region", ["california", "ohio"],
                          format_func=lambda r: REGION_LABELS[r])
with col_b:
    preset_name = st.selectbox(
        "Uncertainty preset", list(UNCERTAINTY_PRESETS),
        index=list(UNCERTAINTY_PRESETS).index("medium"),
        format_func=lambda p: {"low": "Low (evidence-anchored)",
                               "medium": "Medium (paper-safe)",
                               "high": "High (exploratory)"}.get(p, p),
    )
with col_c:
    policy = "baseline"
    st.text_input("Policy", value="baseline (paper-safe)", disabled=True,
                  help="Case Study is baseline-only; non-baseline policies are not paper-safe MC.")

preset_obj = load_uncertainty_preset(preset_name, region)

# ----------------------------------------------------------------------
# Preset banner and exploratory watermark gating
# ----------------------------------------------------------------------
exploratory_mode = not preset_obj["paper_safe"]
if exploratory_mode:
    st.warning(
        f"\u26a0\ufe0f **{preset_obj['label']}** \u2014 EXPLORATORY. Exports "
        "generated under this preset carry an exploratory watermark and must "
        "NOT be cited for headline paper claims."
    )
else:
    st.success(f"**{preset_obj['label']}** \u2014 paper-safe.")

# ----------------------------------------------------------------------
# Shock discovery (CA / OH only; U.S. Average quarantined)
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _discover_shocks() -> pd.DataFrame:
    rows = []
    if not SHOCKS_DIR.exists():
        return pd.DataFrame(rows)
    for p in sorted(SHOCKS_DIR.iterdir()):
        if not p.is_file() or not p.name.endswith("_results.csv"):
            continue
        m = _SHOCK_PATTERN.match(p.name)
        if m is None:
            continue
        rows.append({
            "region": m.group("region"), "shock": m.group("shock"),
            "severity": m.group("severity"),
            "onset_year": int(m.group("onset")),
            "duration_years": int(m.group("duration")),
            "csv_path": str(p),
        })
    return pd.DataFrame(rows)


shocks_all = _discover_shocks()
shocks_all = shocks_all[shocks_all["region"].isin(["california", "ohio"])]
shocks_region = shocks_all[shocks_all["region"] == region]
shock_families = ["(none)"] + sorted(shocks_region["shock"].unique().tolist())

col_d, col_e = st.columns(2)
with col_d:
    shock_family = st.selectbox("Structural shock overlay", shock_families)
with col_e:
    if shock_family != "(none)":
        severities = sorted(shocks_region.loc[shocks_region["shock"] == shock_family, "severity"].unique().tolist())
        shock_severity = st.selectbox("Severity on disk", severities,
                                      help="Only severities with a committed CSV are shown.")
    else:
        shock_severity = None

# ----------------------------------------------------------------------
# Live deterministic simulation
# ----------------------------------------------------------------------
cfg = load_runtime_config(region, policy)
cv = controls_from_config(cfg, region, policy)
rc = apply_controls(cfg, cv)
rc = apply_uncertainty_preset(rc, preset_name, region)
df = run_simulation(rc, DEFAULT_HORIZON)

turning = compute_turning_metrics(df)
_xmin, _xmax = int(df["Year"].min()), int(df["Year"].max())

qf = load_quantiles(region, policy) if preset_name == "medium" else None

# ----------------------------------------------------------------------
# Reviewer-ready key cards
# ----------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Region", REGION_LABELS[region])
k2.metric("Peak year (deterministic)", str(turning["peak_year"]))
k3.metric("Turning year (deterministic)",
          str(turning["turning_year"]) if turning.get("turning_year") else "Not reached")
sc = mc_sample_count(region, policy) or "n/a"
k4.metric("Committed MC runs", str(sc),
          help="Only MEDIUM uses the committed MC CSV; other presets are pending regeneration.")

# ----------------------------------------------------------------------
# Main figure — ATS total energy, ATS total emissions (two panels)
# ----------------------------------------------------------------------
def _paper_safe_marker(fig, target_year: int = 2075):
    if _xmax <= target_year:
        return
    fig.add_vline(x=target_year, line_dash="longdash", line_color="#808080",
                  line_width=1.5,
                  annotation_text=f"{target_year} paper target-reach",
                  annotation_position="top right",
                  annotation_font_size=9, annotation_font_color="#505050")
    fig.add_vrect(x0=target_year, x1=_xmax, fillcolor="#808080",
                  opacity=0.05, line_width=0)


def _exploratory_watermark(fig):
    if not exploratory_mode:
        return
    fig.add_annotation(
        xref="paper", yref="paper", x=0.5, y=0.5,
        text="EXPLORATORY", showarrow=False,
        font=dict(size=48, color="rgba(200, 0, 0, 0.08)"),
        xanchor="center", yanchor="middle",
    )


def _band(fig, metric: str, kind: str, color: str):
    if qf is None:
        return
    if any(f"{metric}_{t}" not in qf.columns for t in ["p05", "p50", "p95"]):
        return
    _, _, factor = scale(qf[f"{metric}_p05"], kind)
    fig.add_trace(go.Scatter(
        x=list(qf.index) + list(qf.index[::-1]),
        y=list(qf[f"{metric}_p05"] / factor) + list((qf[f"{metric}_p95"] / factor)[::-1]),
        fill="toself", fillcolor=rgba(color, 0.18),
        line=dict(width=0),
        name="Baseline MC p05\u2013p95 (ATS total)", hoverinfo="skip",
    ))


def _shock_overlay(fig, metric: str, kind: str):
    if shock_family == "(none)" or shock_severity is None:
        return
    sub = shocks_region[(shocks_region["shock"] == shock_family)
                        & (shocks_region["severity"] == shock_severity)]
    if sub.empty:
        return
    shock_df = pd.read_csv(sub.iloc[0]["csv_path"])
    _, _, factor = scale(df[metric], kind)
    fig.add_trace(go.Scatter(
        x=shock_df["Year"], y=shock_df[metric] / factor, mode="lines",
        name=(f"{shock_family} / {shock_severity} "
              f"(onset {int(sub.iloc[0]['onset_year'])}, duration {int(sub.iloc[0]['duration_years'])}y)"),
        line=dict(color="#d62728", width=1.7, dash="dash"),
    ))
    fig.add_vline(x=int(sub.iloc[0]["onset_year"]), line_dash="dot",
                  line_color="#d62728", line_width=1, opacity=0.5)


def _legend_below(bottom_margin: int = 140, font_size: int = 10) -> dict:
    return dict(
        height=480,
        legend=dict(orientation="h", x=0.5, y=-0.28,
                    xanchor="center", yanchor="top",
                    font=dict(size=font_size)),
        margin=dict(l=60, r=40, t=60, b=bottom_margin),
    )


c1, c2 = st.columns(2)
with c1:
    fig_e = go.Figure()
    _, eu, ef = scale(df["ATS Total Power (kWh)"], "energy")
    _band(fig_e, "ATS Total Power (kWh)", "energy", "#636EFA")
    fig_e.add_trace(go.Scatter(
        x=df["Year"], y=df["ATS Total Power (kWh)"] / ef, mode="lines",
        name="ATS total (live deterministic)",
        line=dict(color="#111", width=3, dash="dash"),
    ))
    if qf is not None and "ATS Total Power (kWh)_p50" in qf.columns:
        fig_e.add_trace(go.Scatter(
            x=qf.index, y=qf["ATS Total Power (kWh)_p50"] / ef,
            mode="lines", name="ATS total (MC p50)",
            line=dict(color="#636EFA", width=1.5, dash="dot"),
        ))
    _shock_overlay(fig_e, "ATS Total Power (kWh)", "energy")
    _paper_safe_marker(fig_e)
    _exploratory_watermark(fig_e)
    fig_e.update_layout(title=f"Annual ATS energy \u2014 {REGION_LABELS[region]}",
                        xaxis_title="Year", yaxis_title=eu,
                        hovermode="x unified", **_legend_below())
    fig_e.update_xaxes(range=[_xmin, _xmax], autorange=False)
    st.plotly_chart(fig_e, use_container_width=True)

with c2:
    fig_em = go.Figure()
    _, emu, emf = scale(df["ATS Emissions (kg CO2)"], "emissions")
    _band(fig_em, "ATS Emissions (kg CO2)", "emissions", "#EF553B")
    fig_em.add_trace(go.Scatter(
        x=df["Year"], y=df["ATS Emissions (kg CO2)"] / emf, mode="lines",
        name="ATS total (live deterministic)",
        line=dict(color="#111", width=3, dash="dash"),
    ))
    if qf is not None and "ATS Emissions (kg CO2)_p50" in qf.columns:
        fig_em.add_trace(go.Scatter(
            x=qf.index, y=qf["ATS Emissions (kg CO2)_p50"] / emf,
            mode="lines", name="ATS total (MC p50)",
            line=dict(color="#EF553B", width=1.5, dash="dot"),
        ))
    _shock_overlay(fig_em, "ATS Emissions (kg CO2)", "emissions")
    _paper_safe_marker(fig_em)
    _exploratory_watermark(fig_em)
    fig_em.update_layout(title=f"Annual ATS CO\u2082 \u2014 {REGION_LABELS[region]}",
                         xaxis_title="Year", yaxis_title=emu,
                         hovermode="x unified", **_legend_below())
    fig_em.update_xaxes(range=[_xmin, _xmax], autorange=False)
    st.plotly_chart(fig_em, use_container_width=True)

# ----------------------------------------------------------------------
# Figure export
# ----------------------------------------------------------------------
st.subheader("Export")
exp_df = df[["Year", "ATS Total Power (kWh)", "ATS Emissions (kg CO2)",
             "ECAV Power (kWh)", "ICECAV Power (kWh)", "STI Power (kWh)",
             "ECAV Emissions (kg CO2)", "ICECAV Emissions (kg CO2)", "STI Emissions (kg CO2)"]].copy()
exp_df["preset"] = preset_name
exp_df["policy"] = policy
exp_df["region"] = region

safety = "paper_safe" if preset_obj["paper_safe"] else "exploratory"
fname_stem = f"clear_ats_{region}_{policy}_{preset_name}_{safety}_casestudy"

col_x, col_y = st.columns(2)
col_x.download_button(
    "Download case-study CSV (deterministic)",
    data=exp_df.to_csv(index=False),
    file_name=f"{fname_stem}.csv",
    mime="text/csv",
    use_container_width=True,
)
col_y.download_button(
    "Download scenario JSON",
    data=json.dumps({"region": region, "policy": policy,
                     "preset": preset_name, "paper_safe": preset_obj["paper_safe"],
                     "horizon_years": DEFAULT_HORIZON,
                     "shock_family": shock_family,
                     "shock_severity": shock_severity,
                     }, indent=2),
    file_name=f"{fname_stem}.json",
    mime="application/json",
    use_container_width=True,
)

st.caption(
    "For publication-style PDF / PNG export matching the `refstyle` layout, "
    "run `python scripts/build_refstyle_figures.py` (writes to "
    "`reports/paper_support/reference_style/`). That script uses the committed "
    "MEDIUM quantile CSVs; to export under LOW / HIGH, first regenerate the "
    "preset-specific quantile CSV and then point the `refstyle` script at it."
)

# ----------------------------------------------------------------------
# Rebuttal-ready annotation text
# ----------------------------------------------------------------------
with st.expander("Reviewer-ready annotations (copy-paste)"):
    bnd_msg = ""
    if preset_name == "medium":
        bnd_msg = ("Under the MEDIUM preset, the interpretation boundary falls at "
                   "2030 for California and 2031 for Ohio (pointwise ATS-emissions "
                   "band width crosses 150 % of the median).")
    elif preset_name == "low":
        bnd_msg = ("LOW preset narrows the band to evidence-anchored priors only; "
                   "the interpretation boundary is expected to shift later than the "
                   "MEDIUM values after a 200-run regeneration.")
    else:
        bnd_msg = ("HIGH preset widens scenario-adjustable priors for exploratory "
                   "analysis; do not cite its bands as paper results.")
    peak_msg = ("Peak and turning years are attributed to the deterministic central "
                "trajectory (Methods M12). Ohio's deterministic turning year is not "
                "reached within the 2024–2092 horizon; 87 of 200 MC runs do reach "
                "turning (conditional p50 = 2081; achieved_fraction = 0.435). This "
                "is disclosed in the metrics-quantiles CSV and is not cited as a "
                "paper headline.")
    st.markdown(f"- **Preset:** {preset_obj['label']} ({'paper-safe' if preset_obj['paper_safe'] else 'exploratory'}).")
    st.markdown(f"- **Region:** {REGION_LABELS[region]}.")
    st.markdown(f"- **Policy:** baseline (only paper-safe MC scope).")
    st.markdown(f"- {bnd_msg}")
    st.markdown(f"- {peak_msg}")
    st.markdown(
        "- **Shocks overlay:** "
        + ("none; MC band and deterministic trajectory only."
           if shock_family == "(none)"
           else f"{shock_family} at {shock_severity} severity (discrete labelled scenario; not merged into MC bands).")
    )
    st.caption(
        "This block is designed to be pasted into a reviewer response while "
        "preserving the deterministic-attribution convention and the baseline-only "
        "MC scope."
    )

# ----------------------------------------------------------------------
# Provenance footer
# ----------------------------------------------------------------------
with st.expander("Provenance footer"):
    st.markdown(
        f"""
**Data sources**
- Live deterministic: `scenarios/{region}/scenario.json` (canonical) → `TransportModel` → annual series.
- MEDIUM MC band: `results/{region}__policy-baseline__model-fixed_table_quantiles.csv`.
- Saturation sidecar: `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json`.
- Preset JSON: `configs/ui_presets/uncertainty_{preset_name}.json`.
- Shock overlay (if selected): `results/shocks/{shock_family if shock_family != '(none)' else 'n/a'}__*.csv`.

**Paper-safety**
- Preset paper-safe: `{preset_obj['paper_safe']}`.
- Policy gate: baseline only.
- Structural shocks: discrete labelled scenarios; never merged into ordinary MC bands.
"""
    )

st.divider()
st.caption(
    "Panel 3 is designed for rebuttal-ready figures. Only the MEDIUM preset "
    "overlays committed MC bands; LOW and HIGH remain deterministic-only "
    "until regenerated. HIGH carries an EXPLORATORY watermark on every chart."
)
