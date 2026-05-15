"""Nature-family figure-style module for CLEAR-ATS v5.

Every figure rendered in the v5 dashboard or regenerated into figures/ must
import the palettes, typography, and axis-style helpers defined here. The
goal is publication parity with Nature Communications methods figures.

Palettes
--------
NATURE_CATEGORICAL     — up to seven discrete categories
NATURE_LAYER           — L1 / L2 / L3 uncertainty layers
NATURE_MITIGATION      — five mitigation levers (consistent colour per lever)

Rule: ≤7 categories → NATURE_CATEGORICAL. L1/L2/L3 layers → NATURE_LAYER.
Continuous colourmaps (viridis, magma) only for genuinely continuous
quantities (e.g. turning-year surfaces).

The palettes were chosen to pass WCAG AA contrast on white and to remain
distinguishable under deuteranopia and protanopia simulation.

Typography
----------
Helvetica → Arial → DejaVu Sans fallback stack, matching the Nature
production stack. Sizes follow the Nature methods-figure guideline
(labels 8–9 pt, titles 10–11 pt).

Axis / tick standards
---------------------
Spines: left + bottom only, 0.8 pt solid #333333. Ticks outward, 3 pt
length, 0.6 pt width. Minor ticks enabled where x-span > 20 yr or y-span
> 1 order of magnitude. Gridlines horizontal only, dotted, alpha 0.30.
"""
from __future__ import annotations

from typing import Any, Iterable

NATURE_CATEGORICAL: dict[str, str] = {
    "primary":    "#0F4C81",
    "secondary":  "#C44E52",
    "tertiary":   "#55A868",
    "accent":     "#D4A017",
    "neutral":    "#595959",
    "muted":      "#B4B4B4",
    "background": "#FAFAFA",
}

NATURE_LAYER: dict[str, str] = {
    "L1": "#2F7A7A",
    "L2": "#C86F3C",
    "L3": "#6F4E93",
}

NATURE_MITIGATION: dict[str, str] = {
    "cav_growth_rate":            "#0F4C81",
    "sti_growth_rate":            "#2F7A7A",
    "ev_growth_rate":             "#55A868",
    "clean_energy_growth_rate":   "#6F4E93",
    "efficiency_doubling_years":  "#D4A017",
}

FONT_STACK = ["Helvetica", "Arial", "DejaVu Sans"]

AXIS_COLOR = "#333333"
GRID_COLOR = "#CCCCCC"
SPINE_WIDTH = 0.8
TICK_WIDTH = 0.6
TICK_LENGTH = 3


def apply_matplotlib_style() -> None:
    """Install Nature-family rcParams. Idempotent; safe to call many times."""
    import matplotlib as mpl

    mpl.rcParams.update({
        "font.family":       "sans-serif",
        "font.sans-serif":   FONT_STACK,
        "font.size":         9,
        "axes.titlesize":    10,
        "axes.labelsize":    9,
        "xtick.labelsize":   8,
        "ytick.labelsize":   8,
        "legend.fontsize":   8,
        "figure.titlesize":  11,
        "axes.edgecolor":    AXIS_COLOR,
        "axes.linewidth":    SPINE_WIDTH,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "xtick.direction":   "out",
        "ytick.direction":   "out",
        "xtick.major.size":  TICK_LENGTH,
        "ytick.major.size":  TICK_LENGTH,
        "xtick.major.width": TICK_WIDTH,
        "ytick.major.width": TICK_WIDTH,
        "xtick.color":       AXIS_COLOR,
        "ytick.color":       AXIS_COLOR,
        "grid.color":        GRID_COLOR,
        "grid.linestyle":    ":",
        "grid.alpha":        0.3,
        "axes.grid":         True,
        "axes.grid.axis":    "y",
        "figure.facecolor":  "white",
        "savefig.facecolor": "white",
        "savefig.dpi":       300,
        "pdf.fonttype":      42,
        "ps.fonttype":       42,
    })


def rgba(color_hex: str, alpha: float) -> str:
    """Convert a #rrggbb hex to an rgba(...) string for Plotly fills."""
    c = color_hex.strip().lstrip("#")
    if len(c) == 6:
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(128,128,128,{alpha})"


def plotly_layout_defaults() -> dict[str, Any]:
    """Return a dict of Plotly layout defaults aligned with the matplotlib style."""
    return {
        "font": {"family": "Helvetica, Arial, DejaVu Sans, sans-serif",
                 "size": 12, "color": AXIS_COLOR},
        "paper_bgcolor": "white",
        "plot_bgcolor":  "white",
        "margin":        {"t": 48, "b": 48, "l": 64, "r": 24},
        "xaxis": {
            "showline": True, "linewidth": SPINE_WIDTH, "linecolor": AXIS_COLOR,
            "ticks": "outside", "tickwidth": TICK_WIDTH, "ticklen": TICK_LENGTH,
            "tickcolor": AXIS_COLOR, "mirror": False,
            "showgrid": False, "zeroline": False,
        },
        "yaxis": {
            "showline": True, "linewidth": SPINE_WIDTH, "linecolor": AXIS_COLOR,
            "ticks": "outside", "tickwidth": TICK_WIDTH, "ticklen": TICK_LENGTH,
            "tickcolor": AXIS_COLOR, "mirror": False,
            "showgrid": True, "gridcolor": GRID_COLOR, "gridwidth": 0.5,
            "zeroline": False,
        },
        "legend": {"bgcolor": "rgba(255,255,255,0)", "bordercolor": "rgba(0,0,0,0)",
                   "font": {"size": 11}},
        "hoverlabel": {"font": {"family": "Helvetica, Arial, sans-serif", "size": 11}},
    }


def year_axis_defaults(year_min: int, year_max: int) -> dict[str, Any]:
    """Axis config for a calendar-year x-axis."""
    span = max(int(year_max) - int(year_min), 1)
    dtick = 10 if span >= 30 else 5 if span >= 15 else 2
    minor_dtick = 5 if dtick >= 10 else (1 if dtick <= 2 else 2)
    return {
        "dtick": dtick, "tick0": int(year_min),
        "tickformat": "d",
        "minor": {"dtick": minor_dtick, "ticklen": TICK_LENGTH * 0.6,
                  "tickwidth": TICK_WIDTH * 0.8, "tickcolor": AXIS_COLOR},
    }


def palette_for(n: int) -> list[str]:
    """Return n colours drawn from NATURE_CATEGORICAL in Nature-preferred order."""
    order = ["primary", "secondary", "tertiary", "accent", "neutral", "muted"]
    return [NATURE_CATEGORICAL[k] for k in order[: max(n, 0)]]


def layer_colors(layers: Iterable[str]) -> list[str]:
    return [NATURE_LAYER.get(str(layer), NATURE_CATEGORICAL["neutral"])
            for layer in layers]


def figsize_single_column() -> tuple[float, float]:
    """Single-column Nature Communications width (88 mm) in inches."""
    return (88.0 / 25.4, 66.0 / 25.4)


def figsize_1_5_column() -> tuple[float, float]:
    return (136.0 / 25.4, 88.0 / 25.4)


def figsize_double_column() -> tuple[float, float]:
    return (184.0 / 25.4, 110.0 / 25.4)
