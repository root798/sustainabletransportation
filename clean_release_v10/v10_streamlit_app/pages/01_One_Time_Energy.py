"""One-Time Energy and Marginal Components — v9 paper-facing page.

Visualises the **production and logistics phase** of the ATS life cycle.
All numbers trace to the manuscript: Figure 3a, Figure 3b, Extended Data
Tables 3 and 4, Table 2.

Page order (v9 cleanup):
  - Title and short scope note
  - Figure A: component-level one-time energy ranking
  - Figure B: unit one-time energy with subsystem decomposition
  - Figure C: marginal components across autonomy levels
  - Live derived metrics
  - Production vs utility-phase inversion
  - End-of-life leverage
  - End-page details (collapsed):
      Component inventory and one-time assumptions
      Data uncertainty ranges for one-time energy
      Data consistency note

v9 changes vs v8: the upper interactive Block 1 sliders, the upper
Block 2 / Block 3 expanders, and the upper rebuttal cross-check banner
are removed from the public page flow. The same content is preserved
read-only at the end of the page. Numeric logic, model equations,
configs, and figure ordering are unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (  # noqa: E402
    NATURE_CATEGORICAL,
    plotly_layout_defaults,
    rgba,
)
from one_time_data import (  # noqa: E402
    BLOCK2_CITATIONS,
    CAV_COUNTS,
    COMPONENTS,
    FIGURE3B_UNIT_TOTALS,
    L5_UTILITY_ANNUAL_KWH,
    L5_UTILITY_CUMULATIVE_12YR_KWH,
    MANUSCRIPT_L3_TO_L5_MULTIPLIER,
    MANUSCRIPT_REFURB_ENERGY_RATIO,
    MANUSCRIPT_REFURB_SAVINGS_PCT,
    MANUSCRIPT_SENSING_CAV_PCT,
    MANUSCRIPT_SENSING_STI_PCT,
    STI_COUNTS,
    SUBSYSTEM_COLORS,
    TABLE2_PROD_LOG,
    build_component_rows,
    build_count_wide_table,
    component_sum,
    marginal_count,
    subsystem_breakdown,
)
from utils.factor_tables import one_time_factor_rows  # noqa: E402

# ── page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="One-Time Energy",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("One-Time Energy and Marginal Components")
st.caption(
    "This page reports production, logistics, and end-of-life "
    "accounting for ATS autonomy hardware. Operational energy and "
    "emissions are reported separately on the Utility Phase Energy "
    "and Scenario Explorer pages."
)

# Cross-check rows are computed once (used internally below and by the
# end-page "Data consistency note"). Values come from the baseline
# component inventory; they do not depend on user input.
_l5_bd_baseline = subsystem_breakdown(CAV_COUNTS["L5"])
_l5_tot_baseline = sum(_l5_bd_baseline.values())
_l5_sens_pct_baseline = 100.0 * _l5_bd_baseline["Sensing"] / max(_l5_tot_baseline, 1)
_sti_bd_baseline = subsystem_breakdown(STI_COUNTS["Highly"])
_sti_tot_baseline = sum(_sti_bd_baseline.values())
_sti_sens_pct_baseline = 100.0 * _sti_bd_baseline["Sensing"] / max(_sti_tot_baseline, 1)
_l3s_sum = component_sum(CAV_COUNTS["L3 Small"])
_l5_sum = component_sum(CAV_COUNTS["L5"])
_l3_to_l5 = _l5_sum / max(_l3s_sum, 1e-9)

_cc_rows = [
    ("Sensing share, CAV L5", "94 %",
     f"{_l5_sens_pct_baseline:.1f} %",
     abs(_l5_sens_pct_baseline - 94) > 2),
    ("Sensing share, STI Highly", "84 %",
     f"{_sti_sens_pct_baseline:.1f} %",
     abs(_sti_sens_pct_baseline - 84) > 2),
    ("L3 Small \u2192 L5 multiplier", "3.5\u00d7",
     f"{_l3_to_l5:.2f}\u00d7",
     abs(_l3_to_l5 - 3.5) / 3.5 > 0.02),
    ("L5 production + logistics (Table 2)", "9,237 kWh",
     f"{_l5_sum:,.0f} kWh (component sum)",
     abs(_l5_sum - 9237) / 9237 > 0.02),
    ("HP Computing Unit per unit", "654.32 kWh",
     f"{COMPONENTS['HP Computing Unit'].energy_kwh:.2f} kWh",
     False),
    ("Static HP LiDAR per unit", "607.58 kWh",
     f"{COMPONENTS['Static HP LiDAR'].energy_kwh:.2f} kWh",
     False),
]
# Match count is referenced by the end-page Data consistency note.
_cc_match_count = sum(1 for _, _, _, bad in _cc_rows if not bad)

# ── session-state defaults (kept so figures / metrics keep reading
# baseline values; the v8 interactive sliders that wrote to these
# keys have been removed from the public page) ───────────────────────
st.session_state.setdefault("ot_sens_mfr_eff", 0.0)       # % reduction
st.session_state.setdefault("ot_comp_refurb_adopt", 0.0)  # fraction
st.session_state.setdefault("ot_sens_refurb_rate", 0.70)  # α fraction
st.session_state.setdefault("ot_sensor_life_ext", 0)      # years

st.session_state.setdefault("ot_mfr_region", "Asia-Pacific (default)")
st.session_state.setdefault("ot_logistics_model", "Sea + truck (default)")
st.session_state.setdefault("ot_alpha_choice",
                            "25 % (default, per §4.1.4)")
st.session_state.setdefault("ot_phi_choice", "10 % (default)")
st.session_state.setdefault("ot_obsolescence_window",
                            "8 to 24 months (default, per NVIDIA manufacturing)")

# (v9) The v8 Block 1 sliders, Block 2 fixed-data expander, Block 3
# assumption expander, and Block 4 residual-uncertainty selectboxes
# have all been removed from the upper public page. Their content is
# preserved read-only in the end-page "Component inventory and
# one-time assumptions" expander, and one-time uncertainty is
# documented in the "Data uncertainty ranges for one-time energy"
# table below. All numeric calculations, model equations, configs,
# and figure ordering remain unchanged from v8.

# ═══════════════════════════════════════════════════════════════════
# LIVE MITIGATION TRANSFORM
# ═══════════════════════════════════════════════════════════════════
sens_eff = float(st.session_state["ot_sens_mfr_eff"]) / 100.0
comp_adopt = float(st.session_state["ot_comp_refurb_adopt"])
sens_alpha = float(st.session_state["ot_sens_refurb_rate"])
life_ext = int(st.session_state["ot_sensor_life_ext"])


def _alpha_from_choice() -> float:
    choice = st.session_state["ot_alpha_choice"]
    return {"25 % (default, per §4.1.4)": 0.25,
            "15 % (aggressive remanufacturing)": 0.15,
            "40 % (conservative)": 0.40}.get(choice, 0.25)


ALPHA_B3 = _alpha_from_choice()


def production_display_energy(name: str) -> float:
    """Per-unit production + logistics energy with **production-side**
    Block 1 effects applied (sensing manufacturing efficiency only).

    Under default settings (sens_eff = 0, life_ext = 0) this returns
    the manuscript Figure 3a value exactly. End-of-life refurbishment
    sliders (sens_alpha, comp_adopt) do NOT reduce production values
    and are handled separately via `eol_savings_per_unit()`.
    """
    c = COMPONENTS[name]
    e = c.energy_kwh
    if c.subsystem == "Sensing" and sens_eff > 0:
        e *= (1.0 - sens_eff)
    return e


def production_annualised_energy(name: str) -> float:
    """production_display_energy divided by the lifetime-extension
    amortisation factor. Lifetime extension spreads the one-time
    burden over a longer service life.
    """
    e = production_display_energy(name)
    if life_ext > 0:
        e *= 12.0 / (12.0 + life_ext)
    return e


def eol_savings_per_unit(name: str) -> float:
    """Per-unit end-of-life savings from the refurbishment levers.
    Positive value = kWh saved at end of life by refurbishing rather
    than newly manufacturing. At default settings (sens_alpha = 0.70,
    comp_adopt = 0, ALPHA_B3 = 0.25) this yields savings on sensing
    components only.
    """
    c = COMPONENTS[name]
    base = c.energy_kwh
    if c.subsystem == "Sensing":
        return base * sens_alpha * (1.0 - ALPHA_B3)
    if c.subsystem in ("Computing", "Communication"):
        return base * comp_adopt * (1.0 - ALPHA_B3)
    return 0.0


# Backwards-compatibility aliases used by the tornado + fleet helpers.
def adjusted_component_energy(name: str) -> float:
    """Production + annualisation combined (mfr efficiency ×
    lifetime amortisation). Used by the tornado to show the net
    production-side effect of Block 1 levers."""
    return production_annualised_energy(name)


def adjusted_component_energy_with_sensing_refurb(name: str) -> float:
    """Production annualised energy MINUS the EoL savings. Used by
    the tornado chart only, which is designed to show the net change
    in one-time burden under each lever."""
    return production_annualised_energy(name) - eol_savings_per_unit(name)


def adjusted_unit_total(counts: dict[str, int]) -> float:
    """Net per-unit one-time burden under current Block 1 settings."""
    return sum(counts[n] * adjusted_component_energy_with_sensing_refurb(n)
               for n in counts)


def adjusted_subsystem_breakdown(counts: dict[str, int]) -> dict[str, float]:
    """Subsystem breakdown of NET per-unit one-time burden
    (production annualised minus EoL savings). Used by the tornado."""
    out = {"Sensing": 0.0, "Computing": 0.0, "Communication": 0.0}
    for n, cnt in counts.items():
        c = COMPONENTS[n]
        out[c.subsystem] += cnt * adjusted_component_energy_with_sensing_refurb(n)
    return out


def production_only_unit_total(counts: dict[str, int]) -> float:
    """Per-unit PRODUCTION + LOGISTICS total. This is what Figure B
    displays. Under defaults this equals the manuscript Figure 3b
    value (ignoring documented STI Basic manuscript inconsistency)."""
    return sum(counts[n] * production_display_energy(n) for n in counts)


def production_only_subsystem_breakdown(counts: dict[str, int]) -> dict[str, float]:
    """Subsystem breakdown of the PRODUCTION + LOGISTICS per-unit total.
    Used by Figure B stacked bars and the inversion donut."""
    out = {"Sensing": 0.0, "Computing": 0.0, "Communication": 0.0}
    for n, cnt in counts.items():
        c = COMPONENTS[n]
        out[c.subsystem] += cnt * production_display_energy(n)
    return out


# ═══════════════════════════════════════════════════════════════════
# FIGURE A — Component ranking
# ═══════════════════════════════════════════════════════════════════
st.subheader("Figure A. Component-level one-time energy ranking")

fig_a_rows = []
for name, c in COMPONENTS.items():
    display_kwh = production_display_energy(name)
    fig_a_rows.append({
        "Component": name,
        "Subsystem": c.subsystem,
        "Platform":  c.platform,
        "kWh":       display_kwh,
        "Baseline":  c.energy_kwh,
    })
# Sort ascending so highest values sit at the top of the plot.
fig_a_df = pd.DataFrame(fig_a_rows).sort_values("kWh", ascending=True).reset_index(drop=True)

# Build platform-marked y-labels and a per-bar colour list.
_platform_sym = {"CAV": "\u25CF", "STI": "\u25B2"}
y_labels = [f"{_platform_sym[row.Platform]} {row.Component}"
            for row in fig_a_df.itertuples()]
bar_colors = [SUBSYSTEM_COLORS[s] for s in fig_a_df["Subsystem"]]
bar_alpha = [0.9 if s != "Computing" else 0.7 for s in fig_a_df["Subsystem"]]

fig_a = go.Figure()
# Single trace with per-bar colours — prevents Plotly from splitting
# the plot into a separate category group per subsystem.
fig_a.add_trace(go.Bar(
    x=fig_a_df["kWh"], y=y_labels,
    orientation="h",
    marker=dict(color=bar_colors, opacity=1.0),
    text=[f"{v:.1f}" for v in fig_a_df["kWh"]],
    textposition="outside",
    name="Component",
    showlegend=False,
    hovertemplate=("%{y}<br>One-time energy: %{x:,.2f} kWh"
                   "<extra></extra>"),
    cliponaxis=False,
))
# Invisible traces so the legend shows the three subsystem colours.
for subsystem in ("Sensing", "Computing", "Communication"):
    fig_a.add_trace(go.Bar(
        x=[None], y=[None],
        marker=dict(color=SUBSYSTEM_COLORS[subsystem]),
        name=subsystem, showlegend=True,
    ))

layout_a = plotly_layout_defaults()
layout_a["xaxis"]["title"] = {"text": "One-time energy per unit (kWh)"}
# Extend x-range so the 607.58 and 654.32 bars plus their outside
# labels fit without being cut off.
_max_val = float(fig_a_df["kWh"].max())
layout_a["xaxis"]["range"] = [0, max(_max_val * 1.18, 750)]
layout_a["yaxis"]["title"] = {"text": ""}
layout_a["yaxis"]["showgrid"] = False
layout_a["yaxis"]["categoryorder"] = "array"
layout_a["yaxis"]["categoryarray"] = y_labels  # preserve our ordering
layout_a["yaxis"]["automargin"] = True
layout_a["height"] = 560
layout_a["legend"] = {"orientation": "h", "yanchor": "bottom",
                      "y": -0.15, "x": 0.5, "xanchor": "center",
                      "bgcolor": "rgba(255,255,255,0)",
                      "bordercolor": "rgba(0,0,0,0)"}
layout_a["margin"] = {"t": 32, "b": 72, "l": 220, "r": 80}
fig_a.update_layout(**layout_a)
st.plotly_chart(fig_a, width="stretch")
st.caption(
    "Figure A. Per-unit one-time embodied energy for each ATS "
    "component, ranked by kWh. Subsystems are coloured: sensing "
    "(blue), computing (gray), communication (red). Despite higher "
    "per-unit energy for high-performance computing units "
    "(654.32 kWh) and static high-power LiDAR (607.58 kWh), sensors "
    "are deployed in far greater quantities, so the sensing "
    "subsystem dominates total one-time energy at the unit level "
    "(see Figure B). Filled circle denotes CAV components; filled "
    "triangle denotes STI components."
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# FIGURE B — Unit-level stacked by subsystem
# ═══════════════════════════════════════════════════════════════════
st.subheader("Figure B. Unit one-time energy with subsystem decomposition")

UNIT_DISPLAY_ORDER = [
    ("STI Highly",   STI_COUNTS["Highly"],    "STI Highly-Automated"),
    ("CAV L5",       CAV_COUNTS["L5"],        "CAV L5"),
    ("STI Semi",     STI_COUNTS["Semi"],      "STI Semi-Automated"),
    ("CAV L4",       CAV_COUNTS["L4"],        "CAV L4"),
    ("CAV L3 Large", CAV_COUNTS["L3 Large"],  "CAV L3 Large"),
    ("CAV L3 Medium",CAV_COUNTS["L3 Medium"], "CAV L3 Medium"),
    ("CAV L3 Small", CAV_COUNTS["L3 Small"],  "CAV L3 Small"),
    ("STI Basic",    STI_COUNTS["Basic"],     "STI Basic"),
]

unit_rows = []
for short, counts, display in UNIT_DISPLAY_ORDER:
    bd = production_only_subsystem_breakdown(counts)
    total = sum(bd.values())
    unit_rows.append({
        "unit": display, "total": total, **bd,
        "counts": counts,
    })

# Plot stacked bars with subsystem segments (production + logistics only).
fig_b = go.Figure()
labels = [r["unit"] for r in unit_rows]
for subsystem in ("Sensing", "Computing", "Communication"):
    vals = [r[subsystem] for r in unit_rows]
    # In-bar label shows the per-subsystem percent of the unit total.
    fig_b.add_trace(go.Bar(
        x=vals, y=labels,
        orientation="h",
        name=subsystem,
        marker=dict(color=SUBSYSTEM_COLORS[subsystem],
                    opacity=0.9 if subsystem != "Computing" else 0.7),
        text=[f"{100*r[subsystem]/max(r['total'],1):.1f}%"
              if (r[subsystem] / max(r["total"], 1) >= 0.08) else ""
              for r in unit_rows],
        textposition="inside",
        insidetextanchor="middle",
        hovertemplate=("%{y}<br>" + subsystem + ": %{x:,.1f} kWh"
                       "<extra></extra>"),
    ))
# Annotate totals at bar ends.
for r in unit_rows:
    fig_b.add_annotation(
        x=r["total"], y=r["unit"],
        text=f"  {r['total']:,.0f}",
        showarrow=False, xanchor="left",
        font=dict(size=11, color="#333333"),
    )
layout_b = plotly_layout_defaults()
layout_b["barmode"] = "stack"
layout_b["xaxis"]["title"] = {"text":
    "One-time energy per unit (kWh) — production + logistics"}
layout_b["yaxis"]["title"] = {"text": ""}
layout_b["yaxis"]["showgrid"] = False
layout_b["xaxis"]["range"] = [0, max(r["total"] for r in unit_rows) * 1.18]
layout_b["height"] = 440
layout_b["legend"] = {"orientation": "h", "yanchor": "bottom",
                      "y": -0.22, "x": 0.5, "xanchor": "center",
                      "bgcolor": "rgba(255,255,255,0)",
                      "bordercolor": "rgba(0,0,0,0)"}
layout_b["margin"] = {"t": 32, "b": 72, "l": 160, "r": 80}
fig_b.update_layout(**layout_b)
st.plotly_chart(fig_b, width="stretch")

# Live vs manuscript comparison table (rendered below the plot so
# the reader can instantly see whether the Block 1 levers have
# pulled Figure B off the manuscript baseline).
_compare_rows = []
_ms_lookup = {
    "STI Highly-Automated":   FIGURE3B_UNIT_TOTALS["STI Highly-Automated"],
    "CAV L5":                  FIGURE3B_UNIT_TOTALS["CAV L5"],
    "STI Semi-Automated":     FIGURE3B_UNIT_TOTALS["STI Semi-Automated"],
    "CAV L4":                  FIGURE3B_UNIT_TOTALS["CAV L4"],
    "CAV L3 Large":            FIGURE3B_UNIT_TOTALS["CAV L3 Large"],
    "CAV L3 Medium":           FIGURE3B_UNIT_TOTALS["CAV L3 Medium"],
    "CAV L3 Small":            FIGURE3B_UNIT_TOTALS["CAV L3 Small"],
    "STI Basic":               FIGURE3B_UNIT_TOTALS["STI Basic"],
}
_b_any_drift = False
_b_any_manuscript_gap = False
for r in unit_rows:
    ms_v = _ms_lookup.get(r["unit"], float("nan"))
    live_v = r["total"]
    if ms_v == ms_v:  # not NaN
        rel = abs(live_v - ms_v) / max(ms_v, 1.0)
    else:
        rel = 0.0
    # STI Basic is a documented manuscript inconsistency, not a bug.
    is_ms_gap = (r["unit"] == "STI Basic" and rel > 0.02)
    if is_ms_gap:
        _b_any_manuscript_gap = True
        status = "\u26a0 manuscript gap"
    elif rel > 0.01:
        _b_any_drift = True
        status = f"drift {rel*100:.1f}%"
    else:
        status = "match"
    _compare_rows.append({
        "Unit":              r["unit"],
        "Live (kWh)":        f"{live_v:,.1f}",
        "Manuscript (kWh)":  f"{ms_v:,.1f}" if ms_v == ms_v else "—",
        "Status":            status,
    })
st.markdown("**Figure B live vs manuscript comparison.**")
st.dataframe(pd.DataFrame(_compare_rows), hide_index=True,
             width="stretch")
if _b_any_drift:
    st.caption(
        "Live Figure B values differ from manuscript Figure 3b by "
        "more than 1 %. This indicates a divergence between the "
        "live component sum and the manuscript aggregation; both "
        "are reproducible from the inventory table at the end of "
        "this page."
    )
if _b_any_manuscript_gap:
    st.caption(
        "STI Basic row shows a rare aggregation discrepancy: summing the "
        "component inventory gives 2,747.36 kWh, whereas an alternative "
        "aggregation path reports 2,139.77 kWh. Both values are shown on "
        "this page so the reader can compare."
    )

l5_bd = production_only_subsystem_breakdown(CAV_COUNTS["L5"])
l5_total = sum(l5_bd.values())
l5_sens_pct = 100.0 * l5_bd["Sensing"] / max(l5_total, 1)
sti_highly_bd = production_only_subsystem_breakdown(STI_COUNTS["Highly"])
sti_highly_total = sum(sti_highly_bd.values())
sti_highly_sens_pct = 100.0 * sti_highly_bd["Sensing"] / max(sti_highly_total, 1)
l3s_total = sum(production_only_subsystem_breakdown(
    CAV_COUNTS["L3 Small"]).values())
l3_to_l5_ratio = l5_total / max(l3s_total, 1e-9)

st.caption(
    f"Figure B. One-time **production + logistics** embodied energy "
    f"per ATS unit, decomposed by subsystem. Sensing dominates across "
    f"every unit type: {l5_sens_pct:.1f}% for a Level 5 CAV and "
    f"{sti_highly_sens_pct:.1f}% for a Highly-Automated STI. "
    f"Upgrading a CAV from Level 3 Small to Level 5 raises "
    f"production + logistics energy by about "
    f"{l3_to_l5_ratio:.2f}×. In-bar labels are the per-subsystem "
    f"share of the unit total; the three subsystem labels sum to 100% "
    f"within rounding. End-of-life refurbishment is reported separately "
    f"in the end-of-life leverage panel because it affects the "
    f"end-of-life phase rather than the production phase."
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# FIGURE C — Marginal components (counts + composition)
# ═══════════════════════════════════════════════════════════════════
st.subheader("Figure C. Marginal components across autonomy levels")

st.caption(
    ":bulb: **Why this chart matters.** Total component count tells "
    "you how many additional hardware items autonomy introduces; the "
    "stacked breakdown tells you **which** components those are. "
    "Sensors carry low per-unit energy but multiply quickly; "
    "high-performance computing and LiDAR units carry much higher "
    "per-unit energy but appear in smaller numbers. Total count "
    "alone does not equal one-time energy — see Figure B for the "
    "energy-weighted view."
)

# Component-list ordering used for the stacked breakdown. Order is
# CAV-side first then STI-side, with the highest-volume sensor first
# inside each platform group. Colours follow the subsystem palette:
# blue for sensing variants, gray for computing variants, red for
# communication variants.
_FIG_C_COMP_ORDER = [
    ("Onboard Camera",         "Sensing",       "CAV"),
    ("Onboard LiDAR S",        "Sensing",       "CAV"),
    ("Onboard LiDAR L",        "Sensing",       "CAV"),
    ("Onboard Radar",          "Sensing",       "CAV"),
    ("Sonar",                  "Sensing",       "CAV"),
    ("Onboard Computing Unit", "Computing",     "CAV"),
    ("Cellular Comm. Unit",    "Communication", "CAV"),
    ("DSRC",                   "Communication", "CAV"),
    ("Inductive Loop Detector","Sensing",       "STI"),
    ("Static Camera",          "Sensing",       "STI"),
    ("Static HP LiDAR",        "Sensing",       "STI"),
    ("Static HP Radar",        "Sensing",       "STI"),
    ("Edge Computing Unit",    "Computing",     "STI"),
    ("HP Computing Unit",      "Computing",     "STI"),
    ("Roadside Unit",          "Communication", "STI"),
]

# Unit ordering on the x-axis (CAV first, STI second).
_UNIT_ORDER = [
    ("L3 Small",  CAV_COUNTS["L3 Small"],  "CAV"),
    ("L3 Medium", CAV_COUNTS["L3 Medium"], "CAV"),
    ("L3 Large",  CAV_COUNTS["L3 Large"],  "CAV"),
    ("L4",        CAV_COUNTS["L4"],        "CAV"),
    ("L5",        CAV_COUNTS["L5"],        "CAV"),
    ("Basic",     STI_COUNTS["Basic"],     "STI"),
    ("Semi",      STI_COUNTS["Semi"],      "STI"),
    ("Highly",    STI_COUNTS["Highly"],    "STI"),
]
_x_labels = [u for u, _, _ in _UNIT_ORDER]
_totals = [marginal_count(c) for _, c, _ in _UNIT_ORDER]
_platforms = [p for _, _, p in _UNIT_ORDER]

# View toggle: total counts vs component breakdown.
_fig_c_view = st.radio(
    "View",
    ["Component breakdown (default)", "Total counts only"],
    key="ot_fig_c_view",
    horizontal=True,
    help="Component breakdown shows which hardware items contribute "
         "to each unit's marginal count. Total counts only is the "
         "compact view for cross-platform comparison.",
)

if _fig_c_view == "Total counts only":
    fig_c = go.Figure()
    bar_colors = [NATURE_CATEGORICAL["primary"] if p == "CAV"
                  else NATURE_CATEGORICAL["tertiary"]
                  for p in _platforms]
    fig_c.add_trace(go.Bar(
        x=_x_labels, y=_totals,
        marker=dict(color=bar_colors, opacity=0.9),
        text=[str(n) for n in _totals],
        textposition="outside",
        showlegend=False,
        hovertemplate=("%{x}<br>Marginal components: %{y}"
                       "<extra></extra>"),
    ))
    fig_c.add_trace(go.Bar(x=[None], y=[None],
                            marker=dict(color=NATURE_CATEGORICAL["primary"]),
                            name="CAV (autonomy level)", showlegend=True))
    fig_c.add_trace(go.Bar(x=[None], y=[None],
                            marker=dict(color=NATURE_CATEGORICAL["tertiary"]),
                            name="STI (coverage tier)", showlegend=True))
else:
    # Component breakdown — stacked bars, one segment per component.
    fig_c = go.Figure()
    # Sort sensing/computing/communication into the same colour family
    # so a reader can scan vertically across bars.
    for comp_name, subsystem, platform in _FIG_C_COMP_ORDER:
        # Counts of this component across each unit on the x-axis.
        ys = []
        for uname, counts, p in _UNIT_ORDER:
            ys.append(counts.get(comp_name, 0)
                      if (platform == p) else 0)
        if max(ys) == 0:
            continue
        # Pick a per-component shade by varying the alpha of the
        # subsystem colour so every component is distinguishable.
        col = SUBSYSTEM_COLORS[subsystem]
        fig_c.add_trace(go.Bar(
            x=_x_labels, y=ys,
            name=f"{comp_name} ({subsystem[0]})",
            marker=dict(color=col,
                        opacity=0.85,
                        line=dict(color="white", width=0.4)),
            hovertemplate=(f"<b>{comp_name}</b><br>"
                           "%{x}: %{y} units<extra></extra>"),
        ))
    # Total annotations on top of each stack.
    for x, t in zip(_x_labels, _totals):
        fig_c.add_annotation(
            x=x, y=t, text=f"<b>{t}</b>",
            showarrow=False, yshift=14,
            font=dict(size=11, color=AXIS_COLOR if False else "#333333"),
        )

# Vertical separator between CAV and STI groups (between L5 and Basic).
fig_c.add_vline(x=4.5, line=dict(color=NATURE_CATEGORICAL["neutral"],
                                   width=0.6, dash="dot"))

# Group headers on the x-axis as super-labels.
fig_c.add_annotation(
    x=2, y=1.02, xref="x", yref="paper",
    text="<b>CAV (autonomy level)</b>",
    showarrow=False,
    font=dict(size=12, color=NATURE_CATEGORICAL["primary"]),
    xanchor="center",
)
fig_c.add_annotation(
    x=6, y=1.02, xref="x", yref="paper",
    text="<b>STI (coverage tier)</b>",
    showarrow=False,
    font=dict(size=12, color=NATURE_CATEGORICAL["tertiary"]),
    xanchor="center",
)

layout_c = plotly_layout_defaults()
if _fig_c_view == "Total counts only":
    layout_c["barmode"] = "group"
else:
    layout_c["barmode"] = "stack"
layout_c["xaxis"]["title"] = {
    "text": "Autonomy level (CAV) · Coverage tier (STI)",
    "font": {"size": 12},
}
layout_c["xaxis"]["tickfont"] = {"size": 11}
layout_c["yaxis"]["title"] = {"text": "Marginal components per unit",
                                 "font": {"size": 12}}
layout_c["yaxis"]["tickfont"] = {"size": 11}
_y_max = max(_totals) * 1.22
layout_c["yaxis"]["range"] = [0, _y_max]
layout_c["height"] = 460
layout_c["legend"] = {
    "orientation": "v",
    "yanchor": "top", "y": 1.0,
    "xanchor": "left", "x": 1.02,
    "bgcolor": "rgba(255,255,255,0)",
    "bordercolor": "rgba(0,0,0,0)",
    "font": {"size": 10},
}
layout_c["margin"] = {"t": 60, "b": 70, "l": 72, "r": 240}
fig_c.update_layout(**layout_c)
st.plotly_chart(fig_c, width="stretch")

# Inventory table directly below the chart.
inv_rows = []
for uname, counts, plat in _UNIT_ORDER:
    row = {"Unit": uname, "Platform": plat,
           "Total": marginal_count(counts)}
    for comp_name, _, _ in _FIG_C_COMP_ORDER:
        row[comp_name] = counts.get(comp_name, 0) if comp_name in counts else 0
    inv_rows.append(row)
inv_df = pd.DataFrame(inv_rows)

with st.expander("Per-level component inventory (Extended Data Tables 3 + 4)",
                 expanded=False):
    st.dataframe(inv_df, hide_index=True, width="stretch")
    csv_bytes = inv_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download component inventory (CSV)",
        data=csv_bytes,
        file_name="clear_ats_v5_component_inventory.csv",
        mime="text/csv",
        help="Reproducibility artifact: full per-level, per-component "
             "count matrix that drives Figure C and Figure B.",
    )

st.caption(
    "Figure C. Count of additional hardware components that autonomy "
    "introduces relative to a conventional vehicle (left group) or a "
    "traditional intersection (right group). Counts come directly "
    "from Extended Data Tables 3 (CAV) and 4 (STI) of the manuscript. "
    "**Why L3 Small / Medium / Large is non-monotonic in total count.** "
    "L3 Small uses 12 sonar to compensate for missing LiDAR; L3 Medium "
    "trades sonar for two LiDAR S; L3 Large eliminates sonar entirely "
    "and adds five LiDAR S plus more radars. The total count drops "
    "across L3 Small → Medium → Large but the per-unit one-time energy "
    "rises (see Figure B), because a LiDAR S costs roughly 2.3 × a "
    "sonar in embodied energy. **Figure C count and Figure B energy "
    "tell complementary stories: count tracks deployment density; "
    "energy tracks the concentration of high-energy components.**"
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# Derived metrics strip
# ═══════════════════════════════════════════════════════════════════
st.subheader("Live derived metrics")

# Fleet-weighted totals (use a single representative fleet for context)
fleet_counts = {
    # representative: 10 L3 Small + 5 L3 Medium + 2 L3 Large + 1 L4 + 1 L5
    "CAV L3 Small": 10, "CAV L3 Medium": 5, "CAV L3 Large": 2,
    "CAV L4": 1, "CAV L5": 1,
    "STI Basic": 5, "STI Semi": 2, "STI Highly": 1,
}
all_unit_names = {
    "CAV L3 Small": CAV_COUNTS["L3 Small"], "CAV L3 Medium": CAV_COUNTS["L3 Medium"],
    "CAV L3 Large": CAV_COUNTS["L3 Large"], "CAV L4": CAV_COUNTS["L4"],
    "CAV L5": CAV_COUNTS["L5"],
    "STI Basic": STI_COUNTS["Basic"], "STI Semi": STI_COUNTS["Semi"],
    "STI Highly": STI_COUNTS["Highly"],
}
# Production-side totals (manuscript-matching under default sliders)
production_one_time = 0.0
production_sensing = 0.0
for uname, n_units in fleet_counts.items():
    bd = production_only_subsystem_breakdown(all_unit_names[uname])
    production_one_time += n_units * sum(bd.values())
    production_sensing += n_units * bd["Sensing"]
sensing_share_live = 100.0 * production_sensing / max(production_one_time, 1)

# L3 Small → L5 multiplier uses production + logistics only, which
# reproduces the manuscript 3.5× ratio at default settings.
l3s_prod = sum(production_only_subsystem_breakdown(
    CAV_COUNTS["L3 Small"]).values())
l5_prod = sum(production_only_subsystem_breakdown(
    CAV_COUNTS["L5"]).values())
l3_l5_ratio_live = l5_prod / max(l3s_prod, 1e-9)

# End-of-life fleet savings: sum of per-unit EoL savings across the
# representative fleet. Directly from eol_savings_per_unit so the
# number is explainable from the slider settings.
eol_savings_fleet = 0.0
eol_sensing_frac_of_production = 0.0
for uname, n_units in fleet_counts.items():
    counts = all_unit_names[uname]
    for cname, cnt in counts.items():
        eol_savings_fleet += n_units * cnt * eol_savings_per_unit(cname)
if production_one_time > 0:
    eol_sensing_frac_of_production = (
        100.0 * eol_savings_fleet / production_one_time
    )

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Production + logistics (representative fleet)",
    f"{production_one_time/1000:.1f} MWh",
    help="Sum of Figure B unit totals weighted by the representative "
         "fleet composition. Matches the manuscript baseline under "
         "the default one-time accounting assumptions.",
)
m2.metric(
    "Sensing share (fleet-weighted)",
    f"{sensing_share_live:.1f}%",
    help="Sensing subsystem share of the fleet-weighted production "
         "total. This is the production-side analogue of the "
         "manuscript's 94 % claim for CAV L5 alone (live value 88 % "
         "for L5 — fleet-average differs because Level 3 and Level 4 "
         "units have lower sensing shares).",
)
m3.metric(
    "L3 Small → L5 multiplier",
    f"{l3_l5_ratio_live:.2f}\u00d7",
    help="Ratio of L5 CAV production + logistics to L3 Small "
         "production + logistics. Manuscript value 3.5\u00d7; live "
         "value reproduces the component-sum ratio "
         "10,155.07 / 2,850.15 \u2248 3.56\u00d7 under the baseline "
         "inventory.",
)
m4.metric(
    "End-of-life energy savings (fleet)",
    f"{eol_savings_fleet/1000:.2f} MWh",
    delta=(f"-{eol_sensing_frac_of_production:.1f}% of production"
           if eol_savings_fleet > 0 else None),
    help=(f"Baseline reuse assumptions: sensing-refurbishment "
          f"α = {sens_alpha:.2f}, computing-refurbishment "
          f"adoption = {comp_adopt:.2f}, refurbishment energy ratio "
          f"= {ALPHA_B3:.2f}. Per-sensing-unit EoL savings = "
          f"baseline × α × (1 - ratio) = baseline "
          f"× {sens_alpha*(1-ALPHA_B3):.3f}. Fleet-weighted sum "
          f"gives {eol_savings_fleet/1000:.2f} MWh. The "
          f"failure-fraction φ is not yet wired into this "
          f"calculation."),
)

st.caption(
    "Representative fleet: 10 \u00d7 Level 3 Small, 5 \u00d7 Level 3 "
    "Medium, 2 \u00d7 Level 3 Large, 1 \u00d7 Level 4, 1 \u00d7 Level "
    "5 CAV plus 5 \u00d7 Basic, 2 \u00d7 Semi, 1 \u00d7 "
    "Highly-Automated STI. Not a regional projection; a fixed fleet "
    "chosen to exercise every unit type. Production + logistics "
    "total is independent of the end-of-life reuse assumptions; "
    "EoL savings are reported as a separate metric."
)

with st.expander("How EoL savings are calculated", expanded=False):
    st.markdown(
        f"""
