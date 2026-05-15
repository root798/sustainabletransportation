"""
Build Figure-6d-style annual ATS energy & emissions plots for California and Ohio.

Reads the latest baseline / bundle-default Monte Carlo quantile CSVs and produces
a dual-axis chart with p05-p95 uncertainty bands, every-other-year error bars,
dashed reference verticals at 2045 and 2075, and a horizontal legend above the
plot. Saves PNG (300 dpi) and PDF for each region under figures/.

Run from repo root:
    python scripts/build_figure6d_state.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

# ---------------------------------------------------------------------------
# Top-level styling constants (tweak here)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = REPO_ROOT / "figures"

REGIONS = {
    "california": "California",
    "ohio": "Ohio",
}

YEAR_MIN = 2025
YEAR_MAX = 2075

# Colors
COLOR_POWER = "#5A6B7B"       # slate / steel blue
COLOR_EMISSIONS = "#A52A2A"   # brick red
COLOR_RATIO = "#2E5E2E"       # dark forest green
COLOR_BAND_POWER = "#5A6B7B"
COLOR_BAND_EMISSIONS = "#D98B8B"  # light pinkish-red
COLOR_REF_LINE = "#B0B0B0"
COLOR_SPINE = "#888888"

# Line / marker / band styling
LW_MAIN = 1.6
LW_RATIO = 1.4
LW_REF = 1.0
LW_SPINE = 0.6
ALPHA_BAND = 0.18
ERR_CAPSIZE = 3.0
ERR_ELW = 0.8
ERR_EVERY_N_YEARS = 2  # error bars every N years starting at YEAR_MIN

# Reference verticals
REF_YEARS = [2045, 2075]

# Font sizes
FS_TITLE = 13
FS_AXIS = 11
FS_TICK = 9
FS_LEGEND = 10

# Figure size
FIG_W = 14
FIG_H = 3.8
DPI_PNG = 300

# Unit conversions
KWH_PER_TWH = 1e9          # kWh -> TWh
KG_PER_KILOTON = 1e6       # kg  -> kilotons


# ---------------------------------------------------------------------------
# Caption template
# ---------------------------------------------------------------------------
CAPTION_TEMPLATE = (
    "(d) Prediction of {Region}'s state-level annual ATS energy consumption "
    "(in TWh) and associated CO$_2$ emissions (in kilotons) from 2025 to 2075. "
    "The solid grey line represents \\textbf{{total energy consumption}}, the "
    "solid red line depicts total CO$_2$ emissions, and the dotted green line "
    "illustrates the \\textbf{{CO$_2$ emissions intensity}} "
    "(emissions-to-energy ratio)."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def quantile_csv_path(region: str) -> Path:
    return (
        RESULTS_DIR
        / f"{region}__policy-baseline__bundle-default_quantiles.csv"
    )


def load_region(region: str) -> pd.DataFrame:
    path = quantile_csv_path(region)
    if not path.exists():
        raise FileNotFoundError(f"Missing quantile CSV: {path}")
    df = pd.read_csv(path)

    # Sanity print
    print(f"\n=== {region} ===")
    print(f"path: {path}")
    print(f"columns ({len(df.columns)}): {df.columns.tolist()[:12]}  ...")
    print("head(3):")
    print(df.head(3).to_string(index=False))

    needed = [
        "Year",
        "ATS Total Power (kWh)_p05",
        "ATS Total Power (kWh)_p50",
        "ATS Total Power (kWh)_p95",
        "ATS Emissions (kg CO2)_p05",
        "ATS Emissions (kg CO2)_p50",
        "ATS Emissions (kg CO2)_p95",
    ]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"{region}: missing required columns {missing}")

    df = df.loc[(df["Year"] >= YEAR_MIN) & (df["Year"] <= YEAR_MAX)].copy()
    df = df.sort_values("Year").reset_index(drop=True)

    # Monotonicity assertion
    for base in ["ATS Total Power (kWh)", "ATS Emissions (kg CO2)"]:
        p05 = df[f"{base}_p05"].to_numpy()
        p50 = df[f"{base}_p50"].to_numpy()
        p95 = df[f"{base}_p95"].to_numpy()
        bad = np.where(~((p05 <= p50 + 1e-9) & (p50 <= p95 + 1e-9)))[0]
        if len(bad) > 0:
            yr = df["Year"].iloc[bad[0]]
            raise ValueError(
                f"{region}: p05<=p50<=p95 violated for '{base}' at year {yr}"
            )

    return df


def derive_series(df: pd.DataFrame) -> dict:
    years = df["Year"].to_numpy()

    p_p05 = df["ATS Total Power (kWh)_p05"].to_numpy() / KWH_PER_TWH
    p_p50 = df["ATS Total Power (kWh)_p50"].to_numpy() / KWH_PER_TWH
    p_p95 = df["ATS Total Power (kWh)_p95"].to_numpy() / KWH_PER_TWH

    e_p05 = df["ATS Emissions (kg CO2)_p05"].to_numpy() / KG_PER_KILOTON
    e_p50 = df["ATS Emissions (kg CO2)_p50"].to_numpy() / KG_PER_KILOTON
    e_p95 = df["ATS Emissions (kg CO2)_p95"].to_numpy() / KG_PER_KILOTON

    # Ratio: kg CO2 per kWh, computed from medians
    ratio = (df["ATS Emissions (kg CO2)_p50"].to_numpy()
             / df["ATS Total Power (kWh)_p50"].to_numpy())

    return {
        "years": years,
        "p_p05": p_p05, "p_p50": p_p50, "p_p95": p_p95,
        "e_p05": e_p05, "e_p50": e_p50, "e_p95": e_p95,
        "ratio": ratio,
    }


def print_sanity(region: str, s: dict) -> None:
    years = s["years"]
    peak_idx_p = int(np.argmax(s["p_p50"]))
    peak_idx_e = int(np.argmax(s["e_p50"]))
    yr_2075 = int(np.where(years == 2075)[0][0])
    print(
        f"[{region}] peak power year={int(years[peak_idx_p])} "
        f"value={s['p_p50'][peak_idx_p]:.3f} TWh | "
        f"peak emissions year={int(years[peak_idx_e])} "
        f"value={s['e_p50'][peak_idx_e]:.1f} ktCO2 | "
        f"2075 emissions={s['e_p50'][yr_2075]:.1f} ktCO2"
    )


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
def make_figure(region_key: str, region_label: str, s: dict) -> tuple[Path, Path]:
    years = s["years"]
    err_mask = ((years - YEAR_MIN) % ERR_EVERY_N_YEARS == 0)

    fig, ax_p = plt.subplots(figsize=(FIG_W, FIG_H))
    ax_e = ax_p.twinx()

    # Power band + line on left axis
    ax_p.fill_between(
        years, s["p_p05"], s["p_p95"],
        color=COLOR_BAND_POWER, alpha=ALPHA_BAND, linewidth=0,
        zorder=1,
    )
    line_p, = ax_p.plot(
        years, s["p_p50"],
        color=COLOR_POWER, lw=LW_MAIN, label="Total Power", zorder=3,
    )
    ax_p.errorbar(
        years[err_mask], s["p_p50"][err_mask],
        yerr=[s["p_p50"][err_mask] - s["p_p05"][err_mask],
              s["p_p95"][err_mask] - s["p_p50"][err_mask]],
        fmt="none", ecolor=COLOR_POWER, elinewidth=ERR_ELW,
        capsize=ERR_CAPSIZE, capthick=ERR_ELW, zorder=4,
    )

    # Emissions band + line on right axis
    ax_e.fill_between(
        years, s["e_p05"], s["e_p95"],
        color=COLOR_BAND_EMISSIONS, alpha=ALPHA_BAND, linewidth=0,
        zorder=1,
    )
    line_e, = ax_e.plot(
        years, s["e_p50"],
        color=COLOR_EMISSIONS, lw=LW_MAIN, label="Total Emissions", zorder=3,
    )
    ax_e.errorbar(
        years[err_mask], s["e_p50"][err_mask],
        yerr=[s["e_p50"][err_mask] - s["e_p05"][err_mask],
              s["e_p95"][err_mask] - s["e_p50"][err_mask]],
        fmt="none", ecolor=COLOR_EMISSIONS, elinewidth=ERR_ELW,
        capsize=ERR_CAPSIZE, capthick=ERR_ELW, zorder=4,
    )

    # Ratio on a third hidden axis so it sits in upper portion of frame
    ax_r = ax_p.twinx()
    ax_r.spines["right"].set_visible(False)
    ax_r.spines["top"].set_visible(False)
    ax_r.spines["left"].set_visible(False)
    ax_r.spines["bottom"].set_visible(False)
    ax_r.set_yticks([])
    ratio_min = float(np.min(s["ratio"]))
    ratio_max = float(np.max(s["ratio"]))
    pad = max((ratio_max - ratio_min) * 0.4, 1e-6)
    # Place the ratio so its line sits in the upper third of the frame:
    # bottom of axis = ratio_min - 1.4 * range, top = ratio_max + 0.15 * range
    ax_r.set_ylim(ratio_min - 1.6 * pad, ratio_max + 0.20 * pad)
    line_r, = ax_r.plot(
        years, s["ratio"],
        color=COLOR_RATIO, lw=LW_RATIO, linestyle=":",
        label="Emissions/Power Ratio", zorder=3,
    )

    # Reference verticals
    ymin, ymax = ax_p.get_ylim()
    for ry in REF_YEARS:
        ax_p.axvline(ry, color=COLOR_REF_LINE, linestyle="--",
                     linewidth=LW_REF, zorder=0)

    # Axes labels & title
    ax_p.set_xlabel("Year", fontsize=FS_AXIS)
    ax_p.set_ylabel("Total Energy Consumption (TWh)", fontsize=FS_AXIS,
                    color="#222")
    ax_e.set_ylabel("Total Emissions (kilo tons CO$_2$)", fontsize=FS_AXIS,
                    color="#222")
    ax_p.set_title(
        f"Annual ATS Energy Consumption and Emissions Prediction for "
        f"{region_label} (2025–2075)",
        fontsize=FS_TITLE, pad=24,
    )

    # X ticks every odd year
    odd_years = [y for y in range(YEAR_MIN, YEAR_MAX + 1) if y % 2 == 1]
    ax_p.set_xticks(odd_years)
    ax_p.set_xticklabels([str(y) for y in odd_years],
                         rotation=45, fontsize=FS_TICK)
    for lbl in ax_p.get_yticklabels():
        lbl.set_fontsize(FS_TICK)
    for lbl in ax_e.get_yticklabels():
        lbl.set_fontsize(FS_TICK)

    # Spines
    for ax in (ax_p, ax_e):
        for side in ("top", "right", "bottom", "left"):
            ax.spines[side].set_color(COLOR_SPINE)
            ax.spines[side].set_linewidth(LW_SPINE)
    ax_p.set_facecolor("white")
    ax_p.grid(False)
    ax_e.grid(False)

    # X limits clipped tight
    ax_p.set_xlim(YEAR_MIN - 0.5, YEAR_MAX + 0.5)

    # Legend (4 entries, single horizontal row, above plot)
    band_proxy = Patch(facecolor=COLOR_SPINE, alpha=0.30,
                       edgecolor="none", label="Uncertainty Range")
    handles = [line_p, line_e, line_r, band_proxy]
    labels = [h.get_label() for h in handles]
    ax_p.legend(
        handles, labels,
        loc="center", bbox_to_anchor=(0.5, 1.02), ncol=4,
        frameon=False, fontsize=FS_LEGEND, handlelength=2.4,
    )

    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIGURES_DIR / f"ats_energy_emissions_{region_key}_2025_2075.png"
    pdf_path = FIGURES_DIR / f"ats_energy_emissions_{region_key}_2025_2075.pdf"
    fig.savefig(png_path, dpi=DPI_PNG, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return png_path, pdf_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    mpl.rcParams["font.family"] = "sans-serif"
    mpl.rcParams["font.sans-serif"] = ["Arial", "Calibri", "Helvetica", "DejaVu Sans"]
    mpl.rcParams["axes.unicode_minus"] = False

    saved: list[Path] = []
    captions: dict[str, str] = {}

    for region_key, region_label in REGIONS.items():
        df = load_region(region_key)
        s = derive_series(df)
        print_sanity(region_key, s)
        png_path, pdf_path = make_figure(region_key, region_label, s)
        saved.extend([png_path, pdf_path])
        captions[region_label] = CAPTION_TEMPLATE.format(Region=region_label)

    print("\n=== saved files ===")
    for p in saved:
        print(p.resolve())

    print("\n=== LaTeX captions ===")
    for region_label, cap in captions.items():
        print(f"\n--- {region_label} ---")
        print(cap)

    return 0


if __name__ == "__main__":
    sys.exit(main())
