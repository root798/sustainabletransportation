"""Utility Phase Energy — per-unit annual running energy.

This page shows annual running energy at the **unit** level: how much energy
one vehicle (or one roadside infrastructure asset) consumes per year, split
into propulsion and the AV subsystems.

New Edit
-----------------
It restores that experiment-based path for the **computing** subsystem
while preserving the v10 component-registry path for **sensing** and
**communication** — which is what Methods §4.1.3 actually requires (those
baselines come from product specifications, not from live experiments).

Concretely, in this page:
  * Sensing and communication energies come from the v10 component registry
    (``component_registry.py``: per-component power × counts × duty ×
    utilization).
  * Computing energy comes from
    ``experiment_computing_baseline.py`` — manuscript Extended Data Tables
    5 and 8, with the Jetson Orin (edge) column as the personal-use default
    and the A100 (cloud) column available as a sensitivity.
  * The "propulsion back-solve" of earlier versions is still removed: the
    propulsion bar is the user-supplied value.

Layout, plot types, colours, captions, and column order are unchanged from v9.

See ``audits/step_09_manuscript_method_alignment/`` for the alignment audit.
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
from experiment_computing_baseline import (  # noqa: E402
    CAV_COMPUTING_BASELINE_KWH, STI_COMPUTING_BASELINE_KWH,
    DEFAULT_CAV_PLATFORM, DEFAULT_STI_ARCHITECTURE,
)
from utils.plotly_layout import (  # noqa: E402
    apply_clearats_layout, page_top_spacing,
)
from utils.df_display import prepare_for_streamlit  # noqa: E402

REPO_ROOT = APP_DIR.parent

st.set_page_config(page_title="Utility Phase Energy", page_icon="C", layout="wide")

# Page-top breathing room (shared CSS block, see utils.plotly_layout).
st.markdown(page_top_spacing(), unsafe_allow_html=True)

st.title("Utility Phase Energy")
st.caption(
    "Annual running energy at the unit level. How much energy does one "
    "vehicle (or one roadside infrastructure asset) consume per year, "
    "and how does that energy divide between propulsion and the AV "
    "subsystems? State-scale evolution, regional comparisons, and "
    "uncertainty controls are on the Scenario Explorer page."
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


# ── bottom-up AV subsystem energy ──────────────────────────────
# Component registry → per-unit {Sensing, Computing, Communication} kWh/yr.
# Region does NOT enter here: per-unit hardware power is region-independent in
# the manuscript's Table 5 / Table 8 (region only changes the grid emission
# factor and fleet sizes — handled on the Scenario Explorer page).
@st.cache_data(show_spinner=False)
def _registry_subsystem_table(
    cav_hours: float,
    cav_compute_platform: str = DEFAULT_CAV_PLATFORM,
    sti_compute_architecture: str = DEFAULT_STI_ARCHITECTURE,
) -> Dict[str, Dict[str, Dict[str, float]]]:
    model = ComponentRegistryEnergyModel(
        cav_hours=cav_hours,
        cav_compute_platform=cav_compute_platform,
        sti_compute_architecture=sti_compute_architecture,
    )
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
    cav_platform_label = st.radio(
        "CAV compute platform (Methods §4.1.3 testbed)",
        ["Edge — Jetson Orin (default)",
         "Cloud — A100 (sensitivity)"],
        index=0, horizontal=True,
        help=(
            "Switches the *computing* row of Extended Data Table 5 between the "
            "two manuscript columns. Edge = Jetson Orin (on-vehicle deployment); "
            "Cloud = A100 (cloud-assisted reference). Sensing and communication "
            "energies are unaffected; they continue to come from the v10 "
            "component registry."
        ),
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
_cav_platform = "edge" if cav_platform_label.startswith("Edge") else "cloud"
_subsys = _registry_subsystem_table(
    _cav_hours,
    cav_compute_platform=_cav_platform,
    sti_compute_architecture=DEFAULT_STI_ARCHITECTURE,
)


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
    "vehicles. (propulsion is the value entered above — not "
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

_max_x_fig1 = float((unit_df["Total"] / 1000.0).max())
apply_clearats_layout(
    fig1,
    kind="hbar",
    num_rows=len(unit_df),
    x_title="MWh / yr",
    max_x=_max_x_fig1,
    barmode="stack",
)
fig1.update_layout(
    title=dict(
        text="<b>Annual running energy per vehicle, by propulsion and autonomy level</b>",
        x=0.0, xanchor="left",
        font=dict(size=14, color=NATURE_CATEGORICAL["neutral"]),
    ),
)
fig1.update_yaxes(autorange="reversed")
st.plotly_chart(fig1, width="stretch",
                config={"displaylogo": False})

st.caption(
    "Bars separate propulsion, computing, sensing and communication; AV shares "
    "reflect the selected duty cycle and compute platform. Underlying inputs "
    "are assembled bottom-up and are not fitted to a target."
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
    _max_x = float((df["Total"] / 1000.0).max()) if len(df) else 1.0
    apply_clearats_layout(
        fig,
        kind="hbar",
        num_rows=len(df),
        x_title="MWh / yr",
        max_x=_max_x,
        barmode="stack",
        height=height,
    )
    fig.update_layout(title=dict(
        text=title_text, x=0.0, xanchor="left",
        font=dict(size=13, color=NATURE_CATEGORICAL["neutral"]),
    ))
    fig.update_yaxes(autorange="reversed")
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
                "Sensing (kWh/yr)":       float(av["Sensing"]),
                "Computing (kWh/yr)":     float(av["Computing"]),
                "Communication (kWh/yr)": float(av["Communication"]),
                "AV total (kWh/yr)":      float(tot),
                "Propulsion (kWh/yr)":    float(prop),
                "AV share of total":      f"{100 * tot / (tot + prop):.1f}%",
            })
    for lvl in STI_LEVEL_ORDER:
        av = _av_annual(lvl, "sti")
        tot = av["Sensing"] + av["Computing"] + av["Communication"]
        _tbl_rows.append({
            "Unit": f"STI {lvl}",
            "Inventory key": STI_LEVELS_CANONICAL[lvl],
            "Sensing (kWh/yr)":       float(av["Sensing"]),
            "Computing (kWh/yr)":     float(av["Computing"]),
            "Communication (kWh/yr)": float(av["Communication"]),
            "AV total (kWh/yr)":      float(tot),
            # STI has no propulsion. Pass NaN (not '—') so the column has
            # a single numeric dtype that Arrow accepts; the em-dash is
            # restored on screen by the Styler-aware helper below.
            "Propulsion (kWh/yr)":    float("nan"),
            "AV share of total":      "100% (no propulsion)",
        })
    _unit_table_df = pd.DataFrame(_tbl_rows)
    _unit_numeric_cols = [
        "Sensing (kWh/yr)", "Computing (kWh/yr)",
        "Communication (kWh/yr)", "AV total (kWh/yr)",
        "Propulsion (kWh/yr)",
    ]
    st.dataframe(
        prepare_for_streamlit(
            _unit_table_df, numeric_cols=_unit_numeric_cols,
        ).style.format(
            {c: (lambda v: "—" if pd.isna(v) else f"{v:,.1f}")
             for c in _unit_numeric_cols},
            na_rep="—",
        ),
        hide_index=True, width="stretch",
    )
    st.caption(
        f"Computed at CAV duty = {_cav_hours:g} h/day, STI duty = 24 h/day, "
        "base-case scenario (moderate traffic, clear weather, daytime, edge "
        "compute). icecav_power_factor and propulsion as set above."
    )

# ── interpretation text ─────────────────────────────────────────────
with st.expander("Interpretation and key takeaways", expanded=False):
    st.markdown("""