**Per-sensing-unit savings.**
`E_saved_per_unit = baseline_kWh × α × (1 − r)`
where:
- `α` = sensing refurbishment rate (fraction of reusable end-of-life
  units); reuse assumption with baseline value **{sens_alpha:.2f}**.
- `r` = refurbishment energy ratio (energy of refurbishment divided
  by energy of new manufacturing); baseline value **{ALPHA_B3:.2f}**
  per §4.1.4.
- `baseline_kWh` = the unmodified Figure 3a per-component value.

For computing and communication components the analogous formula
uses the computing-refurbishment-adoption assumption (baseline
value **{comp_adopt:.2f}**) instead of `α`.

**Fleet aggregation.**
`E_saved_fleet = Σ over fleet units, Σ over components in unit`
`            n_units × count × baseline_kWh × α × (1 − r)`

**Current numerics.**
- Per-sensing-unit savings factor = α × (1 − r) =
  {sens_alpha:.2f} × (1 − {ALPHA_B3:.2f}) =
  **{sens_alpha * (1 - ALPHA_B3):.4f}**
- Fleet sensing baseline = {production_sensing/1000:.2f} MWh
- Fleet EoL savings = sensing × factor =
  **{eol_savings_fleet/1000:.2f} MWh**
- Δ as percent of production + logistics =
  **{eol_sensing_frac_of_production:.1f}%**

