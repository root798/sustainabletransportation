"""Uncertainty Panel — grouped L1 / L2 / L3 presets with fixed/free factor view.

Replaces the legacy single-plot Uncertainty Analysis page. Design spec lives in
audits/uncertainty_governance/UNCERTAINTY_PANEL_REDESIGN.md.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (  # noqa: E402
    GROUPED_DEFAULT_BUNDLE,
    GROUPED_EXPLORATORY_BUNDLE,
    GROUPED_PAPER_SAFE_BUNDLE,
    L1_PRESETS,
    L2_PRESETS,
    L3_PRESETS,
    POLICY_LABELS,
    REGION_LABELS,
    band_metadata,
    interpretation_boundary,
    load_base_config,
    load_contribution_experiment,
    load_grouped_uncertainty_preset,
    load_quantiles,
    mc_sample_count,
    region_paper_safety,
    rgba,
    scale,
    validate_grouped_preset_bundle,
)

st.set_page_config(page_title="Uncertainty Panel", page_icon="U", layout="wide")

# ---------------------------------------------------------------------------
# A. Explainer
# ---------------------------------------------------------------------------
st.title("Uncertainty Panel")
explain_col, bundle_col = st.columns([0.65, 0.35])
with explain_col:
    st.markdown(
        "This panel controls the Monte Carlo uncertainty that surrounds each scenario. "
        "Factors are grouped by layer — **L1** baseline data and emission factors, "
        "**L2** per-device load-model, **L3** long-horizon trajectory. "
        "Each layer has its own preset. Some factors are fixed by default because they "
        "are well constrained, duplicated, or too destabilizing for a decision-meaningful "
        "band. Others remain adjustable. Structural shocks are not folded into any band; "
        "use the separate Structural Shocks panel for those."
    )
with bundle_col:
    st.markdown("**Quick bundles**")
    if st.button("Decision-meaningful default (recommended)"):
        st.session_state["unc_panel_l1"] = GROUPED_DEFAULT_BUNDLE[0]
        st.session_state["unc_panel_l2"] = GROUPED_DEFAULT_BUNDLE[1]
        st.session_state["unc_panel_l3"] = GROUPED_DEFAULT_BUNDLE[2]
    if st.button("Paper-safe reproduction"):
        st.session_state["unc_panel_l1"] = GROUPED_PAPER_SAFE_BUNDLE[0]
        st.session_state["unc_panel_l2"] = GROUPED_PAPER_SAFE_BUNDLE[1]
        st.session_state["unc_panel_l3"] = GROUPED_PAPER_SAFE_BUNDLE[2]
    if st.button("Exploratory long-horizon"):
        st.session_state["unc_panel_l1"] = GROUPED_EXPLORATORY_BUNDLE[0]
        st.session_state["unc_panel_l2"] = GROUPED_EXPLORATORY_BUNDLE[1]
        st.session_state["unc_panel_l3"] = GROUPED_EXPLORATORY_BUNDLE[2]

# Defaults
st.session_state.setdefault("unc_panel_l1", GROUPED_DEFAULT_BUNDLE[0])
st.session_state.setdefault("unc_panel_l2", GROUPED_DEFAULT_BUNDLE[1])
st.session_state.setdefault("unc_panel_l3", GROUPED_DEFAULT_BUNDLE[2])
st.session_state.setdefault("unc_panel_region", "california")
st.session_state.setdefault("unc_panel_policy", "baseline")

# Region and policy selectors
sel_col_r, sel_col_p = st.columns(2)
with sel_col_r:
    region = st.selectbox(
        "Region",
        ["california", "ohio", "us_average"],
        format_func=lambda v: REGION_LABELS[v],
        key="unc_panel_region",
    )
with sel_col_p:
    policy = st.selectbox(
        "Policy",
        ["baseline", "aggressive", "conservative"],
        format_func=lambda v: POLICY_LABELS[v],
        key="unc_panel_policy",
    )

paper_safety = region_paper_safety(region)
if region == "us_average":
    st.warning(
        "US Average uses a synthetic midpoint scenario and is quarantined from paper-safe outputs. "
        "Uncertainty bands are exploratory only."
    )
if policy != "baseline":
    st.info(
        "Policy-conditional Monte Carlo (aggressive / conservative) is exploratory per METHODS_ALIGNMENT M14."
    )

st.divider()

# ---------------------------------------------------------------------------
# B. Grouped controls (three cards)
# ---------------------------------------------------------------------------
st.subheader("Grouped uncertainty controls")

exp_df = load_contribution_experiment()


def _contribution_callout(layer_code: str, year: int = 2030) -> str:
    if exp_df is None:
        return ""
    scenario_tag = {"L1": "L1_only", "L2": "L2_only", "L3": "L3_only"}[layer_code]
    row = exp_df[(exp_df["region"] == region) & (exp_df["scenario"] == scenario_tag) & (exp_df["year"] == year)]
    if row.empty:
        return ""
    wom = float(row.iloc[0]["width_over_median"])
    return f"{layer_code}-only contribution to 2030 band: {wom*100:.0f}% of median."


def _fixed_free_table(layer_code: str, choice: str) -> pd.DataFrame:
    """Hand-curated fixed/free summary per preset. Mirrors the CSV diagnosis."""
    rows: list[dict[str, str]] = []
    if layer_code == "L1":
        if choice == "fixed":
            rows = [
                {"Factor": "initial BEV share (F02)", "Status": "fixed", "Why": "absorbed by F25 within ~3 years"},
                {"Factor": "initial f_clean (F01)", "Status": "fixed", "Why": "absorbed by F26 within ~3 years"},
                {"Factor": "e_clean / e_fossil / e_gasoline (F03–F05)", "Status": "fixed", "Why": "user selected L1 fixed"},
            ]
        else:
            rows = [
                {"Factor": "initial BEV share (F02)", "Status": "free (tight Beta)", "Why": "measurement-grade width"},
                {"Factor": "initial f_clean (F01)", "Status": "free (tight Beta)", "Why": "measurement-grade width"},
                {"Factor": "e_clean (F03)", "Status": "free", "Why": "operational vs life-cycle choice"},
                {"Factor": "e_fossil (F04)", "Status": "free", "Why": "NGCC↔coal technology range"},
                {"Factor": "e_gasoline (F05)", "Status": "free", "Why": "EPA physical range"},
            ]
    elif layer_code == "L2":
        if choice == "fixed":
            rows = [{"Factor": "all L2 (F06–F22)", "Status": "fixed", "Why": "user selected L2 fixed"}]
        elif choice == "low":
            rows = [
                {"Factor": "ECAV per-level (F06–F08)", "Status": "fixed", "Why": "dual-axis duplication S2-01"},
                {"Factor": "STI per-level (F12–F14)", "Status": "fixed", "Why": "dual-axis duplication S2-02"},
                {"Factor": "cohort_decay_factor (F21)", "Status": "fixed", "Why": "effect vanishes by 2036"},
                {"Factor": "ECAV per-subsystem (F09–F11)", "Status": "free (narrowed)", "Why": "retained single axis"},
                {"Factor": "STI per-subsystem (F15–F17)", "Status": "free (narrowed)", "Why": "retained single axis"},
                {"Factor": "Dirichlet level mix (F18–F19)", "Status": "free (narrowed)", "Why": "α ×3 → narrower simplex"},
                {"Factor": "icecav_power_factor (F20)", "Status": "free (narrowed)", "Why": "tighter physical range"},
                {"Factor": "retire_year (F22)", "Status": "free", "Why": "evidence-anchored"},
            ]
        elif choice == "medium":
            rows = [
                {"Factor": "ECAV per-level (F06–F08)", "Status": "free", "Why": "paper-safe baseline retains dual-axis"},
                {"Factor": "STI per-level (F12–F14)", "Status": "free", "Why": "paper-safe baseline retains dual-axis"},
                {"Factor": "ECAV per-subsystem (F09–F11)", "Status": "free", "Why": "per-subsystem axis"},
                {"Factor": "STI per-subsystem (F15–F17)", "Status": "free", "Why": "per-subsystem axis"},
                {"Factor": "Dirichlet level mix (F18–F19)", "Status": "free", "Why": "level-mix scenario"},
                {"Factor": "icecav_power_factor (F20)", "Status": "free", "Why": "alternator overhead"},
                {"Factor": "cohort_decay_factor (F21)", "Status": "free", "Why": "early-horizon only"},
                {"Factor": "retire_year (F22)", "Status": "free", "Why": "evidence-anchored"},
            ]
        else:  # high
            rows = [
                {"Factor": "all L2 (F06–F22)", "Status": "free (widened)", "Why": "exploratory; retains duplication"},
            ]
    else:  # L3
        if choice == "fixed":
            rows = [{"Factor": "all L3 (F23–F28)", "Status": "fixed", "Why": "no trajectory divergence"}]
        elif choice == "low":
            rows = [
                {"Factor": "CAV 2075 target (F23)", "Status": "free (narrowed)", "Why": "pulled to mode"},
                {"Factor": "STI 2075 target (F24)", "Status": "free (narrowed)", "Why": "pulled to mode"},
                {"Factor": "EV growth exponent (F25)", "Status": "free (narrowed)", "Why": "sd halved"},
                {"Factor": "clean-energy growth (F26)", "Status": "free (narrowed)", "Why": "sd halved"},
                {"Factor": "efficiency doubling (F27)", "Status": "free (narrowed)", "Why": "tighter triangular"},
                {"Factor": "total_car_increase (F28)", "Status": "free (narrowed)", "Why": "sd halved"},
            ]
        elif choice == "medium":
            rows = [{"Factor": "all L3 (F23–F28)", "Status": "free", "Why": "paper-safe baseline"}]
        else:  # high
            rows = [{"Factor": "all L3 (F23–F28)", "Status": "free (widened)", "Why": "exploratory long-horizon"}]
    return pd.DataFrame(rows)


cols = st.columns(3)
for i, (layer_code, choices, long_name) in enumerate([
    ("L1", L1_PRESETS, "Baseline data and emission factors"),
    ("L2", L2_PRESETS, "Load-model per-device uncertainty"),
    ("L3", L3_PRESETS, "Long-horizon trajectory uncertainty"),
]):
    with cols[i]:
        st.markdown(f"**{layer_code} — {long_name}**")
        key = f"unc_panel_{layer_code.lower()}"
        choice = st.radio(
            f"{layer_code} preset",
            list(choices),
            index=list(choices).index(st.session_state[key]),
            key=key,
            horizontal=False,
        )
        badge = "paper-safe" if choice in ("fixed", "low", "medium") else "exploratory"
        st.caption(f"_{badge}_")
        st.dataframe(_fixed_free_table(layer_code, choice), hide_index=True, width="stretch")
        callout = _contribution_callout(layer_code)
        if callout:
            st.caption(callout)

l1_choice = st.session_state["unc_panel_l1"]
l2_choice = st.session_state["unc_panel_l2"]
l3_choice = st.session_state["unc_panel_l3"]

# Bundle warnings
warnings = validate_grouped_preset_bundle(l1_choice, l2_choice, l3_choice)
for w in warnings:
    st.warning(w)

# Composed preset preview
bundle = load_grouped_uncertainty_preset(l1_choice, l2_choice, l3_choice, region)
summary_cols = st.columns(3)
summary_cols[0].metric("Bundle", f"L1={l1_choice} / L2={l2_choice} / L3={l3_choice}")
summary_cols[1].metric("Paper-safe", "Yes" if bundle["paper_safe"] else "No")
summary_cols[2].metric("Fixed factors", str(len(bundle["fixed_factors"])))

st.divider()

# ---------------------------------------------------------------------------
# C. Main uncertainty figure — ATS Emissions only
# ---------------------------------------------------------------------------
st.subheader("Main uncertainty figure")

qf = load_quantiles(region, policy)

if qf is None:
    st.info(
        "No quantile file for this region/policy in results/. Run `python footprint_model.py "
        "--scenarios {region} --policy {policy} --mc 200 --seed 42` to populate.".format(region=region, policy=policy)
    )
else:
    metric = "ATS Emissions (kg CO2)"
    meta = band_metadata(qf, metric)
    sample_n = mc_sample_count(region, policy)
    ib = interpretation_boundary(qf, metric=metric)

    cap_cols = st.columns(3)
    cap_cols[0].metric("MC sample count", str(sample_n) if sample_n is not None else "—")
    cap_cols[1].metric("Band status", "Zero-width" if meta["degenerate"] else "Visible")
    cap_cols[2].metric("Interpretation boundary year", str(ib.get("boundary_year")) if ib.get("boundary_year") else "—")

    p05c, p50c, p95c = f"{metric}_p05", f"{metric}_p50", f"{metric}_p95"
    if all(c in qf.columns for c in [p05c, p50c, p95c]):
        p05_scaled, unit, factor = scale(qf[p05c], kind="emissions")
        p50_scaled = qf[p50c] / factor
        p95_scaled = qf[p95c] / factor

        fig = go.Figure()
        if not meta["degenerate"]:
            fig.add_trace(go.Scatter(
                x=list(qf.index) + list(qf.index[::-1]),
                y=list(p05_scaled) + list(p95_scaled[::-1]),
                fill="toself",
                fillcolor=rgba("#1f4f8c", 0.18),
                line=dict(width=0),
                name="p05–p95 band",
                hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=qf.index, y=p50_scaled, mode="lines",
            name="median (p50)", line=dict(color="#1f4f8c", width=3),
        ))
        if ib.get("boundary_year"):
            by = ib["boundary_year"]
            fig.add_vline(x=by, line=dict(color="#d97400", width=1.5, dash="dash"))
            fig.add_annotation(
                x=by, y=float(p95_scaled.max() if len(p95_scaled) else 0),
                text=f"Interpretation boundary ({by})", showarrow=False,
                yshift=8, font=dict(color="#d97400", size=11),
            )
        fig.update_layout(
            title=f"ATS Emissions — {REGION_LABELS[region]} / {POLICY_LABELS[policy]}",
            xaxis_title="Year",
            yaxis_title=unit,
            hovermode="x unified",
            legend=dict(x=0.01, y=0.99),
            margin=dict(t=50, b=40, l=60, r=20),
        )
        st.plotly_chart(fig, width="stretch")

        st.caption(
            f"Preset bundle shown: L1={l1_choice} / L2={l2_choice} / L3={l3_choice}. "
            f"Current committed `_quantiles.csv` reflects the historical paper-safe pipeline; "
            f"re-run MC with the chosen bundle for bundle-specific bands."
        )
    else:
        st.warning("Quantile columns for ATS Emissions are missing.")

st.divider()

# ---------------------------------------------------------------------------
# D. Layer contribution figure
# ---------------------------------------------------------------------------
st.subheader("Layer contribution to band width")

if exp_df is None:
    st.info("Contribution experiment CSV not found. Run `python scripts/uncertainty_contribution_experiment.py`.")
else:
    view_mode = st.radio(
        "Contribution view", ["Grouped bars (2030 / 2050 / 2075)", "Overlay lines (relative width vs year)"],
        horizontal=True,
    )
    region_df = exp_df[exp_df["region"] == region]
    if view_mode.startswith("Grouped"):
        want = region_df[region_df["scenario"].isin(["L1_only", "L2_only", "L3_only"])]
        if want.empty:
            st.info("No contribution data for this region.")
        else:
            pivot = want.pivot_table(index="year", columns="scenario", values="width_over_median")
            fig_bar = go.Figure()
            colors = {"L1_only": "#4c78a8", "L2_only": "#f58518", "L3_only": "#54a24b"}
            for scen in ["L1_only", "L2_only", "L3_only"]:
                if scen in pivot.columns:
                    fig_bar.add_trace(go.Bar(
                        x=[str(int(y)) for y in pivot.index],
                        y=pivot[scen].values,
                        name=scen.replace("_only", ""),
                        marker_color=colors[scen],
                    ))
            fig_bar.update_layout(
                barmode="group",
                title="Layer-only contribution to relative band width (p95–p05)/p50",
                xaxis_title="Year",
                yaxis_title="Relative band width",
                margin=dict(t=50, b=40, l=60, r=20),
                legend=dict(x=0.01, y=0.99),
            )
            st.plotly_chart(fig_bar, width="stretch")
    else:
        # Overlay lines are only available if per-year quantiles are precomputed; here we plot the
        # three sampled years as scatter points for each layer.
        want = region_df[region_df["scenario"].isin(["L1_only", "L2_only", "L3_only"])]
        fig_line = go.Figure()
        colors = {"L1_only": "#4c78a8", "L2_only": "#f58518", "L3_only": "#54a24b"}
        for scen in ["L1_only", "L2_only", "L3_only"]:
            sub = want[want["scenario"] == scen].sort_values("year")
            if sub.empty:
                continue
            fig_line.add_trace(go.Scatter(
                x=sub["year"], y=sub["width_over_median"],
                mode="lines+markers", name=scen.replace("_only", ""),
                line=dict(color=colors[scen], width=2),
            ))
        fig_line.update_layout(
            title="Layer-only contribution trajectories",
            xaxis_title="Year",
            yaxis_title="Relative band width",
            margin=dict(t=50, b=40, l=60, r=20),
            legend=dict(x=0.01, y=0.99),
        )
        st.plotly_chart(fig_line, width="stretch")
    st.caption(
        "Source: audits/uncertainty_governance/UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv. "
        "Each layer-only run samples 150 Monte Carlo draws with only that layer's priors free; "
        "other layers are held at their central values."
    )

st.divider()

# ---------------------------------------------------------------------------
# E. Contribution summary cards
# ---------------------------------------------------------------------------
st.subheader("Layer summary")

def _layer_card(layer_code: str, choice: str, long_name: str) -> None:
    st.markdown(f"**{layer_code} — {long_name}** &nbsp;·&nbsp; current: `{choice}`")
    if exp_df is None:
        st.caption("(no experiment data)")
        return
    tag = {"L1": "L1_only", "L2": "L2_only", "L3": "L3_only"}[layer_code]
    sub = exp_df[(exp_df["region"] == region) & (exp_df["scenario"] == tag)]
    if sub.empty:
        st.caption("(no contribution rows)")
        return
    display = sub[["year", "width_over_median", "interpretation_boundary_year"]].copy()
    display = display.rename(columns={
        "year": "Year",
        "width_over_median": "Relative width",
        "interpretation_boundary_year": "Interp. boundary year",
    })
    display["Relative width"] = display["Relative width"].map(lambda x: f"{float(x):.2f}×p50")
    st.dataframe(display, hide_index=True, width="stretch")

card_cols = st.columns(3)
with card_cols[0]:
    _layer_card("L1", l1_choice, "Baseline data & emission factors")
with card_cols[1]:
    _layer_card("L2", l2_choice, "Load-model per-device uncertainty")
with card_cols[2]:
    _layer_card("L3", l3_choice, "Long-horizon trajectory uncertainty")

recommendations = []
if l3_choice == "medium":
    recommendations.append(
        "L3 is the primary long-horizon driver. The `l3_low` preset halves trajectory sigmas "
        "and tightens truncations; consider switching unless reproducing the paper."
    )
if l2_choice == "medium":
    recommendations.append(
        "L2 medium retains the per-level × per-subsystem dual-axis compounding (S2-01/S2-02). "
        "The `l2_low` preset removes the duplication and narrows bands ~25%."
    )
if l1_choice == "medium":
    recommendations.append(
        "L1 medium widens 2024 baseline via Beta draws. `l1_fixed` is cleaner for 2030+ interpretation."
    )
if recommendations:
    st.markdown("### Recommendations")
    for r in recommendations:
        st.markdown(f"- {r}")

st.divider()

# ---------------------------------------------------------------------------
# F. Support boundary
# ---------------------------------------------------------------------------
st.subheader("What the bands include — and do not")
support_rows = [
    {"Included in quantile bands": "Parameter priors (L1/L2/L3) under the selected preset bundle", "Status": "yes"},
    {"Included in quantile bands": "Alternative model structures (adoption curve, retirement logic)", "Status": "no"},
    {"Included in quantile bands": "Missing lifecycle phases (manufacturing, EoL)", "Status": "no"},
    {"Included in quantile bands": "Structural shocks (grid stall, policy freeze, etc.)", "Status": "no"},
    {"Included in quantile bands": "18 absolute per-level × per-subsystem ECAV/STI power cells (S2-05)", "Status": "disclosed, no prior"},
    {"Included in quantile bands": "Region substitution when files are missing", "Status": "no"},
]
st.dataframe(pd.DataFrame(support_rows), hide_index=True, width="stretch")
st.caption(
    "For discrete-scenario uncertainty (grid stall, EV slowdown, etc.), use the Structural Shocks panel. "
    "Those results are never folded into ordinary Monte Carlo."
)
