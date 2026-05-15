"""Regenerate every v5 static figure using the Nature-grade style module.

Outputs per region go to:
  figures/fig4_emissions_band_{region}_{date}.{png,pdf}
  figures/fig5_top_drivers_{region}_{year}_{date}.{png,pdf}
  figures/fig6_layer_contribution_{region}_{date}.{png,pdf}

Sizes are Nature Communications column widths (single = 88 mm, 1.5-column
= 136 mm). PDFs are vector; PNGs are 300 DPI raster.
"""
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
V5 = REPO / "v5_streamlit_app"
sys.path.insert(0, str(V5))

from core import (  # noqa: E402
    NATURE_CATEGORICAL,
    NATURE_LAYER,
    apply_matplotlib_style,
    interpretation_boundary,
    load_bundle_quantiles,
    load_layer_contribution_experiment,
    load_parameter_contribution_experiment,
)
from figure_style import (  # noqa: E402
    AXIS_COLOR,
    GRID_COLOR,
    TICK_LENGTH,
    TICK_WIDTH,
    figsize_1_5_column,
    figsize_single_column,
)

FIG_DIR = REPO / "figures"
FIG_DIR.mkdir(exist_ok=True)

METRIC = "ATS Emissions (kg CO2)"
TODAY = _dt.date.today().isoformat()


def _save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    png = FIG_DIR / f"{stem}_{TODAY}.png"
    pdf = FIG_DIR / f"{stem}_{TODAY}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png, pdf


def _scale_em(series: pd.Series) -> tuple[pd.Series, str, float]:
    mx = float(series.abs().max())
    if mx >= 1e9:
        return series / 1e9, "Mt CO$_2$ yr$^{-1}$", 1e9
    if mx >= 1e6:
        return series / 1e6, "kt CO$_2$ yr$^{-1}$", 1e6
    return series, "kg CO$_2$ yr$^{-1}$", 1.0


def fig_a_emissions_band(region: str, bundle: str) -> tuple[Path, Path] | None:
    qf = load_bundle_quantiles(region, "baseline", bundle)
    if qf is None:
        return None
    p05c, p50c, p95c = f"{METRIC}_p05", f"{METRIC}_p50", f"{METRIC}_p95"
    if any(c not in qf.columns for c in (p05c, p50c, p95c)):
        return None

    s05, unit, fac = _scale_em(qf[p05c])
    s50 = qf[p50c] / fac
    s95 = qf[p95c] / fac
    ib = interpretation_boundary(qf, metric=METRIC)
    by = ib.get("boundary_year")

    primary = NATURE_CATEGORICAL["primary"]
    accent = NATURE_CATEGORICAL["accent"]
    neutral = NATURE_CATEGORICAL["neutral"]

    fig, ax = plt.subplots(figsize=figsize_1_5_column())
    x = qf.index.values

    if by is not None and by >= x.min():
        ax.axvspan(by, x.max(), facecolor=neutral, alpha=0.05, zorder=0)

    ax.fill_between(x, s05.values, s95.values, color=primary, alpha=0.18,
                    linewidth=0, label="p05 to p95")
    ax.plot(x, s50.values, color=primary, linewidth=1.4,
            label="Median (p50)")

    if by is not None:
        ax.axvline(by, color=accent, linewidth=0.8, linestyle="--")
        ax.annotate(
            f"Interpretation boundary ({by})",
            xy=(by, s95.max() * 0.98), xytext=(4, 0),
            textcoords="offset points", color=accent, fontsize=8,
            ha="left", va="top",
        )

    ax.set_xlabel("Year")
    ax.set_ylabel(f"Annual emissions ({unit})")
    ax.xaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(5))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%g"))
    ax.tick_params(which="minor", length=TICK_LENGTH * 0.6,
                   width=TICK_WIDTH * 0.8, color=AXIS_COLOR)
    leg = ax.legend(frameon=False, loc="upper left", fontsize=8)
    for h in leg.legend_handles:
        if hasattr(h, "set_alpha"):
            h.set_alpha(None)

    stem = f"fig4_emissions_band_{region}_{bundle}"
    return _save(fig, stem)


def fig_b_top_drivers(region: str, year: int) -> tuple[Path, Path] | None:
    pcx = load_parameter_contribution_experiment()
    if pcx is None or pcx.empty:
        return None
    sub = pcx[(pcx["region"] == region) & (pcx["year"] == year)].copy()
    if sub.empty:
        return None
    sub = sub.sort_values("width_over_median", ascending=True)
    colors = [NATURE_LAYER.get(ly, NATURE_CATEGORICAL["neutral"])
              for ly in sub["layer"]]

    # Abbreviate the two compound IDs so the y-axis does not overflow
    def _short(pid: str) -> str:
        if pid == "F06_F07_F08_ecav_per_level":
            return "F06-F08"
        if pid == "F12_F13_F14_sti_per_level":
            return "F12-F14"
        return pid
    y_labels = [_short(p) for p in sub["param_id"]]

    fig, ax = plt.subplots(figsize=figsize_1_5_column())
    ypos = np.arange(len(sub))
    ax.barh(ypos, sub["width_over_median"], color=colors,
            edgecolor="none", alpha=0.9)
    ax.set_yticks(ypos)
    ax.set_yticklabels(y_labels, fontname="monospace", fontsize=8)

    max_v = float(sub["width_over_median"].max())
    for y, v in zip(ypos, sub["width_over_median"]):
        if v >= max_v * 0.6:
            ax.text(v * 0.98, y, f"{v:.2f}",
                    va="center", ha="right", color="white", fontsize=8)
        else:
            ax.text(v, y, f"  {v:.2f}",
                    va="center", ha="left", color=AXIS_COLOR, fontsize=8)

    ax.set_xlabel("(p95 − p05) / p50")
    ax.set_ylabel("")
    ax.grid(axis="x", which="major", color=GRID_COLOR, linestyle=":",
            alpha=0.3)
    # Legend
    import matplotlib.patches as mpatches
    handles = [mpatches.Patch(color=NATURE_LAYER[l], label=l)
               for l in ("L1", "L2", "L3")]
    ax.legend(handles=handles, frameon=False, fontsize=8,
              loc="lower right", bbox_to_anchor=(1.0, 0.0))

    stem = f"fig5_top_drivers_{region}_{year}"
    return _save(fig, stem)


