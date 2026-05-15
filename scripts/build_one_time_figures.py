"""Static Nature-grade figure exports for the One-Time Energy page.

Generates Figure A (component-level ranking, double-column),
Figure B (unit stacked by subsystem, single-column) and
Figure C (marginal components, single-column) as 300 DPI PNG and vector
PDF. Appends entries to figures/EXPORT_MANIFEST.md.
"""
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

REPO = Path(__file__).resolve().parent.parent
V5 = REPO / "v5_streamlit_app"
sys.path.insert(0, str(V5))

from core import NATURE_CATEGORICAL, apply_matplotlib_style  # noqa: E402
from figure_style import (  # noqa: E402
    AXIS_COLOR, GRID_COLOR,
    figsize_single_column, figsize_double_column,
)
from one_time_data import (  # noqa: E402
    CAV_COUNTS, COMPONENTS, STI_COUNTS, SUBSYSTEM_COLORS,
    component_sum, marginal_count, subsystem_breakdown,
)

FIG_DIR = REPO / "figures"
FIG_DIR.mkdir(exist_ok=True)
TODAY = _dt.date.today().isoformat()


def _save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    png = FIG_DIR / f"{stem}_{TODAY}.png"
    pdf = FIG_DIR / f"{stem}_{TODAY}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png, pdf


def fig_a_component_ranking() -> tuple[Path, Path]:
    rows = sorted(COMPONENTS.values(), key=lambda c: c.energy_kwh)
    names = [f"{c.name} ({c.platform})" for c in rows]
    vals = [c.energy_kwh for c in rows]
    colors = [SUBSYSTEM_COLORS[c.subsystem] for c in rows]
    alphas = [0.9 if c.subsystem != "Computing" else 0.7 for c in rows]

    fig, ax = plt.subplots(figsize=figsize_double_column())
    y = np.arange(len(rows))
    for yi, v, col, a in zip(y, vals, colors, alphas):
        ax.barh(yi, v, color=col, alpha=a, edgecolor="none", linewidth=0)
        ax.text(v + max(vals) * 0.01, yi, f"{v:.0f}",
                va="center", ha="left", fontsize=7.5, color=AXIS_COLOR)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("One-time energy per unit (kWh)")
    ax.grid(axis="x", which="major", color=GRID_COLOR,
            linestyle=":", alpha=0.3)
    ax.set_axisbelow(True)
    # Legend
    import matplotlib.patches as mpatches
    handles = [mpatches.Patch(color=SUBSYSTEM_COLORS[s], label=s,
                               alpha=0.9 if s != "Computing" else 0.7)
               for s in ("Sensing", "Computing", "Communication")]
    ax.legend(handles=handles, loc="lower right",
              frameon=False, fontsize=8)
    return _save(fig, "fig_ot_A_component_ranking")


def fig_b_unit_stacked() -> tuple[Path, Path]:
    display = [
        ("STI Highly",    STI_COUNTS["Highly"]),
        ("CAV L5",        CAV_COUNTS["L5"]),
        ("STI Semi",      STI_COUNTS["Semi"]),
        ("CAV L4",        CAV_COUNTS["L4"]),
        ("CAV L3 Large",  CAV_COUNTS["L3 Large"]),
        ("CAV L3 Medium", CAV_COUNTS["L3 Medium"]),
        ("CAV L3 Small",  CAV_COUNTS["L3 Small"]),
        ("STI Basic",     STI_COUNTS["Basic"]),
    ]
    unit_names = [u for u, _ in display]
    sensing = [subsystem_breakdown(c)["Sensing"] for _, c in display]
    computing = [subsystem_breakdown(c)["Computing"] for _, c in display]
    comm = [subsystem_breakdown(c)["Communication"] for _, c in display]
    totals = [s + cp + cm for s, cp, cm in zip(sensing, computing, comm)]

    fig, ax = plt.subplots(figsize=figsize_single_column())
    y = np.arange(len(unit_names))
    ax.barh(y, sensing, color=SUBSYSTEM_COLORS["Sensing"],
            alpha=0.9, edgecolor="none", label="Sensing")
    ax.barh(y, computing, left=sensing,
            color=SUBSYSTEM_COLORS["Computing"], alpha=0.7,
            edgecolor="none", label="Computing")
    ax.barh(y, comm, left=[s + c for s, c in zip(sensing, computing)],
            color=SUBSYSTEM_COLORS["Communication"], alpha=0.9,
            edgecolor="none", label="Communication")
    for yi, t in zip(y, totals):
        ax.text(t + max(totals) * 0.01, yi, f"{t:,.0f}",
                va="center", ha="left", fontsize=7.5, color=AXIS_COLOR)
    # Inline percent labels for sensing (wide segments only)
    for yi, s, t in zip(y, sensing, totals):
        if s / max(t, 1) >= 0.15:
            ax.text(s / 2, yi, f"{100*s/t:.0f} %",
                    va="center", ha="center", fontsize=7,
                    color="white", fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(unit_names, fontsize=8)
    ax.set_xlabel("One-time energy per unit (kWh)")
    ax.grid(axis="x", which="major", color=GRID_COLOR,
            linestyle=":", alpha=0.3)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(totals) * 1.22)
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.02),
              frameon=False, fontsize=7.5, ncol=3)
    return _save(fig, "fig_ot_B_unit_stacked")


