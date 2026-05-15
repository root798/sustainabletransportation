"""Utility Phase Energy (v10) — per-unit annual running energy.

This page shows annual running energy at the **unit** level: how much energy
one vehicle (or one roadside infrastructure asset) consumes per year, split
into propulsion and the AV subsystems.

v10 change vs v3-v9
-------------------
The AV-subsystem energies are now assembled **bottom-up from the component
registry** (``component_registry.py``: deployed-silicon power × component
counts × duty × utilization), not from the flat ``consumption_rates.ecav_power``
/ ``sti_power`` config aggregates. As a consequence:

  * The hidden "propulsion back-solve" that earlier versions used to force the
    on-screen percentages to match the manuscript (a hard-coded autonomy-share
    lookup, with propulsion derived as AV-total ÷ that share − AV-total) is
    **removed**. The propulsion bar is the user-supplied value, full stop.
  * The autonomy stack now sits in the realistic 1-25 % range observed in
    fielded CAVs (Tesla FSD HW3/HW4, NVIDIA DRIVE Orin/Thor, Waymo 5th-gen)
    instead of the ~75-85 % implied by the inflated config.

Layout, plot types, colours, captions, and column order are unchanged from v9.
State-scale scenario evolution and long-horizon uncertainty live on the
**Scenario Explorer** page.

See ``audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md``.
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
from component_registry import (  # noqa: E402
    ComponentRegistryEnergyModel,
    CAV_LEVEL_ORDER, STI_LEVEL_ORDER,
    CAV_LEVELS_CANONICAL, STI_LEVELS_CANONICAL,
    ACTIVE_HOURS_PER_DAY,
    component_power_factor_rows,
    OPERATIONAL,
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

st.success(
    "**v10 recalibration.** AV-subsystem energy on this page is assembled "
    "bottom-up from the component registry — per-component deployed-silicon "
    "power (Tesla FSD / NVIDIA DRIVE Orin / NVIDIA DRIVE Thor class for the "
    "compute slot at L3 / L4 / L5) × component counts (manuscript Extended "
    "Data Tables 3 & 4) × duty (~3 h/day for CAVs, 24 h/day for STI) × "
    "per-level utilization. Propulsion is the value entered below, not "
    "back-solved to match a target percentage. See "
    "`audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md`."
)

# ── component palette (single source of truth, shared with Scenario Explorer)
COMP_COLORS = {
    "Propulsion":    NATURE_CATEGORICAL["neutral"],
    "Computing":     NATURE_CATEGORICAL["primary"],
    "Sensing":       NATURE_CATEGORICAL["tertiary"],
    "Communication": NATURE_CATEGORICAL["secondary"],
}


# ── emission factors / overhead from the regional config (unchanged) ──
@st.cache_data(show_spinner=False)
def _load_region_emission_factors(region: str) -> Dict[str, float]:
    path = REPO_ROOT / "configs" / f"{region}.json"
    if not path.exists():
        path = REPO_ROOT / "scenarios" / region / "scenario.json"
    with open(path) as f:
        cfg = json.load(f)
    cr = cfg.get("consumption_rates", {})
    ef = cfg.get("emission_factors", {})
    return {
        "icecav_factor": float(cr.get("icecav_power_factor", 1.6)),
        "f_clean":       float(cfg.get("initial_data", {}).get("f_clean", 0.5)),
        "e_clean":       float(ef.get("e_clean", 0.03)),
        "e_fossil":      float(ef.get("e_fossil", 0.5)),
        "e_gasoline":    float(ef.get("e_gasoline", 1.65)),
    }


# ── bottom-up AV subsystem energy (v10) ──────────────────────────────
# Component registry → per-unit {Sensing, Computing, Communication} kWh/yr.
# Region does NOT enter here: per-unit hardware power is region-independent in
# the manuscript's Table 5 / Table 8 (region only changes the grid emission
# factor and fleet sizes — handled on the Scenario Explorer page).
@st.cache_data(show_spinner=False)
def _registry_subsystem_table(cav_hours: float) -> Dict[str, Dict[str, Dict[str, float]]]:
    model = ComponentRegistryEnergyModel(cav_hours=cav_hours)
    out: Dict[str, Dict[str, Dict[str, float]]] = {"ecav": {}, "sti": {}}
    for lvl in CAV_LEVEL_ORDER:
        d = model.get_ecav_power(lvl, 0, 0)
        out["ecav"][lvl] = {"Sensing": d["sensing"], "Computing": d["computing"],
                            "Communication": d["communication"]}
    for lvl in STI_LEVEL_ORDER:
        d = model.get_sti_power(lvl, 0, 0)
        out["sti"][lvl] = {"Sensing": d["sensing"], "Computing": d["computing"],
                           "Communication": d["communication"]}
    return out


# ── propulsion baseline (public values; cited) ──────────────────────
# Annual light-duty vehicle energy demand, US average.
# Derivation:
#   FHWA "Highway Statistics" average ~11,500 mi/yr per light-duty vehicle.
#   ICE: EPA "Automotive Trends Report" fleet-average ~27.3 mpg →
#        11,500 / 27.3 = 421 gal/yr at EIA 33.7 kWh/gal (GGE LHV) →
#        ~14,200 kWh/yr gasoline-equivalent.
#   BEV: EPA fleet-average BEV ~0.31 kWh/mi at the wall →
#        11,500 × 0.31 = ~3,565 kWh/yr.
PROP_ICE_KWH_YR = 14_200.0
PROP_BEV_KWH_YR = 3_565.0

# ── page controls ────────────────────────────────────────────────────
c1, c2 = st.columns([2, 1])
with c1:
    region_for_ef = st.selectbox(
        "Emission-factor region (config file)",
        ["california", "ohio", "us_average"],
        index=0,
        format_func=lambda v: {"california": "California", "ohio": "Ohio",
                                "us_average": "U.S. Average"}[v],
        help="ICECAV overhead factor and grid emission factors are read from "
             "the regional configuration file. AV-subsystem and propulsion "
             "energy on this page are region-independent (US averages); "
             "regional variation enters via the grid mix and fleet size on "
             "the Scenario Explorer.",
    )
    duty_label = st.radio(
        "CAV duty cycle",
        ["Personal use (~3 h/day)", "Robotaxi (~12 h/day) — sensitivity"],
        index=0, horizontal=True,
        help="Personal-use is the manuscript baseline (~3 h/day). The robotaxi "
             "case is a sensitivity scenario only; it does not change the "
             "Scenario Explorer default.",
    )
with c2:
    prop_ice = st.number_input("ICE propulsion (kWh / yr)",
                                value=PROP_ICE_KWH_YR, step=500.0, format="%.0f")
    prop_bev = st.number_input("BEV propulsion (kWh / yr)",
                                value=PROP_BEV_KWH_YR, step=250.0, format="%.0f")

_ef = _load_region_emission_factors(region_for_ef)
_cav_hours = (ACTIVE_HOURS_PER_DAY["CAV_personal_baseline"]["median"]
              if duty_label.startswith("Personal")
              else ACTIVE_HOURS_PER_DAY["CAV_robotaxi"]["median"])
_subsys = _registry_subsystem_table(_cav_hours)


def _av_annual(lvl: str, which: str = "ecav", ice_factor: bool = False) -> Dict[str, float]:
    base = _subsys["ecav"][lvl] if which == "ecav" else _subsys["sti"][lvl]
    mul = _ef["icecav_factor"] if ice_factor else 1.0
    return {
        "Sensing":       float(base["Sensing"]) * mul,
        "Computing":     float(base["Computing"]) * mul,
        "Communication": float(base["Communication"]) * mul,
    }


# ── Figure 1 — per-unit horizontal stacked bars (publication grade) ──
st.subheader("Annual running energy, per vehicle")
st.caption(
    "Propulsion + AV subsystems, stacked. Bars are ordered from least "
    "to most automation-heavy to show how AV-system energy grows with "
    "autonomy level, separately for gasoline and battery-electric "
    "vehicles. (v10: propulsion is the value entered above — not "
    "back-solved.)"
)

_unit_rows: List[Dict[str, float]] = []
for fuel, ice_factor, prop_val in [("BEV", False, float(prop_bev)),
                                   ("ICE", True, float(prop_ice))]:
    for lvl in ("L5", "L4", "L3"):
        av = _av_annual(lvl, "ecav", ice_factor=ice_factor)
        _unit_rows.append({
            "Unit":          f"{fuel} {lvl}",
            "Propulsion":    prop_val,
            "Sensing":       av["Sensing"],
            "Computing":     av["Computing"],
            "Communication": av["Communication"],
        })
unit_df = pd.DataFrame(_unit_rows)
unit_df["Total"] = unit_df[["Propulsion", "Sensing", "Computing", "Communication"]].sum(axis=1)
unit_df["AV total"] = unit_df[["Sensing", "Computing", "Communication"]].sum(axis=1)
unit_df["AV share"] = unit_df["AV total"] / unit_df["Total"]

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
            f"%{{x:.3f}} MWh / yr<extra></extra>"
        ),
    ))
# Total labels at the right of each bar (now with the AV share alongside).
for idx, row in unit_df.iterrows():
    fig1.add_annotation(
        x=row["Total"] / 1000.0,
        y=row["Unit"],
        text=f"  <b>{row['Total']/1000:.1f}</b>  ({row['AV share']*100:.1f}% AV)",
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
    "margin": {"t": 70, "b": 48, "l": 110, "r": 150},
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
    "dominates the total at every autonomy level — the autonomy stack is a "
    "low-single-digit-to-~10 % share. For a battery-electric vehicle the "
    "smaller propulsion baseline makes the autonomy stack more visible, "
    "rising to roughly one-fifth of the total at L5. Electrification shifts "
    "the relative burden structure; it does not eliminate the autonomy cost. "
    "These shares are computed bottom-up from component datasheets, not fitted "
    "to a target."
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
                f"<b>{comp}</b><br>%{{y}}<br>%{{x:.3f}} MWh / yr<extra></extra>"),
        ))
    for _, row in df.iterrows():
        fig.add_annotation(
            x=row["Total"] / 1000.0,
            y=row["Unit"],
            text=f"  <b>{row['Total']/1000:.2f}</b>",
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
        "margin": {"t": 70, "b": 48, "l": 120, "r": 90},
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

# ── numeric table (per-unit, kWh/yr) ────────────────────────────────
with st.expander("Per-unit annual energy table (kWh/yr)", expanded=False):
    _tbl_rows = []
    for fuel, ice in [("ECAV", False), ("ICECAV", True)]:
        for lvl in CAV_LEVEL_ORDER:
            av = _av_annual(lvl, "ecav", ice_factor=ice)
            tot = av["Sensing"] + av["Computing"] + av["Communication"]
            prop = float(prop_ice if ice else prop_bev)
            _tbl_rows.append({
                "Unit": f"{fuel} {lvl}",
                "Inventory key": CAV_LEVELS_CANONICAL[lvl],
                "Sensing (kWh/yr)": round(av["Sensing"], 1),
                "Computing (kWh/yr)": round(av["Computing"], 1),
                "Communication (kWh/yr)": round(av["Communication"], 1),
                "AV total (kWh/yr)": round(tot, 1),
                "Propulsion (kWh/yr)": round(prop, 0),
                "AV share of total": f"{100 * tot / (tot + prop):.1f}%",
            })
    for lvl in STI_LEVEL_ORDER:
        av = _av_annual(lvl, "sti")
        tot = av["Sensing"] + av["Computing"] + av["Communication"]
        _tbl_rows.append({
            "Unit": f"STI {lvl}",
            "Inventory key": STI_LEVELS_CANONICAL[lvl],
            "Sensing (kWh/yr)": round(av["Sensing"], 1),
            "Computing (kWh/yr)": round(av["Computing"], 1),
            "Communication (kWh/yr)": round(av["Communication"], 1),
            "AV total (kWh/yr)": round(tot, 1),
            "Propulsion (kWh/yr)": "—",
            "AV share of total": "100% (no propulsion)",
        })
    st.dataframe(pd.DataFrame(_tbl_rows), hide_index=True, width="stretch")
    st.caption(
        f"Computed at CAV duty = {_cav_hours:g} h/day, STI duty = 24 h/day, "
        "base-case scenario (moderate traffic, clear weather, daytime, edge "
        "compute). icecav_power_factor and propulsion as set above."
    )

# ── interpretation text ─────────────────────────────────────────────
st.subheader("Reading this page")
st.markdown("""
- **Propulsion dominates total vehicle energy.** At any autonomy level,
  combustion propulsion is by far the largest single block for a gasoline
  vehicle (autonomy stack ≈ 1-11 % of the total). Battery-electric
  propulsion is roughly one-quarter of the gasoline case, so the autonomy
  stack becomes a meaningfully larger share — about one-fifth of the total
  at L5.