def fig_c_layer_contribution(region: str) -> tuple[Path, Path] | None:
    lcx = load_layer_contribution_experiment()
    if lcx is None or lcx.empty:
        return None
    sub = lcx[(lcx["region"] == region)
              & (lcx["scenario"].isin(["L1_only", "L2_only", "L3_only"]))]
    if sub.empty:
        return None
    pivot = sub.pivot_table(index="year", columns="scenario",
                             values="width_over_median")
    years = pivot.index.astype(int).values
    width = 0.28

    fig, ax = plt.subplots(figsize=figsize_1_5_column())
    for i, (scen, layer_code) in enumerate(
            [("L1_only", "L1"), ("L2_only", "L2"), ("L3_only", "L3")]):
        if scen in pivot.columns:
            vals = pivot[scen].values
            offsets = (i - 1) * width
            bars = ax.bar(np.arange(len(years)) + offsets, vals, width,
                          color=NATURE_LAYER[layer_code],
                          alpha=0.9, label=layer_code, edgecolor="none")
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}",
                        ha="center", va="bottom", fontsize=7,
                        color=AXIS_COLOR)

    ax.set_xticks(np.arange(len(years)))
    ax.set_xticklabels([str(y) for y in years])
    ax.set_xlabel("Year")
    ax.set_ylabel("Layer-only (p95 − p05) / p50")
    ax.legend(ncol=3, frameon=False, fontsize=8,
              loc="upper center", bbox_to_anchor=(0.5, -0.18))
    ax.margins(x=0.05)

    stem = f"fig6_layer_contribution_{region}"
    return _save(fig, stem)


def main() -> None:
    apply_matplotlib_style()
    manifest_rows: list[dict] = []
    for region in ("california", "ohio"):
        for bundle in ("default", "paper-safe"):
            res = fig_a_emissions_band(region, bundle)
            if res:
                png, pdf = res
                manifest_rows.append({
                    "Figure": f"Figure A ({region}, {bundle})",
                    "Target manuscript slot": "Figure 4 or Extended Data",
                    "PDF": pdf.relative_to(REPO).as_posix(),
                    "PNG": png.relative_to(REPO).as_posix(),
                    "Size (mm)": "136 × 88 (1.5-column)",
                    "DPI": 300,
                })
        for year in (2030, 2050, 2075):
            res = fig_b_top_drivers(region, year)
            if res:
                png, pdf = res
                manifest_rows.append({
                    "Figure": f"Figure B ({region}, {year})",
                    "Target manuscript slot": "Figure 5 or Extended Data",
                    "PDF": pdf.relative_to(REPO).as_posix(),
                    "PNG": png.relative_to(REPO).as_posix(),
                    "Size (mm)": "136 × 88 (1.5-column)",
                    "DPI": 300,
                })
        res = fig_c_layer_contribution(region)
        if res:
            png, pdf = res
            manifest_rows.append({
                "Figure": f"Figure C ({region})",
                "Target manuscript slot": "Figure 6 or Extended Data",
                "PDF": pdf.relative_to(REPO).as_posix(),
                "PNG": png.relative_to(REPO).as_posix(),
                "Size (mm)": "136 × 88 (1.5-column)",
                "DPI": 300,
            })

    mf = REPO / "figures" / "EXPORT_MANIFEST.md"
    lines = [
        "# v5 figure export manifest",
        "",
        f"Generated on {TODAY} by `scripts/build_v5_figures.py`.",
        "Every figure uses the Nature-family palette and typography from "
        "`v5_streamlit_app/figure_style.py`. PDFs use vector text (pdf.fonttype 42).",
        "",
        "| Figure | Target slot | PDF | PNG | Size | DPI |",
        "|--------|-------------|-----|-----|------|----:|",
    ]
    for r in manifest_rows:
        lines.append(f"| {r['Figure']} | {r['Target manuscript slot']} "
                     f"| `{r['PDF']}` | `{r['PNG']}` "
                     f"| {r['Size (mm)']} | {r['DPI']} |")
    mf.write_text("\n".join(lines) + "\n")
    print(f"wrote {mf} with {len(manifest_rows)} entries")
    print(f"generated {len(manifest_rows) * 2} files under figures/")


if __name__ == "__main__":
    main()
