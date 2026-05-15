"""Regenerate the legacy reference-style CA + OH figures with the current
validated baseline quantile CSVs, restricted to the 2025-2075 window.

Style source: adapted verbatim from the `plot_refstyle_fixed` function in
`CLEAR_ATS_uncertainty_notebook.ipynb` (cell "PLOT FIX -- make uncertainty
band visible under twinx ..."). All colors, line styles, legend order,
legend placement, axis structure, title format, and milestone vlines are
preserved.

Data source: the CURRENT validated baseline quantile CSVs under results/:
    results/california__policy-baseline__model-fixed_table_quantiles.csv
    results/ohio__policy-baseline__model-fixed_table_quantiles.csv
(these replace the legacy results_notebook/ inputs). U.S. Average is NOT
regenerated (paper-safety quarantine).

Outputs:
    reports/paper_support/reference_style/{region}_2025_2075_refstyle.pdf
    reports/paper_support/reference_style/{region}_2025_2075_refstyle.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.family"] = "Arial"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

# ------------------------------------------------------------------
# Style constants -- identical to the legacy notebook
# ------------------------------------------------------------------
POWER_COLOR = "#486878"
EMISS_COLOR = "#8B0000"
RATIO_COLOR = "#006000"

UNC_FILL = "0.85"   # light grey fill
UNC_EDGE = "0.55"   # darker grey edge/error bars

PLOT_YEAR_MIN = 2025
PLOT_YEAR_MAX = 2075              # legacy was 2085; this revision stops at 2075
MILESTONE_YEARS = [2045, 2075]    # keep the same milestone markers
POLICY_NAME = "baseline"

ENERGY_BASE = "ATS Total Power (kWh)"
EMISS_BASE = "ATS Emissions (kg CO2)"

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
OUT_DIR = REPO / "reports" / "paper_support" / "reference_style"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Unit conversions -- kept identical to legacy notebook
# ------------------------------------------------------------------
def kWh_to_TWh(x: np.ndarray) -> np.ndarray:
    return x / 1e9          # 1 TWh = 1e9 kWh


def kg_to_kilotons(x: np.ndarray) -> np.ndarray:
    return x / 1e6          # 1 kt = 1e6 kg


def subset_and_sort(qdf: pd.DataFrame, y_min: int, y_max: int) -> pd.DataFrame:
    q = qdf[(qdf["Year"] >= y_min) & (qdf["Year"] <= y_max)].copy()
    return q.sort_values("Year").reset_index(drop=True)


# ------------------------------------------------------------------
# Plot function -- copied from legacy notebook, unchanged logic
# ------------------------------------------------------------------
def plot_refstyle_fixed(qdf: pd.DataFrame, region_label: str, out_prefix: str) -> tuple[Path, Path]:
    q = subset_and_sort(qdf, PLOT_YEAR_MIN, PLOT_YEAR_MAX)

    years = q["Year"].to_numpy(dtype=float)

    e05 = kWh_to_TWh(q[f"{ENERGY_BASE}_p05"].to_numpy(dtype=float))
    e50 = kWh_to_TWh(q[f"{ENERGY_BASE}_p50"].to_numpy(dtype=float))
    e95 = kWh_to_TWh(q[f"{ENERGY_BASE}_p95"].to_numpy(dtype=float))

    em05 = kg_to_kilotons(q[f"{EMISS_BASE}_p05"].to_numpy(dtype=float))
    em50 = kg_to_kilotons(q[f"{EMISS_BASE}_p50"].to_numpy(dtype=float))
    em95 = kg_to_kilotons(q[f"{EMISS_BASE}_p95"].to_numpy(dtype=float))

    spread_energy = np.nanmax(np.abs(e95 - e05))
    spread_emiss = np.nanmax(np.abs(em95 - em05))
    print(f"[{region_label}] max energy band thickness (TWh): {spread_energy:.6f}")
    print(f"[{region_label}] max emiss  band thickness (kt):  {spread_emiss:.6f}")

    e_lo = np.minimum(e05, e95)
    e_hi = np.maximum(e05, e95)

    m = (
        np.isfinite(years) & np.isfinite(e_lo) & np.isfinite(e_hi)
        & np.isfinite(e50) & np.isfinite(em50)
    )
    years = years[m]
    e_lo, e_hi, e50 = e_lo[m], e_hi[m], e50[m]
    em05, em50, em95 = em05[m], em50[m], em95[m]

    # Ratio in physical units (kg/kWh); scaled onto left axis for visual only.
    e_kWh = q.loc[m, f"{ENERGY_BASE}_p50"].to_numpy(dtype=float)
    em_kg = q.loc[m, f"{EMISS_BASE}_p50"].to_numpy(dtype=float)
    ratio_raw = np.divide(em_kg, np.maximum(e_kWh, 1e-12))  # kg/kWh
    max_ratio = np.nanmax(ratio_raw) if np.isfinite(ratio_raw).any() else 0.0
    ratio_scale = (np.nanmax(e50) / max_ratio) if max_ratio > 0 else 1.0
    ratio_scaled = ratio_raw * ratio_scale

    fig, ax1 = plt.subplots(figsize=(11.2, 3.4))

    # Energy uncertainty band + whiskers.
    band_energy = ax1.fill_between(
        years, e_lo, e_hi, color=UNC_FILL, alpha=1.0, linewidth=0,
        label="Uncertainty Range", zorder=1,
    )
    yerr_e = np.vstack([e50 - e_lo, e_hi - e50])
    ax1.errorbar(
        years, e50, yerr=yerr_e,
        fmt="none", ecolor=UNC_EDGE, elinewidth=0.9, capsize=2.0, capthick=0.9,
        alpha=0.9, zorder=2,
    )

    l_power, = ax1.plot(
        years, e50, color=POWER_COLOR, linewidth=2.2, label="Total Power", zorder=3,
    )
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Total Energy Consumption (TWh)")

    # Twin axis for emissions (transparent so left-axis grey band stays visible).
    ax2 = ax1.twinx()
    ax2.patch.set_visible(False)
    ax2.set_zorder(ax1.get_zorder() + 1)

    ax2.fill_between(
        years, np.minimum(em05, em95), np.maximum(em05, em95),
        color=EMISS_COLOR, alpha=0.08, linewidth=0, zorder=1,
    )
    yerr_em = np.vstack([em50 - np.minimum(em05, em95), np.maximum(em05, em95) - em50])
    ax2.errorbar(
        years, em50, yerr=yerr_em,
        fmt="none", ecolor=EMISS_COLOR, elinewidth=0.8, capsize=2.0, capthick=0.8,
        alpha=0.55, zorder=2,
    )
    l_emiss, = ax2.plot(
        years, em50, color=EMISS_COLOR, linewidth=2.2, label="Total Emissions", zorder=3,
    )
    ax2.set_ylabel("Total Emissions (kilo tons CO2)")

    l_ratio, = ax1.plot(
        years, ratio_scaled, color=RATIO_COLOR, linestyle=":", linewidth=2.0,
        label="Emissions/Power Ratio", zorder=4,
    )

    for y in MILESTONE_YEARS:
        if years.min() <= y <= years.max():
            ax1.axvline(y, color="0.6", linestyle="--", linewidth=0.9, alpha=0.9, zorder=5)

    ax1.set_title(
        f"Annual ATS Energy Consumption and Emissions Prediction for "
        f"{region_label} ({int(years.min())}-{int(years.max())})"
    )

    # X ticks every 2 years if annual series.
    if len(years) > 2 and np.all(np.diff(years) == 1):
        ax1.set_xticks(years[::2])
    ax1.tick_params(axis="x", labelrotation=45)

    handles = [l_power, l_emiss, l_ratio, band_energy]
    labels = [h.get_label() for h in handles]
    fig.legend(
        handles, labels, loc="upper center", ncol=4, frameon=False,
        bbox_to_anchor=(0.5, 1.02),
    )

    fig.tight_layout(rect=[0.02, 0.02, 0.98, 0.90])

    pdf_path = OUT_DIR / f"{out_prefix}.pdf"
    png_path = OUT_DIR / f"{out_prefix}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=600, bbox_inches="tight")
    plt.close(fig)

    print("Saved:", pdf_path)
    print("Saved:", png_path)
    return pdf_path, png_path


# ------------------------------------------------------------------
# Current-baseline quantile CSV paths
# ------------------------------------------------------------------
REGIONS = {
    "california": "California",
    "ohio": "Ohio",
}


def _quantile_csv(region_key: str) -> Path:
    return RESULTS / f"{region_key}__policy-{POLICY_NAME}__model-fixed_table_quantiles.csv"


if __name__ == "__main__":
    for region_key, region_label in REGIONS.items():
        q_path = _quantile_csv(region_key)
        if not q_path.exists():
            raise FileNotFoundError(f"Missing quantile CSV: {q_path}")
        qdf = pd.read_csv(q_path)
        out_prefix = f"{region_key}_2025_2075_refstyle"
        plot_refstyle_fixed(qdf, region_label=region_label, out_prefix=out_prefix)
