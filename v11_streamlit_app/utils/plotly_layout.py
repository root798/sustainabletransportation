"""Common Plotly layout helpers for the CLEAR-ATS dashboard.

Symptoms this module fixes (see PR / task brief):

  * Horizontal legend sitting on top of the x-axis title.
  * Bar value labels (textposition="outside") getting clipped at the
    right plot edge on narrow viewports.
  * Insufficient vertical breathing room between the page H1, the figure
    subheader, and the chart.

Usage:

    from utils.plotly_layout import apply_clearats_layout

    fig = go.Figure(...)
    apply_clearats_layout(
        fig,
        kind="hbar",            # "hbar" / "vbar" / "line" / "pie"
        num_rows=len(rows),     # for hbar: drives height
        x_title="One-time energy per unit (kWh)",
        max_x=max(values),      # extends x-range so outside labels fit
    )
    st.plotly_chart(fig, width="stretch")

The helper composes on top of ``figure_style.plotly_layout_defaults()``
so per-page colour, font, and spine styling is preserved.
"""
from __future__ import annotations

from typing import Any, Optional

import plotly.graph_objects as go

# We re-use the established plot defaults from figure_style.py.
try:
    from figure_style import plotly_layout_defaults  # type: ignore
except ImportError:  # when imported as v11_streamlit_app.utils.plotly_layout
    from ..figure_style import plotly_layout_defaults  # type: ignore


# Public constants — keep margins consistent across pages and figure types.
_MARGINS = {
    "hbar": {"t": 40, "b": 92, "l": 200, "r": 88},
    "vbar": {"t": 40, "b": 92, "l": 80,  "r": 32},
    "line": {"t": 40, "b": 92, "l": 80,  "r": 32},
    "pie":  {"t": 40, "b": 16, "l": 16,  "r": 16},
}

# Horizontal legend placement below the x-axis title.
_LEGEND_BELOW = {
    "orientation": "h",
    "yanchor": "top",
    "y": -0.22,                  # below the x-axis title (which uses standoff=12)
    "xanchor": "center",
    "x": 0.5,
    "bgcolor": "rgba(0,0,0,0)",
    "bordercolor": "rgba(0,0,0,0)",
    "font": {"size": 11},
}


def _height_for_hbar(num_rows: int, *, min_height: int = 420,
                     row_height: int = 28, padding: int = 120) -> int:
    return max(int(min_height), int(row_height * max(int(num_rows), 1) + padding))


def apply_clearats_layout(
    fig: go.Figure,
    *,
    kind: str = "hbar",
    num_rows: Optional[int] = None,
    x_title: Optional[str] = None,
    y_title: Optional[str] = None,
    max_x: Optional[float] = None,
    height: Optional[int] = None,
    show_legend_below: bool = True,
    barmode: Optional[str] = None,
) -> go.Figure:
    """Apply CLEAR-ATS layout defaults to a Plotly figure.

    Parameters
    ----------
    fig
        Plotly figure to mutate.
    kind
        Layout family. Currently ``"hbar"`` (horizontal bars),
        ``"vbar"`` (vertical bars), ``"line"``, ``"pie"``.
    num_rows
        Number of y-axis categories for ``kind="hbar"``. Used to size the
        figure so y-axis labels don't crush together. Ignored for other
        kinds.
    x_title, y_title
        Axis titles. ``x_title`` gets a generous ``standoff`` so the
        legend can sit below it without overlap.
    max_x
        Maximum data value on the x-axis. Extends the x-range to
        ``max_x * 1.10`` so outside-bar value labels are not clipped on
        narrow viewports. Ignored when ``None`` or for non-bar kinds.
    height
        Override the computed default height (px).
    show_legend_below
        If True (default), place the legend below the x-axis title in
        the centered horizontal form. If False, leave the legend
        configuration to the caller (used for figures with no legend).
    barmode
        If set (``"stack"`` / ``"group"``), forwarded to the layout.
    """
    layout: dict[str, Any] = plotly_layout_defaults()

    # Margins: kind-specific, with extra bottom room for the legend
    # below the x-axis title.
    layout["margin"] = dict(_MARGINS.get(kind, _MARGINS["line"]))

    # x-axis title + standoff + automargin (so long axis text doesn't
    # collide with the legend).
    xaxis = dict(layout.get("xaxis", {}))
    if x_title is not None:
        xaxis["title"] = {"text": str(x_title), "standoff": 12}
    xaxis["automargin"] = True
    if max_x is not None and kind in ("hbar", "vbar", "line"):
        # 10 % headroom for outside-bar labels; the user-facing brief
        # specified this exact multiplier.
        xaxis["range"] = [0, float(max_x) * 1.10]
    layout["xaxis"] = xaxis

    # y-axis: automargin so long tick labels don't push the plot.
    yaxis = dict(layout.get("yaxis", {}))
    if y_title is not None:
        yaxis["title"] = {"text": str(y_title), "standoff": 8}
    yaxis["automargin"] = True
    layout["yaxis"] = yaxis

    if barmode is not None:
        layout["barmode"] = str(barmode)

    # Legend placement
    if show_legend_below:
        layout["legend"] = dict(_LEGEND_BELOW)

    # Height
    if height is None:
        if kind == "hbar":
            layout["height"] = _height_for_hbar(num_rows or 1)
        elif kind == "pie":
            layout["height"] = 360
        else:
            layout["height"] = 420
    else:
        layout["height"] = int(height)

    fig.update_layout(**layout)

    # Defensive: ensure outside-bar value labels are not clipped by the
    # plot area. (`cliponaxis=False` is a per-trace attribute.)
    if kind in ("hbar", "vbar"):
        for trace in fig.data:
            if isinstance(trace, go.Bar):
                trace.cliponaxis = False

    return fig


def page_top_spacing() -> str:
    """Return a small CSS block that adds breathing room between the
    Streamlit page H1, the figure subheader, and the first chart.

    Inject once near the top of a Streamlit page via
    ``st.markdown(page_top_spacing(), unsafe_allow_html=True)``.
    """
    return (
        "<style>"
        "h1 + div, h1 + p { margin-bottom: 0.6rem; }"
        "h2, .stMarkdown h2 { margin-top: 1.4rem; margin-bottom: 0.6rem; }"
        "h3, .stMarkdown h3 { margin-top: 1.1rem; margin-bottom: 0.5rem; }"
        "div[data-testid='stPlotlyChart'] { margin-bottom: 0.8rem; }"
        "</style>"
    )
