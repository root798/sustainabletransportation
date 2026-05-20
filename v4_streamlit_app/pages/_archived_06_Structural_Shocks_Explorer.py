"""Structural Shocks Explorer — EXPLORATORY / SUPPLEMENTARY.

Lightweight overlay of deterministic shock trajectories against the baseline
deterministic trajectory for California and Ohio.

Scope and limits (see audits/step_07_structural_shocks/SHOCK_UI_IMPLEMENTATION_NOTE.md):
 - California + Ohio only; U.S. Average remains quarantined.
 - Reads only pre-generated deterministic shock CSVs under `results/shocks/`.
 - Only `moderate` severity is executed on disk at the time of writing; mild
   and severe are design-stage only and will be auto-discovered here if they
   are ever generated.
 - Shocks are NEVER mixed into the baseline Monte-Carlo quantile bands. This
   page displays shocks as labelled separate trajectories only.
 - This page is EXPLORATORY / SUPPLEMENTARY. It does not produce paper-facing
   claims; it does not alter baseline pages.
"""
from __future__ import annotations

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
    REGION_LABELS, REGION_ORDER, available_policies, load_runtime_config,
    controls_from_config, apply_controls, run_simulation,
    scale, fmt_emissions, DEFAULT_HORIZON,
)

REPO_DIR = APP_DIR.parent
SHOCKS_DIR = REPO_DIR / "results" / "shocks"

st.set_page_config(page_title="Structural Shocks Explorer", page_icon="C", layout="wide")
st.title("Structural Shocks Explorer")

st.warning(
    "\u26a0\ufe0f **EXPLORATORY / SUPPLEMENTARY page.** "
    "This view overlays deterministic structural-shock trajectories on the "
    "baseline deterministic trajectory. It does NOT produce paper-facing "
    "quantitative claims. Shocks are labelled discrete scenarios; they are "
    "not mixed into ordinary Monte-Carlo quantile bands. "
    "California and Ohio only; U.S. Average remains quarantined."
)

# ---------------------------------------------------------------------------
# Discover on-disk shock CSVs
# ---------------------------------------------------------------------------

_SHOCK_PATTERN = re.compile(
    r"^(?P<region>[^_]+)__(?P<shock>[a-z_]+?)__(?P<severity>mild|moderate|severe)__"
    r"onset-(?P<onset>\d{4})__duration-(?P<duration>\d{2,3})_results\.csv$"
)


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
            "region": m.group("region"),
            "shock": m.group("shock"),
            "severity": m.group("severity"),
            "onset_year": int(m.group("onset")),
            "duration_years": int(m.group("duration")),
            "csv_path": str(p),
        })
    return pd.DataFrame(rows)


shocks_df = _discover_shocks()
# CA/OH only; U.S. Average quarantine.
shocks_df = shocks_df[shocks_df["region"].isin(["california", "ohio"])].reset_index(drop=True)

if shocks_df.empty:
    st.error(
        "No shock result CSVs discovered under `results/shocks/`. "
        "Generate with `python footprint_model.py --shock all --scenarios california ohio --mc 0`."
    )
    st.stop()

severities_on_disk = sorted(shocks_df["severity"].unique().tolist())
st.info(
    f"**Severities on disk:** {', '.join(severities_on_disk)}. "
    "If only `moderate` is listed, mild / severe are design-stage only — see "
    "`audits/step_07_structural_shocks/SHOCK_SCOPE_HONESTY.md`. Do NOT cite "
    "absent severities in the manuscript."
)

# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------
col_a, col_b, col_c = st.columns(3)
with col_a:
    region = st.selectbox(
        "Region", ["california", "ohio"],
        format_func=lambda r: REGION_LABELS[r],
    )
with col_b:
    available_shocks = sorted(
        shocks_df.loc[shocks_df["region"] == region, "shock"].unique().tolist()
    )
    shock = st.selectbox("Shock family", available_shocks)
with col_c:
    metric = st.selectbox(
        "Metric",
        ["ATS Emissions (kg CO2)", "ATS Total Power (kWh)"],
        format_func=lambda c: "Annual emissions" if "Emissions" in c else "Annual energy",
    )

subset = shocks_df[(shocks_df["region"] == region) & (shocks_df["shock"] == shock)].copy()

# ---------------------------------------------------------------------------
# Baseline deterministic reference
# ---------------------------------------------------------------------------
cfg = load_runtime_config(region, "baseline")
cv = controls_from_config(cfg, region, "baseline")
base_df = run_simulation(apply_controls(cfg, cv), DEFAULT_HORIZON)

base_series, unit, _ = scale(base_df[metric],
                             "emissions" if "Emissions" in metric else "energy")

# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=base_df["Year"], y=base_series, mode="lines",
    name="Baseline (deterministic)",
    line=dict(color="#333333", width=2.5),
))

severity_colors = {
    "mild": "#6baed6",
    "moderate": "#fd8d3c",
    "severe": "#de2d26",
}

rows_meta = []
for _, row in subset.iterrows():
    df_shock = pd.read_csv(row["csv_path"])
    ys, _, _ = scale(df_shock[metric],
                     "emissions" if "Emissions" in metric else "energy")
    # Force same auto-scale factor as baseline so lines are comparable.
    # scale() is auto per-series; to keep them comparable we reuse baseline unit.
    # Re-scale against baseline factor:
    _, _, base_factor = scale(base_df[metric],
                              "emissions" if "Emissions" in metric else "energy")
    ys_consistent = df_shock[metric] / base_factor
    color = severity_colors.get(row["severity"], "#888888")
    nm = (f"{row['shock']} / {row['severity']} "
          f"(onset {row['onset_year']}, duration {row['duration_years']}y)")
    fig.add_trace(go.Scatter(
        x=df_shock["Year"], y=ys_consistent, mode="lines",
        name=nm, line=dict(color=color, width=1.7, dash="dash"),
    ))
    # onset marker
    fig.add_vline(
        x=row["onset_year"], line_dash="dot", line_color=color, line_width=1,
        opacity=0.5,
    )
    rows_meta.append({
        "Shock": row["shock"],
        "Severity": row["severity"],
        "Onset year": row["onset_year"],
        "Duration (yr)": row["duration_years"],
        "CSV": Path(row["csv_path"]).name,
    })

fig.update_layout(
    title=f"{REGION_LABELS[region]} \u2014 {shock} vs baseline (deterministic)",
    xaxis_title="Year", yaxis_title=unit, hovermode="x unified",
    legend=dict(orientation="h"),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Shock scenarios shown")
st.dataframe(pd.DataFrame(rows_meta), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Delta summary
# ---------------------------------------------------------------------------
st.subheader("Shock \u0394 vs baseline at sampled years")
compare_years = [2030, 2045, 2060, 2075, 2092]
delta_rows = []
for _, row in subset.iterrows():
    df_shock = pd.read_csv(row["csv_path"])
    for yr in compare_years:
        b = base_df.loc[base_df["Year"] == yr, metric]
        s = df_shock.loc[df_shock["Year"] == yr, metric]
        if b.empty or s.empty:
            continue
        b0, s0 = float(b.iloc[0]), float(s.iloc[0])
        pct = (s0 - b0) / b0 * 100.0 if b0 != 0 else float("nan")
        delta_rows.append({
            "Shock": row["shock"],
            "Severity": row["severity"],
            "Year": yr,
            "Baseline": fmt_emissions(b0) if "Emissions" in metric else f"{b0:,.3g}",
            "Shock": fmt_emissions(s0) if "Emissions" in metric else f"{s0:,.3g}",
            "\u0394 %": f"{pct:+.2f}%",
        })
if delta_rows:
    st.dataframe(pd.DataFrame(delta_rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Provenance panel (exploratory disclosure)
# ---------------------------------------------------------------------------
with st.expander("Provenance and paper-safety notes"):
    st.markdown(
        """
**Scope of this page**

- Compares each shock trajectory to the baseline deterministic trajectory for
  the same region. Shock CSVs are loaded verbatim from `results/shocks/`.
- Baseline reference is re-simulated live from `scenarios/{region}/scenario.json`
  with the current slider state = baseline controls.
- Uncertainty bands from ordinary Monte-Carlo are intentionally **not** drawn
  here. Shocks are labelled discrete scenarios, not draws from the MC
  distribution (see METHODS_ALIGNMENT \u00a7M6).
- California and Ohio only. U.S. Average is quarantined and does not appear.
- Severities on disk are auto-discovered; if mild or severe are missing, the
  page does not fabricate them.

**Do not cite this page as a paper-facing result.** Paper-safety restrictions
for shock claims are in `audits/step_07_structural_shocks/SHOCK_SCOPE_HONESTY.md`.
        """
    )
    prov_path_candidates = [
        Path(r["csv_path"]).with_name(Path(r["csv_path"]).name.replace("_results.csv", "_provenance.json"))
        for _, r in subset.iterrows()
    ]
    for p in prov_path_candidates:
        if p.exists():
            with st.expander(p.name):
                try:
                    st.json(json.loads(p.read_text(encoding="utf-8")))
                except Exception as exc:
                    st.caption(f"Failed to parse provenance: {exc}")