- **The propulsion/AV split is control-dependent.** Propulsion uses the values
  entered above; the AV-system total responds to autonomy level, duty cycle,
  compute platform and the configured ICECAV overhead factor. Figure 1 reports
  the resulting share for every bar rather than assuming one component always
  dominates.
- **AV-system demand rises with autonomy.** The experiment-based computing
  baseline and component inventory both vary by autonomy level. Selecting the
  cloud platform changes computing demand; selecting robotaxi duty changes the
  duty-scaled sensing and communication loads.
- **Computing is the largest AV-subsystem contribution at higher autonomy
  levels under the displayed baseline.** Communication remains the smallest
  contribution; exact shares are shown in the figure and per-unit table.
- **STI and CAV values use different operating assumptions.** STI runs
  continuously, while CAV duty is selected above; the STI architecture and
  its on-road sensing inventory also differ from the vehicle model.
- **Electrification changes the relative burden structure.** The lower BEV
  propulsion baseline makes the same AV-system demand a larger fraction of
  the vehicle total. Depending on autonomy level and selected controls, that
  fraction can be smaller or larger than propulsion.
""")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# Component registry & experiment baseline — power sources / Monte-Carlo priors
# ═══════════════════════════════════════════════════════════════════
st.subheader("Component power registry")
st.caption(
    "Every per-component power range used above, with its evidence tier and "
    "the Monte-Carlo prior actually propagated on the Scenario Explorer. "
    "Triangular ranges for `vendor_estimate` / `assumption` components are "
    "widened (×1.25 / ×1.5) before sampling. "
)
_cr_rows = component_power_factor_rows()
st.dataframe(
    prepare_for_streamlit(pd.DataFrame(_cr_rows)[[
        "Factor ID", "Factor name", "Subsystem", "Level / class",
        "Distribution / range", "Affected quantity", "Role in analysis",
    ]]),
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
    st.dataframe(prepare_for_streamlit(pd.DataFrame(_src_rows)),
                 hide_index=True, width="stretch")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# Legacy read-only utility-phase ranges (kept from v9 for continuity)
# ═══════════════════════════════════════════════════════════════════
st.subheader("Legacy utility-phase factor ranges (v9 parameter registry)")
st.caption(
    "It supersedes the flat ECAV/STI "
    "subsystem load factors below with the experiment-based computing "
    "baseline (Extended Data Tables 5 and 8) and the bottom-up sensing / "
    "communication registry shown above; the ICECAV conversion / overhead "
    "factor still applies."
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
        prepare_for_streamlit(pd.DataFrame(_group_rows)[[
            "Factor ID",
            "Factor name",
            "Layer / class",
            "Distribution / range",
            "Affected quantity",
            "Role in analysis",
        ]]),
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
        prepare_for_streamlit(pd.DataFrame(_WX_ROWS)[[
            "Region",
            "Clear share",
            "Cloudy share",
            "Adverse share",
            "Weather-share concentration",
            "Grid-side CO₂ weather sensitivity",
            "Role in analysis",
        ]]),
        hide_index=True,
        width="stretch",
    )

st.markdown("---")
with st.expander("Data sources and model lineage", expanded=False):
    st.caption(
        "AV-subsystem energy per level: `v11_streamlit_app/"
        "component_registry.py` (per-component deployed-silicon power × component "
        "counts from manuscript Extended Data Tables 3 & 4 × duty × utilization). "
        "Emission factors and the ICECAV overhead factor: `configs/<region>.json`. "
        "Propulsion baselines: FHWA Highway Statistics (VMT), EPA Automotive Trends "
        "Report (ICE mpg), EPA fuel-economy BEV kWh/mi. Propulsion values are "
        "editable above. Recalibration rationale and evidence tiers: "
        "`audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md`."
    )
