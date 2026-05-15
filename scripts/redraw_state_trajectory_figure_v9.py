"""Redraw the state-level annual ATS energy/emissions reference figure
using the v9 dashboard's data pipeline, while preserving the visual
grammar of the legacy reference figures
(`figures/ats_energy_emissions_{region}_2025_2075.png`).

Visual grammar (frozen, matched cell-for-cell against
``scripts/build_refstyle_figures.py``):

  * figsize=(11.2, 3.4) — same canvas
  * font: Arial, pdf/ps fonttype=42
  * energy line color "#486878" (blue-gray), 2.2 pt solid
  * emissions line color "#8B0000" (dark red), 2.2 pt solid
  * ratio line color "#006000", 2.0 pt dotted
  * energy band: light grey fill 0.85, gray whiskers 0.55 with caps,
    sitting on the LEFT axis
  * emissions band: same dark-red, alpha 0.08, whiskers alpha 0.55,
    sitting on the RIGHT (twinx) axis
  * ax2.patch.set_visible(False) so the left-axis grey band stays
    visible underneath the twin
  * vertical dashed milestones at 2045 and 2075, color "0.6", lw 0.9
  * x ticks every 2 years, rotated 45 degrees
  * legend: top-center, 4 columns, frameon=False,
    bbox_to_anchor=(0.5, 1.02), legend ORDER:
      Total Power, Total Emissions, Emissions/Power Ratio, Uncertainty Range
  * title: "Annual ATS Energy Consumption and Emissions Prediction for
    {Region} (2025-2075)"  — kept identical to the cached reference
    figure (an en-dash is used to match the on-figure rendering)
  * axis labels: "Total Energy Consumption (TWh)" (left),
    "Total Emissions (kilo tons CO$_2$)" (right), "Year" (bottom)

Data source — what changed:

  * The legacy figures read
    ``results/{region}__policy-baseline__model-fixed_table_quantiles.csv``
    directly. The v9 dashboard does not show those numbers. Instead
    the v9 Scenario Explorer's primary "default" band is computed by
    ``v9_streamlit_app.core._weather_adjusted_quantiles_from_mc_runs(
        region, "baseline", "default")`` — it re-percentiles
    ``results/{region}__policy-baseline__bundle-default_mc_runs.csv``
    after applying the v8 annual weather Dirichlet to every (run, year).
    This script uses that exact function so the plotted band matches
    Figure A in the v9 Scenario Explorer.
  * The central trajectory (the solid line you see in the dashboard)
    is the v9 deterministic line — ``core.run_simulation(cfg, years=68)``
    on the baseline runtime config with ``attach_weather_region`` set,
    so the line carries the deterministic p_state weather centroid
    factor. This matches the deterministic overlay on the dashboard.
  * Restricted to 2025-2075 (the dashboard's display horizon).

Outputs:
  figs/figure6c_california_updated.{png,pdf,svg}
  figs/figure6f_ohio_updated.{png,pdf,svg}
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
V9_DIR = REPO / "v9_streamlit_app"
OUT_DIR = REPO / "figs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(V9_DIR) not in sys.path:
    sys.path.insert(0, str(V9_DIR))

# Import v9 dashboard core. ``run_simulation`` here is the v9 wrapper that
# applies the deterministic weather centroid; ``_weather_adjusted_quantiles
# _from_mc_runs`` is the function that powers Figure A's default band.
from v9_streamlit_app.core import (  # noqa: E402
    attach_weather_region,
    load_runtime_config,
    run_simulation,
    _weather_adjusted_quantiles_from_mc_runs,
)

# ------------------------------------------------------------------
# Style constants — copied verbatim from build_refstyle_figures.py so
# the redraw is style-identical.
# ------------------------------------------------------------------
plt.rcParams["font.family"] = "Arial"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

POWER_COLOR = "#486878"
EMISS_COLOR = "#8B0000"
RATIO_COLOR = "#006000"
UNC_FILL = "0.85"
UNC_EDGE = "0.55"

PLOT_YEAR_MIN = 2025
PLOT_YEAR_MAX = 2075
MILESTONE_YEARS = [2045, 2075]

ENERGY_COL = "ATS Total Power (kWh)"
EMISS_COL = "ATS Emissions (kg CO2)"

REGIONS = {
    "california": ("California", "figure6c_california_updated"),
    "ohio":       ("Ohio",       "figure6f_ohio_updated"),
}


def kWh_to_TWh(x):
    if isinstance(x, pd.Series):
        return x.astype(float) / 1.0e9
    return np.asarray(x, dtype=float) / 1.0e9


def kg_to_kt(x):
    if isinstance(x, pd.Series):
        return x.astype(float) / 1.0e6
    return np.asarray(x, dtype=float) / 1.0e6


# ------------------------------------------------------------------
# Data assembly: v9 deterministic line + v9 weather-adjusted MC band
# ------------------------------------------------------------------
def load_v9_trajectory(region: str) -> pd.DataFrame:
    """Return a per-year DataFrame indexed by Year with columns:
        energy_det_kwh, emiss_det_kg          — v9 deterministic line
        energy_p05_kwh, energy_p50_kwh, energy_p95_kwh
        emiss_p05_kg,   emiss_p50_kg,   emiss_p95_kg
    Restricted to PLOT_YEAR_MIN-PLOT_YEAR_MAX.
    """
    cfg = load_runtime_config(region, "baseline")
    attach_weather_region(cfg, region)
    det = run_simulation(cfg, years=68).set_index("Year")
    det = det.loc[(det.index >= PLOT_YEAR_MIN) & (det.index <= PLOT_YEAR_MAX)]

    qf = _weather_adjusted_quantiles_from_mc_runs(region, "baseline", "default")
    if qf is None or qf.empty:
        raise SystemExit(
            f"v9 weather-adjusted bundle quantiles unavailable for {region}; "
            f"expected results/{region}__policy-baseline__bundle-default_mc_runs.csv"
        )
    qf = qf.loc[(qf.index >= PLOT_YEAR_MIN) & (qf.index <= PLOT_YEAR_MAX)]

    out = pd.DataFrame(index=det.index)
    out["energy_det_kwh"] = det[ENERGY_COL].astype(float)
    out["emiss_det_kg"]   = det[EMISS_COL].astype(float)
    for src, dst in [
        (f"{ENERGY_COL}_p05", "energy_p05_kwh"),
        (f"{ENERGY_COL}_p50", "energy_p50_kwh"),
        (f"{ENERGY_COL}_p95", "energy_p95_kwh"),
        (f"{EMISS_COL}_p05",  "emiss_p05_kg"),
        (f"{EMISS_COL}_p50",  "emiss_p50_kg"),
        (f"{EMISS_COL}_p95",  "emiss_p95_kg"),
    ]:
        out[dst] = qf[src].astype(float)
    out.index.name = "Year"
    return out


# ------------------------------------------------------------------
# Plot — visual grammar locked to the legacy reference
# ------------------------------------------------------------------
def render_panel(traj: pd.DataFrame, region_label: str, out_prefix: str) -> dict:
    years = traj.index.to_numpy(dtype=float)

    # The plotted central line now equals the band median (p50). The
    # deterministic series is retained only for the validation table —
    # it is no longer drawn. This keeps the line and the band as a
    # single coherent statistical object.
    e_det = kWh_to_TWh(traj["energy_det_kwh"])
    e05   = kWh_to_TWh(traj["energy_p05_kwh"])
    e50   = kWh_to_TWh(traj["energy_p50_kwh"])
    e95   = kWh_to_TWh(traj["energy_p95_kwh"])

    em_det = kg_to_kt(traj["emiss_det_kg"])
    em05   = kg_to_kt(traj["emiss_p05_kg"])
    em50   = kg_to_kt(traj["emiss_p50_kg"])
    em95   = kg_to_kt(traj["emiss_p95_kg"])

    e_lo = np.minimum(e05, e95)
    e_hi = np.maximum(e05, e95)
    em_lo = np.minimum(em05, em95)
    em_hi = np.maximum(em05, em95)

    # Monotonicity gate: the band ordering must be p05 <= p50 <= p95
    # for every plotted year. Tiny float noise is tolerated by an
    # absolute slack (1e-9) before flagging.
    _slack = 1e-9
    bad = []
    for y, lo, mid, hi in zip(years, e05, e50, e95):
        if not (lo <= mid + _slack and mid <= hi + _slack):
            bad.append(("energy", int(y), float(lo), float(mid), float(hi)))
    for y, lo, mid, hi in zip(years, em05, em50, em95):
        if not (lo <= mid + _slack and mid <= hi + _slack):
            bad.append(("emissions", int(y), float(lo), float(mid), float(hi)))
    if bad:
        msg = "\n".join(
            f"  {kind} year={yr}: p05={lo:.6g} p50={mid:.6g} p95={hi:.6g}"
            for kind, yr, lo, mid, hi in bad[:10]
        )
        raise SystemExit(
            f"FAILED monotonicity check (p05 <= p50 <= p95) for {region_label}:\n{msg}"
        )

    # Ratio uses the SAME p50 series as the lines, so the green dotted
    # intensity = red_p50 / blue_p50. The visual rescaling onto the left
    # axis is unchanged from the legacy figure.
    ratio_kg_per_kwh = traj["emiss_p50_kg"].to_numpy(dtype=float) / np.maximum(
        traj["energy_p50_kwh"].to_numpy(dtype=float), 1e-12,
    )
    max_ratio = float(np.nanmax(ratio_kg_per_kwh)) if np.isfinite(ratio_kg_per_kwh).any() else 0.0
    e_top = float(np.nanmax(e50))
    ratio_scale = (e_top / max_ratio) if max_ratio > 0 else 1.0
    ratio_scaled = ratio_kg_per_kwh * ratio_scale

    fig, ax1 = plt.subplots(figsize=(11.2, 3.4))

    # Left axis: energy band + whiskers + line. Line is the MC p50, so
    # it sits inside the p05-p95 ribbon by construction.
    band_energy = ax1.fill_between(
        years, e_lo, e_hi,
        color=UNC_FILL, alpha=1.0, linewidth=0,
        label="Uncertainty Range", zorder=1,
    )
    yerr_e = np.vstack([e50 - e_lo, e_hi - e50])
    yerr_e = np.maximum(yerr_e, 0)  # belt-and-braces against tiny float noise
    ax1.errorbar(
        years, e50, yerr=yerr_e,
        fmt="none", ecolor=UNC_EDGE,
        elinewidth=0.9, capsize=2.0, capthick=0.9,
        alpha=0.9, zorder=2,
    )
    l_power, = ax1.plot(
        years, e50,
        color=POWER_COLOR, linewidth=2.2,
        label="Total Power", zorder=3,
    )
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Total Energy Consumption (TWh)")

    # Right (twin) axis: emissions band + whiskers + line
    ax2 = ax1.twinx()
    ax2.patch.set_visible(False)
    ax2.set_zorder(ax1.get_zorder() + 1)

    ax2.fill_between(
        years, em_lo, em_hi,
        color=EMISS_COLOR, alpha=0.08, linewidth=0, zorder=1,
    )
    yerr_em = np.vstack([em50 - em_lo, em_hi - em50])
    yerr_em = np.maximum(yerr_em, 0)
    ax2.errorbar(
        years, em50, yerr=yerr_em,
        fmt="none", ecolor=EMISS_COLOR,
        elinewidth=0.8, capsize=2.0, capthick=0.8,
        alpha=0.55, zorder=2,
    )
    l_emiss, = ax2.plot(
        years, em50,
        color=EMISS_COLOR, linewidth=2.2,
        label="Total Emissions", zorder=3,
    )
    ax2.set_ylabel("Total Emissions (kilo tons CO$_2$)")

    # Intensity (Emissions/Power) — green dotted, on the left axis but
    # rescaled to share visual range. Intentional: matches the legacy.
    l_ratio, = ax1.plot(
        years, ratio_scaled,
        color=RATIO_COLOR, linestyle=":", linewidth=2.0,
        label="Emissions/Power Ratio", zorder=4,
    )

    # Milestone vertical dashes at 2045 and 2075
    for y in MILESTONE_YEARS:
        if years.min() <= y <= years.max():
            ax1.axvline(y, color="0.6", linestyle="--", linewidth=0.9,
                        alpha=0.9, zorder=5)

    # Title at the very top of the canvas, legend tucked just beneath
    # it (matches the cached reference layout in
    # figures/ats_energy_emissions_{region}_2025_2075.png — title above,
    # legend below).
    fig.suptitle(
        "Annual ATS Energy Consumption and Emissions Prediction for "
        f"{region_label} ({int(years.min())}–{int(years.max())})",
        y=0.99,
    )

    if len(years) > 2 and np.all(np.diff(years) == 1):
        ax1.set_xticks(years[::2])
    ax1.tick_params(axis="x", labelrotation=45)

    handles = [l_power, l_emiss, l_ratio, band_energy]
    labels = [h.get_label() for h in handles]
    fig.legend(
        handles, labels,
        loc="upper center", ncol=4, frameon=False,
        bbox_to_anchor=(0.5, 0.95),
    )

    fig.tight_layout(rect=[0.02, 0.02, 0.98, 0.88])

    png_path = OUT_DIR / f"{out_prefix}.png"
    pdf_path = OUT_DIR / f"{out_prefix}.pdf"
    svg_path = OUT_DIR / f"{out_prefix}.svg"
    fig.savefig(png_path, dpi=600, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)

    print(f"[{region_label}] saved {png_path.relative_to(REPO)}")
    print(f"[{region_label}] saved {pdf_path.relative_to(REPO)}")
    print(f"[{region_label}] saved {svg_path.relative_to(REPO)}")

    # Return validation snapshot
    snap = {"region": region_label}
    for yr in (2045, 2075):
        snap[f"energy_p05_twh_{yr}"]  = float(e05.loc[yr])
        snap[f"energy_p50_twh_{yr}"]  = float(e50.loc[yr])
        snap[f"energy_p95_twh_{yr}"]  = float(e95.loc[yr])
        snap[f"energy_det_twh_{yr}"]  = float(e_det.loc[yr])
        snap[f"emiss_p05_kt_{yr}"]    = float(em05.loc[yr])
        snap[f"emiss_p50_kt_{yr}"]    = float(em50.loc[yr])
        snap[f"emiss_p95_kt_{yr}"]    = float(em95.loc[yr])
        snap[f"emiss_det_kt_{yr}"]    = float(em_det.loc[yr])
        snap[f"ratio_p50_kg_per_kwh_{yr}"] = float(
            ratio_kg_per_kwh[np.where(years == yr)[0][0]]
        )
    return snap


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------
# The Sankey extraction (scripts/extract_figure6_sankey_values_v9.py)
# uses the v9 DETERMINISTIC line. This figure now uses MC p50. The two
# central references differ; they are reported side-by-side below for
# consistency-checking purposes.
SANKEY_DETERMINISTIC_REFERENCE = {
    "California": {
        "energy_2045_twh":  6.046230664387228,
        "energy_2075_twh":  4.779879676944212,
        "emiss_2045_kt":    6543.978766058738,
        "emiss_2075_kt":    143.39639030832637,
    },
    "Ohio": {
        "energy_2045_twh":  1.0622900376027933,
        "energy_2075_twh":  1.371209707088766,
        "emiss_2045_kt":    1307.9721283257866,
        "emiss_2075_kt":    1580.9887060326587,
    },
}


def validate(snapshots: list[dict]) -> None:
    print("\nFigure-line series == MC p50; band == p05-p95.")
    print("Per-region 2045 / 2075 percentiles + deterministic-vs-p50 delta:\n")

    header = (f"{'region':>12} {'year':>5} | "
              f"{'energy p05':>10} {'energy p50':>10} {'energy p95':>10} "
              f"{'energy det':>10} {'Δdet-p50':>9} | "
              f"{'emiss p05':>9} {'emiss p50':>9} {'emiss p95':>9} "
              f"{'emiss det':>9} {'Δdet-p50':>9}")
    print(header)
    print("-" * len(header))

    fail = 0
    for s in snapshots:
        for yr in (2045, 2075):
            e05 = s[f"energy_p05_twh_{yr}"]; e50 = s[f"energy_p50_twh_{yr}"]; e95 = s[f"energy_p95_twh_{yr}"]
            edet = s[f"energy_det_twh_{yr}"]
            m05 = s[f"emiss_p05_kt_{yr}"]; m50 = s[f"emiss_p50_kt_{yr}"]; m95 = s[f"emiss_p95_kt_{yr}"]
            mdet = s[f"emiss_det_kt_{yr}"]
            de = edet - e50
            dm = mdet - m50
            print(f"{s['region']:>12} {yr:>5} | "
                  f"{e05:>10.4f} {e50:>10.4f} {e95:>10.4f} "
                  f"{edet:>10.4f} {de:>9.4f} | "
                  f"{m05:>9.2f} {m50:>9.2f} {m95:>9.2f} "
                  f"{mdet:>9.2f} {dm:>9.2f}")
            if not (e05 <= e50 + 1e-9 <= e95 + 2e-9):
                print(f"  ! energy ordering violated at {yr}")
                fail += 1
            if not (m05 <= m50 + 1e-9 <= m95 + 2e-9):
                print(f"  ! emissions ordering violated at {yr}")
                fail += 1

    if fail:
        raise SystemExit(f"\nFAILED: {fail} ordering violation(s)")

    print("\nAll plotted years satisfy p05 <= p50 <= p95 for both metrics.")
    print("\nDeterministic reference (Sankey extraction, scripts/"
          "extract_figure6_sankey_values_v9.py) is shown only for comparison; "
          "it is NOT plotted on the figure.")


if __name__ == "__main__":
    snapshots = []
    for region_key, (region_label, out_prefix) in REGIONS.items():
        traj = load_v9_trajectory(region_key)
        snapshots.append(render_panel(traj, region_label, out_prefix))
    validate(snapshots)
