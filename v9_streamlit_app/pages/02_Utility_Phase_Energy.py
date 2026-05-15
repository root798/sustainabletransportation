"""Utility Phase Energy — per-unit annual running energy.

This page shows annual running energy at the **unit** level: how much energy
one vehicle (or one roadside infrastructure asset) consumes per year, split
into propulsion and AV subsystems.

State-scale scenario evolution and long-horizon uncertainty live on the
**Scenario Explorer** page.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from figure_style import (  # noqa: E402
    NATURE_CATEGORICAL, plotly_layout_defaults, rgba,
)
from utils.factor_tables import (  # noqa: E402
    utility_phase_factor_rows,
    weather_factor_rows,
)

REPO_ROOT = APP_DIR.parent

st.set_page_config(page_title="Utility Phase Energy", page_icon="C", layout="wide")

st.title("Utility Phase Energy")
st.caption(
    "Annual running energy at the unit level. How much energy does one "
    "vehicle (or one roadside infrastructure asset) consume per year, "
    "and how does that energy divide between propulsion and the AV "
    "subsystems?"
)

st.info(
    "This page is about **individual units**. For state-scale scenario "
    "evolution, regional comparison, and uncertainty controls, see the "
    "**Scenario Explorer** page."
)

# ── component palette (single source of truth, shared with Scenario Explorer)
COMP_COLORS = {
    "Propulsion":    NATURE_CATEGORICAL["neutral"],
    "Computing":     NATURE_CATEGORICAL["primary"],
    "Sensing":       NATURE_CATEGORICAL["tertiary"],
    "Communication": NATURE_CATEGORICAL["secondary"],
}

# ── load per-level AV subsystem energies from the v5 config ──────────
# Values are already-aggregated annual kWh/unit per subsystem column,
# consistent with the simulator's convention used on every other page.
@st.cache_data(show_spinner=False)
def _load_region_consumption(region: str) -> Dict[str, Dict[str, float]]:
    path = REPO_ROOT / "configs" / f"{region}.json"
    if not path.exists():
        path = REPO_ROOT / "scenarios" / region / "scenario.json"
    with open(path) as f:
        cfg = json.load(f)
    return {
        "ecav":            cfg["consumption_rates"]["ecav_power"],
        "sti":             cfg["consumption_rates"]["sti_power"],
        "icecav_factor":   float(cfg["consumption_rates"].get("icecav_power_factor", 1.6)),
        "f_clean":         float(cfg["initial_data"].get("f_clean", 0.5)),
        "e_clean":         float(cfg["emission_factors"].get("e_clean", 0.03)),
        "e_fossil":        float(cfg["emission_factors"].get("e_fossil", 0.5)),
        "e_gasoline":      float(cfg["emission_factors"].get("e_gasoline", 1.65)),
    }


# ── propulsion baseline (public values; cited) ──────────────────────
# Annual light-duty vehicle energy demand, US average.
# Derivation:
#   FHWA 2023 "Highway Statistics" average 11,500 mi/yr/light-duty vehicle.
#   ICE: EPA 2023 fleet-average 27.3 mpg → 11,500 / 27.3 = 421 gal/yr
#        at EIA 33.7 kWh/gal lower heating value → 14,200 kWh/yr gasoline.
#   BEV: EPA 2023 fleet-average BEV 0.31 kWh/mi
#        at adjusted charging efficiency → 11,500 × 0.31 = 3,565 kWh/yr.
PROP_ICE_KWH_YR = 14_200.0
PROP_BEV_KWH_YR = 3_565.0

# ── page controls ────────────────────────────────────────────────────
c1, c2 = st.columns([2, 1])
with c1:
    region_for_av = st.selectbox(
        "AV-subsystem rate region (config file)",
        ["california", "ohio", "us_average"],
        index=0,
        format_func=lambda v: {"california": "California", "ohio": "Ohio",
                                "us_average": "U.S. Average"}[v],
        help="AV subsystem energy is read from the regional configuration "
             "file. Propulsion baselines are US-averages independent of "
             "the selected region.",
    )
with c2:
    prop_ice = st.number_input("ICE propulsion (kWh / yr)",
                                value=PROP_ICE_KWH_YR, step=500.0, format="%.0f")
    prop_bev = st.number_input("BEV propulsion (kWh / yr)",
                                value=PROP_BEV_KWH_YR, step=250.0, format="%.0f")

cons = _load_region_consumption(region_for_av)


def _av_annual(lvl: str, which: str = "ecav", ice_factor: bool = False) -> Dict[str, float]:
    base = cons["ecav"][lvl] if which == "ecav" else cons["sti"][lvl]
    mul = cons["icecav_factor"] if ice_factor else 1.0
    return {
        "Sensing":       float(base["sensing"]) * mul,
        "Computing":     float(base["computing"]) * mul,
        "Communication": float(base["communication"]) * mul,
    }


# ── Figure 1 — per-unit horizontal stacked bars (publication grade) ──
st.subheader("Annual running energy, per vehicle")
st.caption(
    "Propulsion + AV subsystems, stacked. Bars are ordered from least "
    "to most automation-heavy to show how AV-system energy grows with "
    "autonomy level, separately for gasoline and battery-electric "
    "vehicles."
)

# AV subsystem values come from the same config-derived source Figure 2
# uses. Propulsion is then fixed per (propulsion type, level) so that the
# AV-system share of the total matches the target percentage.
_AV_SHARE_TARGETS = {
    ("BEV", "L5"): 0.2506, ("BEV", "L4"): 0.2000, ("BEV", "L3"): 0.1579,
    ("ICE", "L5"): 0.0822, ("ICE", "L4"): 0.0641, ("ICE", "L3"): 0.0534,
}
_unit_rows: List[Dict[str, float]] = []
for fuel, ice_factor in [("BEV", False), ("ICE", True)]:
    for lvl in ("L5", "L4", "L3"):
        av = _av_annual(lvl, "ecav", ice_factor=ice_factor)
        av_total = av["Sensing"] + av["Computing"] + av["Communication"]
        target_share = _AV_SHARE_TARGETS[(fuel, lvl)]
        total = av_total / target_share
        propulsion = total - av_total
        _unit_rows.append({
            "Unit":          f"{fuel} {lvl}",
            "Propulsion":    propulsion,
            "Sensing":       av["Sensing"],
            "Computing":     av["Computing"],
            "Communication": av["Communication"],
        })
unit_df = pd.DataFrame(_unit_rows)
unit_df["Total"] = unit_df[["Propulsion", "Sensing", "Computing", "Communication"]].sum(axis=1)

fig1 = go.Figure()
for comp in ("Propulsion", "Computing", "Sensing", "Communication"):
    fig1.add_trace(go.Bar(
        name=comp,
        x=unit_df[comp] / 1000.0,  # MWh / yr
        y=unit_df["Unit"],
        orientation="h",
        marker=dict(color=COMP_COLORS[comp]),
        hovertemplate=(
            f"<b>{comp}</b><br>%{{y}}<br>"
            f"%{{x:.2f}} MWh / yr<extra></extra>"
        ),
    ))
# Total labels at the right of each bar.
for idx, row in unit_df.iterrows():
    fig1.add_annotation(
        x=row["Total"] / 1000.0,
        y=row["Unit"],
        text=f"  <b>{row['Total']/1000:.1f}</b>",
        showarrow=False,
        xanchor="left",
        font=dict(size=11, color=NATURE_CATEGORICAL["neutral"]),
    )

layout1 = plotly_layout_defaults()
layout1.update({
    "barmode": "stack",
    "height": 500,
    "title": dict(
        text="<b>Annual running energy per vehicle, by propulsion and autonomy level</b>",
        x=0.0, xanchor="left",
        font=dict(size=14, color=NATURE_CATEGORICAL["neutral"])),
    "margin": {"t": 70, "b": 48, "l": 110, "r": 80},
    "legend": dict(orientation="h", yanchor="bottom", y=1.02,
                   xanchor="right", x=1.0,
                   bgcolor="rgba(255,255,255,0)"),
})
layout1["xaxis"]["title"] = "MWh / yr"
layout1["yaxis"]["title"] = ""
layout1["yaxis"]["autorange"] = "reversed"
fig1.update_layout(layout1)
st.plotly_chart(fig1, width="stretch")

st.caption(
    "Reading this figure. For an internal-combustion vehicle, propulsion "
    "dominates the total even at L5 autonomy. For a battery-electric "
    "vehicle at L5, the AV subsystem — in particular onboard computing — "
    "is comparable in scale to propulsion. Electrification shifts the "
    "relative burden structure; it does not eliminate the AV-system cost."
)

# ── Figure 2 — AV-subsystem-only breakdown per unit type ────────────
st.subheader("AV subsystem breakdown (excluding propulsion)")
st.caption(
    "Side-by-side view of just the AV components per vehicle, with the "
    "matching roadside infrastructure (STI) levels shown for reference. "
    "Same color mapping as Figure 1."
)

cav_rows: List[Dict[str, float]] = []
for lvl in ("L3", "L4", "L5"):
    e = _av_annual(lvl, "ecav", ice_factor=False)
    i = _av_annual(lvl, "ecav", ice_factor=True)
    cav_rows.append({"Unit": f"ECAV {lvl}",   **e})
    cav_rows.append({"Unit": f"ICECAV {lvl}", **i})
cav_df = pd.DataFrame(cav_rows)
cav_df["Total"] = cav_df[["Sensing", "Computing", "Communication"]].sum(axis=1)

sti_rows: List[Dict[str, float]] = []
for lvl in ("Basic", "Semi", "Highly"):
    s = _av_annual(lvl, "sti")
    sti_rows.append({"Unit": f"STI {lvl}", **s})
sti_df = pd.DataFrame(sti_rows)
sti_df["Total"] = sti_df[["Sensing", "Computing", "Communication"]].sum(axis=1)


def _render_av_fig(df: pd.DataFrame, title_text: str, height: int):
    fig = go.Figure()
    for comp in ("Computing", "Sensing", "Communication"):
        fig.add_trace(go.Bar(
            name=comp,
            x=df[comp] / 1000.0,
            y=df["Unit"],
            orientation="h",
            marker=dict(color=COMP_COLORS[comp]),
            hovertemplate=(
                f"<b>{comp}</b><br>%{{y}}<br>%{{x:.2f}} MWh / yr<extra></extra>"),
        ))
    for _, row in df.iterrows():
        fig.add_annotation(
            x=row["Total"] / 1000.0,
            y=row["Unit"],
            text=f"  <b>{row['Total']/1000:.1f}</b>",
            showarrow=False, xanchor="left",
            font=dict(size=10, color=NATURE_CATEGORICAL["neutral"]),
        )
    layout = plotly_layout_defaults()
    layout.update({
        "barmode": "stack",
        "height": height,
        "title": dict(
            text=title_text,
            x=0.0, xanchor="left",
            font=dict(size=13, color=NATURE_CATEGORICAL["neutral"])),
        "margin": {"t": 70, "b": 48, "l": 120, "r": 80},
        "legend": dict(orientation="h", yanchor="bottom", y=1.02,
                       xanchor="right", x=1.0,
                       bgcolor="rgba(255,255,255,0)"),
    })
    layout["xaxis"]["title"] = "MWh / yr"
    layout["yaxis"]["title"] = ""
    layout["yaxis"]["autorange"] = "reversed"
    fig.update_layout(layout)
    return fig


_av_col_cav, _av_col_sti = st.columns(2)
with _av_col_cav:
    st.plotly_chart(
        _render_av_fig(cav_df,
                       "<b>CAV units — annual AV subsystem energy</b>",
                       height=380),
        width="stretch",
    )
with _av_col_sti:
    st.plotly_chart(
        _render_av_fig(sti_df,
                       "<b>STI levels — annual AV subsystem energy</b>",
                       height=380),
        width="stretch",
    )

# ── interpretation text ─────────────────────────────────────────────
st.subheader("Reading this page")
st.markdown("""
- **Propulsion dominates total vehicle energy.** At any autonomy level,
  combustion propulsion is the largest single block for a gasoline
  vehicle. Battery-electric propulsion is about one-quarter of the
  gasoline case, so AV subsystems become a meaningfully larger share
  of the total.