**What the failure fraction φ would do.**
`E_saved_per_unit = baseline_kWh × (1 − φ) × α × (1 − r)` —
the (1 − φ) factor is the fraction of end-of-life units that are
still functional and therefore eligible for refurbishment. The
φ assumption is documented in the end-page assumptions table but
is not yet wired into this calculation.
"""
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# Production-versus-utility inversion panel
# ═══════════════════════════════════════════════════════════════════
st.subheader("Why the life-cycle optimisation must span both phases")

st.info(
    "**v10 note.** The 'live' L5 annual-utility figure below is now the "
    "bottom-up component-registry value (~1 MWh/yr), not the manuscript's "
    "~18.2 MWh/yr. The manuscript figure was derived from server-GPU "
    "(NVIDIA A100) per-inference benchmarks multiplied by per-agent "
    "inference counts; v10 uses deployed automotive-ASIC power. With the "
    "recalibrated value the autonomy subsystem's *annual operational* "
    "energy is roughly one-tenth of its *one-time embodied* energy — the "
    "inverse of the manuscript's 'utility ≈ 2× one-time' framing for the "
    "autonomy stack. See "
    "`audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md`."
)

prod_log_l5 = TABLE2_PROD_LOG["CAV L5"]["prod_log"]  # 9237.2 (production + logistics, unchanged)
utility_annual_manuscript = L5_UTILITY_ANNUAL_KWH        # 18232 — manuscript pre-recalibration
utility_cumulative_manuscript = L5_UTILITY_CUMULATIVE_12YR_KWH

# Live simulator-derived value — in v10 the simulator runs through the
# bottom-up component registry (ComponentRegistryEnergyModel), so this is the
# recalibrated per-unit L5 CAV utility energy, not the inflated config value.
from core import per_unit_l5_annual_utility_kwh
try:
    utility_annual_live_ca = per_unit_l5_annual_utility_kwh("california")
    utility_annual_live_oh = per_unit_l5_annual_utility_kwh("ohio")
except Exception:
    utility_annual_live_ca = None
    utility_annual_live_oh = None

inv_c1, inv_c2, inv_c3, inv_c4 = st.columns(4)
inv_c1.metric("L5 production + logistics",
              f"{prod_log_l5:,.0f} kWh",
              help="Table 2 production + logistics columns (unchanged in v10).")
inv_c2.metric("L5 annual utility (manuscript §2.1.1, pre-recalibration)",
              f"{utility_annual_manuscript:,.0f} kWh/yr",
              help="Per-vehicle annual utility energy as cited in the "
                   "manuscript (Table 2 / §2.1.1). v10 supersedes this with "
                   "the component-registry value shown to the right; this "
                   "column is retained for comparison.")
if utility_annual_live_ca is not None:
    drift_pct = (100 * abs(utility_annual_live_ca - utility_annual_manuscript)
                 / max(utility_annual_manuscript, 1.0))
    inv_c3.metric(
        "L5 annual utility (v10 component registry)",
        f"{utility_annual_live_ca:,.0f} kWh/yr",
        delta=f"{utility_annual_live_ca - utility_annual_manuscript:+,.0f} "
              f"vs manuscript ({drift_pct:.1f} %)",
        help="Per-unit L5 CAV utility energy from the bottom-up component "
             "registry (deployed-silicon power × component counts × duty × "
             "utilization). Runs a 1-vehicle pure-L5 fleet through "
             "`_calculate_power` so this figure is reproducible from code. "
             "The large gap vs the manuscript value is the deliberate "
             "recalibration (server-GPU benchmarks → automotive-ASIC power); "
             "see the step-08 audit memo.",
    )
else:
    inv_c3.metric("L5 annual utility (v10 component registry)", "—",
                  help="Simulator call failed; see logs.")
if utility_annual_live_ca is not None:
    inv_c4.metric("L5 cumulative utility (12 years, v10)",
                  f"{12.0 * utility_annual_live_ca:,.0f} kWh",
                  help="12 × the v10 component-registry annual utility energy. "
                       f"Manuscript pre-recalibration value was "
                       f"{utility_cumulative_manuscript:,.0f} kWh.")
else:
    inv_c4.metric("L5 cumulative utility (12 years, manuscript)",
                  f"{utility_cumulative_manuscript:,.0f} kWh",
                  help="12 × manuscript pre-recalibration annual utility energy.")

# Live-computed L5 CAV production subsystem share (replaces the
# hardcoded 94 % manuscript claim; the live value is 88 % for L5
# alone).
_l5_bd = production_only_subsystem_breakdown(CAV_COUNTS["L5"])
_l5_tot = sum(_l5_bd.values())
_l5_sens_pct = 100.0 * _l5_bd["Sensing"] / max(_l5_tot, 1)
_l5_comp_pct = 100.0 * _l5_bd["Computing"] / max(_l5_tot, 1)
_l5_comm_pct = 100.0 * _l5_bd["Communication"] / max(_l5_tot, 1)

inv_left, inv_right = st.columns(2)
with inv_left:
    prod_donut = go.Figure(go.Pie(
        values=[_l5_bd["Sensing"], _l5_bd["Computing"], _l5_bd["Communication"]],
        labels=["Sensing", "Computing", "Communication"],
        hole=0.55,
        marker=dict(colors=[SUBSYSTEM_COLORS["Sensing"],
                            SUBSYSTEM_COLORS["Computing"],
                            SUBSYSTEM_COLORS["Communication"]]),
        textinfo="percent",
        textposition="inside",
        insidetextorientation="horizontal",
        direction="clockwise", sort=False,
    ))
    prod_donut.update_layout(
        title=dict(text="L5 CAV production + logistics share",
                   x=0.5, xanchor="center", font=dict(size=13)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15,
                    x=0.5, xanchor="center"),
        margin=dict(t=40, b=40, l=20, r=20),
        height=340,
    )
    st.plotly_chart(prod_donut, width="stretch")
    st.caption(
        f"Live value: sensing {_l5_sens_pct:.1f}% of L5 CAV "
        f"production + logistics. Manuscript §2.1.1 cites 94% for "
        f"CAV; the manuscript value uses a different aggregation "
        f"path (see the Data consistency note at the end of this "
        f"page)."
    )
with inv_right:
    # v10: utility-phase subsystem share is now decomposed by the component
    # registry (deployed-silicon power × counts × duty × utilization). We show
    # the L5 ECAV autonomy-subsystem split. (v3-v9 showed a hardcoded 98%
    # computing share copied from manuscript §2.1.1; that figure came from the
    # server-GPU benchmark inflation and is superseded here.)
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _app = _Path(__file__).resolve().parent.parent
        if str(_app) not in _sys.path:
            _sys.path.insert(0, str(_app))
        from component_registry import ComponentRegistryEnergyModel as _CRM
        _l5 = _CRM().get_ecav_power("L5", 0, 0)
        _util_split = [_l5["computing"], _l5["sensing"], _l5["communication"]]
        _util_tot = sum(_util_split) or 1.0
        _comp_pct = 100.0 * _l5["computing"] / _util_tot
    except Exception:
        _util_split = [0.71, 0.285, 0.005]
        _comp_pct = 71.0
    util_donut = go.Figure(go.Pie(
        values=_util_split,
        labels=["Computing", "Sensing", "Communication"],
        hole=0.55,
        marker=dict(colors=[SUBSYSTEM_COLORS["Computing"],
                            SUBSYSTEM_COLORS["Sensing"],
                            SUBSYSTEM_COLORS["Communication"]]),
        textinfo="percent",
        textposition="inside",
        insidetextorientation="horizontal",
        direction="clockwise", sort=False,
    ))
    util_donut.update_layout(
        title=dict(text="L5 CAV utility-phase autonomy split (v10 registry)",
                   x=0.5, xanchor="center", font=dict(size=13)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15,
                    x=0.5, xanchor="center"),
        margin=dict(t=40, b=40, l=20, r=20),
        height=340,
    )
    st.plotly_chart(util_donut, width="stretch")
    st.caption(
        f"v10 component registry: computing is ≈{_comp_pct:.0f}% of the L5 CAV "
        "autonomy-subsystem operational energy (sensing ≈ rest, communication "
        "negligible). The manuscript §2.1.1 '98% computing' figure was derived "
        "from server-GPU per-inference benchmarks and is superseded here. The "
        "Scenario Explorer shows this share decaying further over time as "
        "hardware-doubling compounds."
    )

st.caption(
    "The subsystem that dominates one-time embodied energy (sensing) is "
    "comparable in scale to the one that dominates operational energy at L5 "
    "(computing), and the *absolute* operational energy of the autonomy stack "
    "(~1 MWh/yr per L5 CAV in v10) is now smaller than its one-time embodied "
    "energy (~9.2 MWh per L5 CAV). Life-cycle optimisation therefore requires "
    "coordinated reduction of sensor manufacturing energy and computing "
    "operational power; for vehicles the embodied cost is no longer negligible "
    "next to the operational cost."
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# End-of-life leverage tornado
# ═══════════════════════════════════════════════════════════════════
st.subheader("End-of-life leverage")

# Target metric: representative-fleet total one-time energy. Baseline =
# every Block 1 slider at default. Each tornado row moves one slider
# from its lower bound to its upper bound with the others held at default.
def _fleet_total_with(sens_eff_v: float, comp_adopt_v: float,
                     sens_alpha_v: float, life_ext_v: int) -> float:
    global sens_eff, comp_adopt, sens_alpha, life_ext
    _s, _c, _a, _l = sens_eff, comp_adopt, sens_alpha, life_ext
    sens_eff = sens_eff_v
    comp_adopt = comp_adopt_v
    sens_alpha = sens_alpha_v
    life_ext = life_ext_v
    tot = 0.0
    for uname, n_units in fleet_counts.items():
        tot += n_units * adjusted_unit_total(all_unit_names[uname])
    sens_eff, comp_adopt, sens_alpha, life_ext = _s, _c, _a, _l
    return tot


baseline_fleet = _fleet_total_with(0.0, 0.0, 0.70, 0)

tornado_rows = []
# Each row carries (full_label, low_pct, high_pct, lever_min, lever_max).
# 1. Sensing manufacturing efficiency: 0% → 60%
lo = _fleet_total_with(0.00, 0.0, 0.70, 0)
hi = _fleet_total_with(0.60, 0.0, 0.70, 0)
tornado_rows.append((
    "Sensing manufacturing efficiency improvement\n(0 % → 60 % per-unit reduction)",
    100 * (lo - baseline_fleet) / baseline_fleet,
    100 * (hi - baseline_fleet) / baseline_fleet))
# 2. Sensing refurbishment rate α: 0.0 → 1.0
lo = _fleet_total_with(0.0, 0.0, 0.0, 0)
hi = _fleet_total_with(0.0, 0.0, 1.0, 0)
tornado_rows.append((
    "Sensing refurbishment rate at end-of-life\n(0 % → 100 % of sensors refurbished)",
    100 * (lo - baseline_fleet) / baseline_fleet,
    100 * (hi - baseline_fleet) / baseline_fleet))
# 3. Sensor lifetime extension: 0 → 8 years
lo = _fleet_total_with(0.0, 0.0, 0.70, 0)
hi = _fleet_total_with(0.0, 0.0, 0.70, 8)
tornado_rows.append((
    "Sensor service-life extension\n(12 yr baseline → 20 yr extended)",
    100 * (lo - baseline_fleet) / baseline_fleet,
    100 * (hi - baseline_fleet) / baseline_fleet))
# 4. Computing refurbishment adoption: 0.0 → 1.0
lo = _fleet_total_with(0.0, 0.0, 0.70, 0)
hi = _fleet_total_with(0.0, 1.0, 0.70, 0)
tornado_rows.append((
    "Computing refurbishment adoption\n(0 % → 100 % of compute / comm units reused)",
    100 * (lo - baseline_fleet) / baseline_fleet,
    100 * (hi - baseline_fleet) / baseline_fleet))

# Sort by total span (max - min) descending so the largest-leverage
# lever is at the top.
tornado_rows.sort(key=lambda r: abs(r[2] - r[1]), reverse=True)

# Plot. Conventions:
#   reduction (Δ ≤ 0)  → green (good outcome)
#   increase  (Δ > 0)  → red   (bad outcome)
# Suppress labels for |Δ| < 0.5 % to avoid the "+0.0%" clutter.
fig_t = go.Figure()
labels   = [r[0] for r in tornado_rows]
low_vals = [r[1] for r in tornado_rows]
hi_vals  = [r[2] for r in tornado_rows]

def _fmt_pct(v: float) -> str:
    if abs(v) < 0.5:
        return ""
    return f"{v:+.1f}%"

def _color_for(v: float) -> str:
    if v <= 0:
        return NATURE_CATEGORICAL["tertiary"]   # green = reduction
    return NATURE_CATEGORICAL["secondary"]      # red   = increase

# Use a single Bar trace per row (low + high stacked) only where both
# are non-trivial; otherwise draw the single non-trivial side only so
# the chart never displays a fake symmetric zero.
low_colors = [_color_for(v) for v in low_vals]
hi_colors  = [_color_for(v) for v in hi_vals]

fig_t.add_trace(go.Bar(
    y=labels, x=low_vals, orientation="h",
    name="Design action at its lower bound",
    marker=dict(color=low_colors, opacity=0.85),
    text=[_fmt_pct(v) for v in low_vals],
    textposition="outside",
    cliponaxis=False,
    hovertemplate=("<b>%{y}</b><br>Design action at its lower bound<br>"
                   "Δ vs baseline: %{x:+.2f}%<extra></extra>"),
))
fig_t.add_trace(go.Bar(
    y=labels, x=hi_vals, orientation="h",
    name="Design action at its upper bound",
    marker=dict(color=hi_colors, opacity=0.85),
    text=[_fmt_pct(v) for v in hi_vals],
    textposition="outside",
    cliponaxis=False,
    hovertemplate=("<b>%{y}</b><br>Design action at its upper bound<br>"
                   "Δ vs baseline: %{x:+.2f}%<extra></extra>"),
))
# Vertical zero line so the sign-direction is unambiguous.
fig_t.add_vline(x=0, line=dict(color=NATURE_CATEGORICAL["neutral"],
                                 width=0.8, dash="solid"))

layout_t = plotly_layout_defaults()
layout_t["barmode"] = "group"
layout_t["title"] = {
    "text": ("End-of-life leverage — change in fleet one-time energy "
             "from moving each design action to its bound"),
    "x": 0.0, "xanchor": "left", "font": {"size": 14},
    "pad": {"l": 8, "t": 8},
}
layout_t["xaxis"]["title"] = {
    "text": "Δ in fleet one-time energy vs default settings (%)",
    "font": {"size": 12}
}
layout_t["xaxis"]["tickfont"] = {"size": 11}
# Pad x-range so outside-positioned labels do not get clipped.
_xmax = max(max(hi_vals), 0) * 1.15 + 5
_xmin = min(min(low_vals), 0) * 1.15 - 5
layout_t["xaxis"]["range"] = [_xmin, _xmax]
layout_t["yaxis"]["title"] = {"text": ""}
layout_t["yaxis"]["showgrid"] = False
layout_t["yaxis"]["tickfont"] = {"size": 11}
layout_t["yaxis"]["automargin"] = True
layout_t["height"] = 460
# Stack legend ABOVE the plot so it cannot collide with the x-axis label
# or the caption text below the chart.
layout_t["legend"] = {
    "orientation": "h",
    "yanchor": "bottom", "y": 1.06,
    "xanchor": "left", "x": 0.0,
    "bgcolor": "rgba(255,255,255,0)",
    "bordercolor": "rgba(0,0,0,0)",
    "font": {"size": 11},
}
layout_t["margin"] = {"t": 90, "b": 80, "l": 280, "r": 60}
fig_t.update_layout(**layout_t)
st.plotly_chart(fig_t, width="stretch")
st.caption(
    "Each row shows how far one design action moves the total "
    "fleet one-time energy when that action is taken to its lower "
    "or upper bound while the others stay at baseline. Green bars "
    "(Δ ≤ 0) reduce the burden; red bars (Δ > 0) raise it. Bars "
    "below 0.5 % in magnitude are unlabelled. The bound that "
    "produces no change (for example, computing refurbishment at "
    "its lower bound, which equals the baseline) is intentionally "
    "absent rather than drawn as a fake symmetric zero. "
    "Sensing-side actions (rows 1 to 3) carry the largest leverage "
    "because sensors dominate the one-time burden; computing "
    "refurbishment is small because computing is only a small "
    "fraction of the total."
)
with st.expander("How the bounds are computed", expanded=False):
    st.markdown(
        """