def fig_c_marginal_counts() -> tuple[Path, Path]:
    cav = [(u, marginal_count(CAV_COUNTS[u]))
           for u in ("L3 Small", "L3 Medium", "L3 Large", "L4", "L5")]
    sti = [(u, marginal_count(STI_COUNTS[u]))
           for u in ("Basic", "Semi", "Highly")]

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=figsize_single_column(),
        gridspec_kw={"width_ratios": [5, 3]},
    )
    cav_names = [u for u, _ in cav]
    cav_vals = [n for _, n in cav]
    ax1.bar(cav_names, cav_vals, color=NATURE_CATEGORICAL["primary"],
            alpha=0.9, edgecolor="none")
    for xi, v in enumerate(cav_vals):
        ax1.text(xi, v + 1, str(v), ha="center", va="bottom",
                 fontsize=8, color=AXIS_COLOR)
    ax1.set_xlabel("CAV autonomy level")
    ax1.set_ylabel("Marginal components per unit")
    ax1.grid(axis="y", which="major", color=GRID_COLOR,
             linestyle=":", alpha=0.3)
    ax1.set_axisbelow(True)
    ax1.tick_params(axis="x", labelsize=7, rotation=30)
    for t in ax1.get_xticklabels():
        t.set_horizontalalignment("right")

    sti_names = [u for u, _ in sti]
    sti_vals = [n for _, n in sti]
    ax2.bar(sti_names, sti_vals,
            color=NATURE_CATEGORICAL["tertiary"],
            alpha=0.9, edgecolor="none")
    for xi, v in enumerate(sti_vals):
        ax2.text(xi, v + 1, str(v), ha="center", va="bottom",
                 fontsize=8, color=AXIS_COLOR)
    ax2.set_xlabel("STI tier")
    ax2.grid(axis="y", which="major", color=GRID_COLOR,
             linestyle=":", alpha=0.3)
    ax2.set_axisbelow(True)
    ax2.tick_params(axis="x", labelsize=8)
    ax2.set_ylim(ax1.get_ylim())  # align y-axes

    fig.tight_layout()
    return _save(fig, "fig_ot_C_marginal_counts")


def main() -> None:
    apply_matplotlib_style()
    manifest_rows: list[dict] = []
    for builder, desc, target, dims in [
        (fig_a_component_ranking,
         "Figure A · Component-level one-time energy ranking",
         "One-Time Energy page / Figure 3a", "184 × 110 (double-column)"),
        (fig_b_unit_stacked,
         "Figure B · Unit one-time energy stacked by subsystem",
         "One-Time Energy page / Figure 3b", "88 × 66 (single-column)"),
        (fig_c_marginal_counts,
         "Figure C · Marginal components across autonomy levels",
         "One-Time Energy page / Extended Data 3 + 4 visual",
         "88 × 66 (single-column)"),
    ]:
        png, pdf = builder()
        manifest_rows.append({
            "Figure": desc,
            "Target slot": target,
            "PDF": pdf.relative_to(REPO).as_posix(),
            "PNG": png.relative_to(REPO).as_posix(),
            "Size (mm)": dims, "DPI": 300,
        })

    # Append to EXPORT_MANIFEST.md (do not clobber the existing entries)
    mf = REPO / "figures" / "EXPORT_MANIFEST.md"
    new_section = ["", "", "## One-Time Energy page additions",
                   f"Appended on {TODAY}.", ""]
    new_section.append(
        "| Figure | Target slot | PDF | PNG | Size | DPI |")
    new_section.append(
        "|--------|-------------|-----|-----|------|----:|")
    for r in manifest_rows:
        new_section.append(
            f"| {r['Figure']} | {r['Target slot']} "
            f"| `{r['PDF']}` | `{r['PNG']}` "
            f"| {r['Size (mm)']} | {r['DPI']} |")
    existing = mf.read_text() if mf.exists() else "# v5 figure export manifest\n"
    mf.write_text(existing + "\n".join(new_section) + "\n")
    print(f"wrote {len(manifest_rows) * 2} files to figures/ and "
          f"appended manifest entries to {mf}")


if __name__ == "__main__":
    main()
