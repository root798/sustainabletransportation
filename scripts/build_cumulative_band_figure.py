"""Build the rebuttal Extended Data figure: cumulative ATS CO2 band, CA + OH.

Generates `figures/cumulative_band.pdf` (and matching PNG) from the
seed-42 / N=200 L3 propagation stored in
`results/{region}__policy-baseline__bundle-default_mc_runs.csv`.

Two side-by-side panels (CA, OH). Primary axis: median C(t) line plus
[q_0.05, q_0.95] band in Mt CO2. Secondary axis: relative band width
W_C(t) = (q95 - q05) / q50 plotted as a thin line so reviewers can
visually inspect both the absolute (widening) and relative (roughly
flat) behaviour of the cumulative band.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "v5_streamlit_app"))

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from figure_style import (  # type: ignore
    NATURE_CATEGORICAL,
    apply_matplotlib_style,
)

REGIONS = [
    ("California", "results/california__policy-baseline__bundle-default_mc_runs.csv"),
    ("Ohio",       "results/ohio__policy-baseline__bundle-default_mc_runs.csv"),
]
YEAR_MIN, YEAR_MAX = 2025, 2075

OUT_DIR = REPO / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH = OUT_DIR / "cumulative_band.pdf"
PNG_PATH = OUT_DIR / "cumulative_band.png"


def cumulative_quantiles(mc_path: Path) -> pd.DataFrame:
    df = pd.read_csv(mc_path)
    M = (
        df.pivot_table(index="Year", columns="run_id", values="ATS Emissions (kg CO2)")
        .sort_index()
    )
    M = M.loc[(M.index >= YEAR_MIN) & (M.index <= YEAR_MAX)]
    C = M.cumsum(axis=0)
    out = pd.DataFrame(
        {
            "q05": C.quantile(0.05, axis=1),
            "q50": C.quantile(0.50, axis=1),
            "q95": C.quantile(0.95, axis=1),
        }
    )
    out["abs_band"] = out["q95"] - out["q05"]
    out["W_C"] = out["abs_band"] / out["q50"]
    return out


def kg_to_mt(x: float | np.ndarray) -> float | np.ndarray:
    return x * 1e-9  # kg -> Mt


def main() -> None:
    apply_matplotlib_style()

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4), sharey=False)

    band_color = NATURE_CATEGORICAL["primary"]
    median_color = NATURE_CATEGORICAL["primary"]
    width_color = NATURE_CATEGORICAL["secondary"]

    for ax, (region, rel_path) in zip(axes, REGIONS):
        q = cumulative_quantiles(REPO / rel_path)
        years = q.index.values

        ax.fill_between(
            years,
            kg_to_mt(q["q05"].values),
            kg_to_mt(q["q95"].values),
            color=band_color,
            alpha=0.20,
            linewidth=0,
            label=r"$[q_{0.05}, q_{0.95}]$",
        )
        ax.plot(
            years,
            kg_to_mt(q["q50"].values),
            color=median_color,
            linewidth=1.6,
            label=r"$q_{0.50}$",
        )
        ax.set_xlim(YEAR_MIN, YEAR_MAX)
        ax.set_xlabel("Year")
        ax.set_ylabel(r"Cumulative ATS CO$_2$ (Mt)")
        ax.set_title(region, fontsize=10)
        ax.set_xticks([2025, 2035, 2045, 2055, 2065, 2075])
        ax.grid(axis="y", linestyle=":", alpha=0.30)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax2 = ax.twinx()
        ax2.plot(
            years,
            q["W_C"].values,
            color=width_color,
            linewidth=1.0,
            linestyle="--",
            label=r"$W_C(t)$",
        )
        ax2.set_ylabel(r"Relative band width $W_C(t)$", color=width_color)
        ax2.tick_params(axis="y", colors=width_color)
        ax2.spines["top"].set_visible(False)
        ax2.set_ylim(0.0, max(0.6, q["W_C"].max() * 1.15))

        # Annotate cumulative absolute band growth in the lower-right corner
        first_band = q["abs_band"].iloc[0]
        last_band = q["abs_band"].iloc[-1]
        growth_factor = last_band / first_band if first_band > 0 else float("nan")
        ax.text(
            0.98,
            0.05,
            (
                rf"$|q_{{0.95}}-q_{{0.05}}|$ "
                rf"$\times {growth_factor:.1f}$"
                "\n"
                rf"({YEAR_MIN}$\to${YEAR_MAX})"
            ),
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=7.5,
            color=NATURE_CATEGORICAL["neutral"],
        )

    legend_handles = [
        Line2D([0], [0], color=median_color, linewidth=1.6, label=r"$q_{0.50}(C(t))$"),
        Patch(color=band_color, alpha=0.20, label=r"$[q_{0.05}, q_{0.95}](C(t))$"),
        Line2D([0], [0], color=width_color, linewidth=1.0, linestyle="--",
               label=r"$W_C(t)$ (right axis)"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
        fontsize=8,
    )

    fig.tight_layout(rect=(0.0, 0.06, 1.0, 1.0))
    fig.savefig(PDF_PATH, dpi=300, bbox_inches="tight")
    fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
    print(f"[cumulative_band] wrote {PDF_PATH.relative_to(REPO)}")
    print(f"[cumulative_band] wrote {PNG_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