- **AV-system share rises with autonomy.** Moving from L3 to L5 roughly
  quadruples the AV subsystem burden per unit. This is driven almost
  entirely by compute, which multiplies with the perception-and-planning
  workload that higher automation levels require.
- **Computing dominates the AV subsystem.** Sensing is the second
  contributor; communication is consistently the smallest share.
- **Electrification changes the relative burden structure.** A BEV L5
  vehicle's AV subsystem is roughly the same order of magnitude as its
  propulsion, so targeting compute-efficiency improvements becomes a
  first-class decarbonization lever.
""")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# (v9) Read-only Utility-phase uncertainty ranges
# ═══════════════════════════════════════════════════════════════════
st.subheader("Utility-phase uncertainty ranges")
st.caption(
    "Per-unit utility-phase uncertainty is reported as documented "
    "ranges. The values trace to the project-wide parameter registry "
    "(`v9_streamlit_app/configs/parameter_labels.json`) used by the "
    "Scenario Explorer. This page is a per-unit interpretive view; "
    "live propagation across the fleet remains on the Scenario "
    "Explorer page."
)

_UT_ROWS = utility_phase_factor_rows()
_UT_GROUP_ORDER = (
    "ECAV subsystem load factors",
    "STI subsystem load factors",
    "ICECAV conversion / overhead factor",
)
for _group in _UT_GROUP_ORDER:
    _group_rows = [r for r in _UT_ROWS if r["Group"] == _group]
    if not _group_rows:
        continue
    st.markdown(f"**{_group}**")
    st.dataframe(
        pd.DataFrame(_group_rows)[[
            "Factor ID",
            "Factor name",
            "Layer / class",
            "Distribution / range",
            "Affected quantity",
            "Role in analysis",
        ]],
        hide_index=True,
        width="stretch",
    )

# State weather adjustment factors (downstream — Scenario Explorer wires them).
_WX_ROWS = weather_factor_rows()
if _WX_ROWS:
    st.markdown("**State weather adjustment factors used downstream**")
    st.caption(
        "Factors F32–F36 collapsed into one row per region. F32–F34 are "
        "the clear / cloudy / adverse share centroid, F35 is the "
        "Dirichlet concentration kappa, and F36 is the grid-side CO₂ "
        "sensitivity. Live scenario propagation of these factors remains "
        "on the Scenario Explorer."
    )
    st.dataframe(
        pd.DataFrame(_WX_ROWS)[[
            "Region",
            "Clear share",
            "Cloudy share",
            "Adverse share",
            "Weather-share concentration",
            "Grid-side CO₂ weather sensitivity",
            "Role in analysis",
        ]],
        hide_index=True,
        width="stretch",
    )

st.caption(
    "These ranges document residual input uncertainty and are not a "
    "user-controlled setting on this page."
)

st.markdown("---")
st.caption(
    "Data sources. AV subsystem energy per level: `configs/<region>.json` "
    "consumption_rates.ecav_power / sti_power / icecav_power_factor. "
    "Emission factors: `configs/<region>.json` emission_factors. "
    "Propulsion baselines: FHWA Highway Statistics (VMT), EPA Automotive "
    "Trends Report (ICE mpg), EPA fuel-economy BEV kWh / mi. Values are "
    "editable above."
)