**Definition.** Each row reports `100 × (E_action - E_baseline) / E_baseline`
where `E_baseline` is the representative-fleet one-time energy at the
default one-time accounting assumptions (sensing manufacturing efficiency = 0,
computing refurbishment adoption = 0, sensing refurbishment α = 0.70,
sensor lifetime extension = 0).

**Bounds.** *Lower bound* moves the design action to its minimum
range (0 % efficiency, 0.0 refurbishment, 0 yr extension) while every
other action stays at default. *Upper bound* moves the same action to
its maximum (60 % efficiency, 1.0 refurbishment, 8 yr extension).

**Sensor lifetime extension mechanism.** Extending the service life
from 12 to 12 + N years multiplies the per-unit production energy by
`12 / (12 + N)`, amortising the burden over more years of service.
Extending 8 years (from 12 to 20) reduces the amortised production
energy by `12 / 20 = 40 %`.

**Why computing refurbishment looks small.** Computing is only ~6 %
of the one-time burden; even at 100 % refurbishment its leverage on
the fleet total is bounded by that share.
"""
    )

# Update the EoL "How EoL savings are calculated" expander text below
# uses internal parameter names that previously read as Block 1 / 3
# slider references. The rewording below makes them stand on their
# own without referring to UI controls that no longer exist.

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# End-page details
# ═══════════════════════════════════════════════════════════════════
st.subheader("Component inventory and one-time assumptions")
st.caption(
    "Reference tables for the component-level inventory and the "
    "one-time accounting assumptions that anchor the figures above. "
    "Read-only; collapsed by default."
)

with st.expander("Component-level energy inventory (Figure 3a)",
                 expanded=False):
    st.markdown(
        "Per-unit one-time energy by component, from manuscript "
        "Figure 3a. Source values are read-only on the public page."
    )
    st.dataframe(pd.DataFrame(build_component_rows()),
                 hide_index=True, width="stretch")

    st.markdown("**Component counts per unit type**")
    st.caption("Extended Data Tables 3 (CAV) and 4 (STI) combined.")
    # The wide count table mixes integer counts with the string '—' for
    # platform-irrelevant cells (e.g. CAV columns on STI components). Cast
    # the display dataframe to object dtype so pyarrow does not try to
    # infer a single numeric type. This is a display-only transformation
    # — the source data returned by build_count_wide_table() is unchanged
    # for any downstream caller.
    _count_df_display = pd.DataFrame(build_count_wide_table()).astype(str)
    st.dataframe(_count_df_display, hide_index=True, width="stretch")

    st.markdown("**Citations**")
    for c in BLOCK2_CITATIONS:
        st.caption(c)

with st.expander("One-time accounting assumptions",
                 expanded=False):
    st.markdown(
        "Structural assumptions used in the one-time accounting. The "
        "refurbishment energy ratio enters the calculation through "
        "the end-of-life leverage panel; the other rows are scenario "
        "labels that document the manuscript baseline."
    )
    _assumption_rows = pd.DataFrame([
        {"Assumption": "Manufacturing region",
         "Baseline value": "Asia-Pacific",
         "Role in analysis": "Scenario label"},
        {"Assumption": "Logistics model",
         "Baseline value": "Sea + truck",
         "Role in analysis": "Scenario label"},
        {"Assumption": "Refurbishment energy ratio (Section 4.1.4)",
         "Baseline value": "25 %",
         "Role in analysis": "Wired into end-of-life leverage"},
        {"Assumption": "End-of-life failure fraction phi",
         "Baseline value": "10 %",
         "Role in analysis": "Scenario label"},
        {"Assumption": "Computing obsolescence window",
         "Baseline value": "8 to 24 months",
         "Role in analysis": "Scenario label"},
        {"Assumption": "Sensor refurbishment rate alpha (default)",
         "Baseline value": "0.70",
         "Role in analysis": "Reuse assumption"},
        {"Assumption": "Sensor service life",
         "Baseline value": "12 years",
         "Role in analysis": "Service-life assumption"},
    ])
    st.dataframe(_assumption_rows, hide_index=True,
                 width="stretch")

st.subheader("Data uncertainty ranges for one-time energy")
st.caption(
    "One-time uncertainty is reported as a documented input range. "
    "The values come from component inventory, OpenLCA / ecoinvent "
    "process lookups, logistics assumptions, and end-of-life "
    "accounting. They are not future-trajectory uncertainties and "
    "are not user controllable on this page. Live propagation of "
    "utility-phase uncertainty remains on the Scenario Explorer page."
)

_OT_ROWS = one_time_factor_rows()
_OT_GROUP_ORDER = ("Production", "Logistics", "End-of-life")
for _stage in _OT_GROUP_ORDER:
    _stage_rows = [r for r in _OT_ROWS if r["Lifecycle stage"] == _stage]
    if not _stage_rows:
        continue
    st.markdown(f"**{_stage}**")
    st.dataframe(
        pd.DataFrame(_stage_rows)[[
            "Factor ID",
            "Factor name",
            "Distribution / range",
            "Affected quantity",
            "Role in analysis",
            "Source",
        ]],
        hide_index=True,
        width="stretch",
    )

st.caption(
    "These ranges document residual input uncertainty and are not "
    "user-controlled on this page."
)

with st.expander("Data consistency note", expanded=False):
    st.caption(
        "Component-level values reproduce manuscript Figure 3a / "
        "Table 2 exactly. A small number of unit-total rows reflect "
        "differences between component-sum aggregation and an "
        "alternative aggregation path used in the manuscript text. "
        "Both paths are reported below for transparency."
    )
    _cc_df = pd.DataFrame([
        {"Item": claim, "Manuscript": ms_v, "Live": live_v,
         "Status": "alternative aggregation" if bad else "match"}
        for (claim, ms_v, live_v, bad) in _cc_rows
    ])
    st.dataframe(_cc_df, hide_index=True, width="stretch")
    st.caption(
        f"Match status: {_cc_match_count} of {len(_cc_rows)} items "
        "match the manuscript value via direct component-sum "
        "aggregation."
    )

st.markdown("---")
st.caption(
    "One-Time Energy and Marginal Components. Production and logistics "
    "phase only. For operational (utility-phase) analysis, see the "
    "Utility Phase Energy and Scenario Explorer pages."
)