- **AV-system share rises with autonomy.** Moving from L3 to L5 raises the
  AV-subsystem burden per unit by ~8×. Most of that growth is compute,
  because deployed perception-and-planning silicon scales with the autonomy
  level (Tesla-FSD-class at L3 → NVIDIA-DRIVE-Orin-class at L4 →
  NVIDIA-DRIVE-Thor-class at L5) **and** the compute-unit count doubles at L5.
- **Computing dominates the AV subsystem at L5, sensing at lower levels.**
  At L5 compute is ~70 % of the autonomy stack; at L3 sensing and compute
  are comparable. Communication is consistently the smallest share.
- **STI runs continuously, so its autonomy stack is roughly an order of
  magnitude larger than a vehicle's.** A highly-automated STI's annual
  autonomy energy is ~12-14× a L5 CAV's autonomy stack — driven by 24/7
  operation and an extensive on-road sensing inventory, not by per-agent
  inference inflation.
- **Electrification changes the relative burden structure.** A BEV L5
  vehicle's AV subsystem is roughly one-fifth of its propulsion, so
  targeting compute-efficiency improvements becomes a first-class
  decarbonization lever — but the autonomy stack does not, on its own,
  outweigh propulsion at any autonomy level.
""")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# (v10) Component registry — power sources & Monte-Carlo priors
# ═══════════════════════════════════════════════════════════════════
st.subheader("Component power registry (v10)")
st.caption(
    "Every per-component power range used above, with its evidence tier and "
    "the Monte-Carlo prior actually propagated on the Scenario Explorer. "
    "Triangular ranges for `vendor_estimate` / `assumption` components are "
    "widened (×1.25 / ×1.5) before sampling. Source notes are in "
    "`v10_streamlit_app/component_registry.py` and the step-08 audit memo."
)
_cr_rows = component_power_factor_rows()
st.dataframe(
    pd.DataFrame(_cr_rows)[[
        "Factor ID", "Factor name", "Subsystem", "Level / class",
        "Distribution / range", "Affected quantity", "Role in analysis",
    ]],
    hide_index=True, width="stretch",
)
with st.expander("Component source notes (evidence)", expanded=False):
    _src_rows = []
    for cid, op in OPERATIONAL.items():
        _src_rows.append({
            "Component": cid, "Subsystem": op.subsystem,
            "Evidence tier": op.evidence_tier,
            "Active fraction": op.active_fraction,
            "Utilization (by level)": "; ".join(f"{k}={v}" for k, v in op.utilization.items()),
            "Source / what to verify": op.source_note,
        })
    st.dataframe(pd.DataFrame(_src_rows), hide_index=True, width="stretch")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# Legacy read-only utility-phase ranges (kept from v9 for continuity)
# ═══════════════════════════════════════════════════════════════════
st.subheader("Legacy utility-phase factor ranges (v9 parameter registry)")
st.caption(
    "Retained from v9 for continuity. v10 supersedes the flat ECAV/STI "
    "subsystem load factors below with the bottom-up component registry shown "
    "above; the ICECAV conversion / overhead factor still applies."
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
        "Factors F32-F36 collapsed into one row per region. F32-F34 are "
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

st.markdown("---")
st.caption(
    "Data sources. AV-subsystem energy per level: `v10_streamlit_app/"
    "component_registry.py` (per-component deployed-silicon power × component "
    "counts from manuscript Extended Data Tables 3 & 4 × duty × utilization). "
    "Emission factors and the ICECAV overhead factor: `configs/<region>.json`. "
    "Propulsion baselines: FHWA Highway Statistics (VMT), EPA Automotive Trends "
    "Report (ICE mpg), EPA fuel-economy BEV kWh/mi. Propulsion values are "
    "editable above. Recalibration rationale and evidence tiers: "
    "`audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md`."
)
