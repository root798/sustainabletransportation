"""Plotly figures for the CLEAR-ATS national dashboard."""
from __future__ import annotations

import textwrap
from typing import Any, Mapping

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from atlas_io import (
    EXPERT_GRID_CLASS_COLORS,
    EXPERT_GRID_CLASS_LABELS,
    EXPERT_VEHICLE_CLASS_COLORS,
    EXPERT_VEHICLE_CLASS_LABELS,
    GRID_CLASS_COLORS,
    GRID_CLASS_LABELS,
    MARKET_GRID_CLASS_COLORS,
    MARKET_GRID_CLASS_LABELS,
    MARKET_VEHICLE_CLASS_COLORS,
    MARKET_VEHICLE_CLASS_LABELS,
    PRIMARY_SCOPE,
    TURNING_POINT_NONE_FILL,
    TURNING_POINT_NONE_LABEL,
    TURNING_POINT_NONE_OUTLINE,
    TURNING_POINT_NONE_TOKEN,
    VEHICLE_CLASS_COLORS,
    VEHICLE_CLASS_LABELS,
    MetricSpec,
    metric_spec,
    national_median,
    state_slice,
)
from style import (
    BLUE,
    MANUSCRIPT_DEEP_TEAL,
    MANUSCRIPT_MAUVE,
    MANUSCRIPT_STEEL_BLUE,
    DIVERGING,
    HAIRLINE,
    INK,
    MUTED,
    ORANGE,
    PAPER,
    POLLUTION_SEQUENTIAL,
    SEQUENTIAL_BLUE,
    scenario_color,
    scenario_dash,
    UNCERTAINTY_SCALE,
)


# See pathway_charts.PLOT_SANS: a web font in this stack makes Plotly reserve
# a fallback-width slot and then draw a ~6% wider string into it, which is
# what over-printed the legend entries and spilled annotation text out of
# its own frame (A10 defects 4, 5, 8-13).
PLOT_FONT = "Arial, Helvetica, DejaVu Sans, sans-serif"

# Shared geo frame for every USA map: all 51 jurisdictions are painted by
# choropleth traces, so no base land/lakes/frame chrome may show — the earlier
# gray Canada band and Great Lakes patches came from showland/landcolor.
_MAP_GEO: dict[str, Any] = {
    "scope": "usa",
    "projection": {"type": "albers usa"},
    "showland": False,
    "showlakes": False,
    "showframe": False,
    "showcoastlines": False,
    "bgcolor": "rgba(0,0,0,0)",
    "framecolor": "rgba(0,0,0,0)",
}


def _base_layout(height: int, *, margin: dict[str, int] | None = None) -> dict[str, Any]:
    return {
        "height": height,
        "paper_bgcolor": PAPER,
        "plot_bgcolor": PAPER,
        "font": {"family": PLOT_FONT, "size": 12, "color": INK},
        "margin": margin or {"l": 58, "r": 18, "t": 30, "b": 54},
        "hoverlabel": {
            "align": "left",
            "font": {"family": PLOT_FONT, "size": 12, "color": INK},
            "bgcolor": "#ffffff",
            "bordercolor": "#b9b7b0",
        },
        "legend": {
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": 1.03,
            "yanchor": "bottom",
            # X6 / A10 defects 8-11: entrywidth 0 means "size each entry to
            # its own characters". It must be stated EXPLICITLY: the host
            # injects entrywidthmode="pixels" into the Plotly layout, so
            # with no entrywidth the entries were laid out on slots
            # narrower than their text -- each name over-printed by the
            # next swatch, the last one cut mid-word.
            "entrywidth": 0,
            "font": {"size": 11},
            "bgcolor": "rgba(0,0,0,0)",
        },
        "hovermode": "x unified",
    }


def _axis(title: str, *, percent: bool = False) -> dict[str, Any]:
    axis: dict[str, Any] = {
        # A10 defects 4, 5: 9px let "kg CO2 kWh-1" strike through the 0.2/0.1
        # tick labels after the web font swapped in.
        "title": {"text": title, "font": {"size": 11, "color": MUTED}, "standoff": 16},
        "showline": True,
        "linecolor": "#4a4945",
        "linewidth": 0.8,
        "ticks": "outside",
        "tickcolor": "#4a4945",
        "tickfont": {"size": 11, "color": MUTED},
        "gridcolor": HAIRLINE,
        "gridwidth": 0.6,
        "zeroline": False,
        "automargin": True,
    }
    if percent:
        axis["ticksuffix"] = "%"
    return axis


def _hover_unit_lines(unit: str) -> str:
    """Wrap long basis-qualified units without changing their meaning."""
    equal_size = " on the equal-size comparison ("
    if equal_size in unit and unit.endswith(")"):
        measure, basis = unit.split(equal_size, 1)
        return f"{measure}<br>equal-size comparison<br>{basis[:-1]}"
    if " per " in unit:
        measure, basis = unit.split(" per ", 1)
        return f"{measure}<br>per {basis}"
    return "<br>".join(
        textwrap.wrap(unit, width=38, break_long_words=False, break_on_hyphens=False)
    )


def _primary_domain(frame: pd.DataFrame, spec: MetricSpec) -> tuple[float, float]:
    values = frame.loc[frame["scope_role"] == PRIMARY_SCOPE, "value"].dropna().astype(float)
    if values.empty:
        return (0.0, 1.0)
    if spec.diverging:
        extent = float(np.max(np.abs(values)))
        return (-extent, extent)
    lo, hi = float(values.min()), float(values.max())
    if np.isclose(lo, hi):
        pad = max(abs(lo) * 0.05, 1.0)
        return (lo - pad, hi + pad)
    return (lo, hi)


# A10 defect 17 / X9: the "no turning point through 2075" sentinel used to be
# a flat gray, and gray was also the ~0.45 step of the old diverging pollution
# ramp -- a mid-range state and a no-data state looked the same.  The sentinel
# is now an unfilled, heavily outlined polygon that sits on no ramp at all.
ONSET_SENTINEL_FILL = "#f7f6f2"
ONSET_SENTINEL_OUTLINE = "#4a4945"


def _onset_colorscale(zmin: float, zmax: float) -> list[list[Any]]:
    """Discrete visual steps for exact modeled turning-point years.

    A10 defect 16: the turning-point year is a strictly sequential, unsigned
    quantity, so it takes the sequential blue ramp -- never the warm pollution
    ramp, which would imply that a later year is "more polluted", and never a
    diverging ramp, which would invent a midpoint the years do not have.

    V2-06: the year stepping stays DISCRETE -- one flat block per modeled
    year -- because the quantity is ordinal time with a one-year resolution.
    Only the ramp the blocks are sampled from is set by the "timing" palette
    role; the stepping itself is a property of the quantity, not the palette.
    """
    start, stop = int(np.floor(zmin)), int(np.ceil(zmax))
    count = max(stop - start + 1, 1)
    colors = sample_colorscale(SEQUENTIAL_BLUE, np.linspace(0, 1, count).tolist())
    stepped: list[list[Any]] = []
    for index, color in enumerate(colors):
        left = index / count
        right = (index + 1) / count
        stepped.extend([[left, color], [right, color]])
    return stepped


def _metric_colorscale(spec: MetricSpec) -> list[list[Any]]:
    """Palette by declared ROLE, never by metric key (four-lens V8 / V2-06).

    Every branch below reads ``spec.palette_role``.  The retired
    ``spec.key == "onset_year"`` special case made the rendered palette
    disagree with the declared role: the turning point was declared
    "pollution" and drawn blue, so any other consumer of the declaration --
    an export script, a caption generator, a future panel -- was told the
    wrong thing.  Ordinal-time quantities now carry the "timing" role and it
    is the role that picks the ramp.

    Role -> ramp, and why:
      signed      -> DIVERGING            the only genuinely signed quantity
                                          has a real zero to diverge about
      timing      -> SEQUENTIAL_BLUE      ordinal time: monotone single hue,
                                          no invented midpoint, and never the
                                          pollution ramp (a later year is not
                                          "more polluted")
      pollution   -> POLLUTION_SEQUENTIAL strictly non-negative loads, one
                                          warm hue, monotone in lightness
      uncertainty -> UNCERTAINTY_SCALE    width-of-support quantities
      energy/context -> SEQUENTIAL_BLUE   magnitude with no valence
    """
    if spec.diverging or spec.palette_role == "signed":
        return DIVERGING
    if spec.palette_role == "timing":
        return SEQUENTIAL_BLUE
    if spec.palette_role == "pollution":
        # V2-06 judgement, 2026-09-03: the five strictly non-negative CO2 and
        # intensity metrics KEEP this role.  The finding's premise -- that
        # they still sit on POLLUTION_BLUE_RED -- was already false: that
        # light-blue -> tan -> dark-red ramp flipped hue at ~0.4 and was
        # retired at A10 defect 16.  POLLUTION_SEQUENTIAL is monotone in
        # relative luminance across all seven stops and never crosses into
        # blue (red >= blue at every stop, enforced in test_visual_contract),
        # so it is a sequential encoding already; it is not a second
        # diverging ramp wearing a new name.  Moving them to SEQUENTIAL_BLUE
        # would buy no correctness and would cost the one thing the warm ramp
        # earns: on a page where blue means "energy/time/magnitude", warm
        # means "emitted CO2", so a reader can tell the two families apart
        # without reading the legend title.  Kept, deliberately, on the
        # record.
        return POLLUTION_SEQUENTIAL
    if spec.palette_role == "uncertainty":
        return UNCERTAINTY_SCALE
    return SEQUENTIAL_BLUE


def make_state_map(frame: pd.DataFrame, metric_key: str, selected_state: str) -> go.Figure:
    """Build a fixed-scope Albers-USA map with explicit right-censor handling."""
    spec = metric_spec(metric_key)
    zmin, zmax = _primary_domain(frame, spec)
    direction = (
        "negative ← 0 → positive"
        if spec.diverging
        else "lower → higher"
    )
    colorbar: dict[str, Any] = {
        "title": {
            "text": f"{spec.legend_title}<br><span style='font-size:10px'>{direction}</span>",
            "side": "top",
            "font": {"size": 11},
        },
        "orientation": "h",
        "x": 0.5,
        "xanchor": "center",
        "y": -0.04,
        "yanchor": "top",
        "len": 0.55,
        "thickness": 10,
        "outlinewidth": 0,
        "tickfont": {"size": 11},
    }
    colorscale = _metric_colorscale(spec)
    if spec.key == "onset_year":
        colorscale = _onset_colorscale(zmin, zmax)
        onset_ticks = list(range(int(np.floor(zmin)), int(np.ceil(zmax)) + 1))
        colorbar.update({"tickmode": "array", "tickvals": onset_ticks, "ticktext": onset_ticks})
    identified = frame.loc[frame["value"].notna()].copy()
    custom = np.column_stack(
        [
            identified["state_name"],
            identified["display_value"],
            identified["scope_note"],
            np.repeat(spec.unit, len(identified)),
        ]
    )
    fig = go.Figure()
    fig.add_trace(
        go.Choropleth(
            locations=identified["state"],
            z=identified["value"],
            locationmode="USA-states",
            zmin=zmin,
            zmax=zmax,
            colorscale=colorscale,
            marker={"line": {"color": PAPER, "width": 0.85}},
            colorbar=colorbar,
            customdata=custom,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                + spec.compact_label
                + ": %{customdata[1]}"
                + "<br><span style='color:#64625d'>Click to select</span>"
                + "<extra></extra>"
            ),
            name=spec.label,
        )
    )
    fig.add_trace(
        go.Scattergeo(
            lon=[-119.42, -82.91],
            lat=[36.78, 40.42],
            mode="markers",
            marker={
                "symbol": "star",
                "size": 8,
                "color": ORANGE,
                "line": {"color": PAPER, "width": 0.7},
            },
            text=["California · registered case available", "Ohio · registered case available"],
            hovertemplate="<b>%{text}</b><extra></extra>",
            showlegend=False,
            name="Registered case available",
        )
    )

    censored = frame.loc[frame["value"].isna()].copy()
    if not censored.empty:
        fig.add_trace(
            go.Choropleth(
                locations=censored["state"],
                z=np.ones(len(censored)),
                locationmode="USA-states",
                colorscale=[
                    [0, ONSET_SENTINEL_FILL], [1, ONSET_SENTINEL_FILL],
                ],
                showscale=False,
                marker={"line": {"color": ONSET_SENTINEL_OUTLINE, "width": 1.6}},
                customdata=np.column_stack([censored["state_name"], censored["display_value"]]),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>%{customdata[1]}"
                    "<br><span style='color:#64625d'>Click to select</span>"
                    "<extra></extra>"
                ),
                name="No turning point by 2075",
            )
        )

    # CA/OH are manuscript spotlights, not validation or ground truth.
    fig.add_trace(
        go.Choropleth(
            locations=["CA", "OH"],
            z=[1, 1],
            locationmode="USA-states",
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False,
            marker={"line": {"color": ORANGE, "width": 1.55}},
            hoverinfo="skip",
            name="Registered case available; map value remains normalized",
        )
    )
    fig.add_trace(
        go.Choropleth(
            locations=[selected_state],
            z=[1],
            locationmode="USA-states",
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False,
            marker={"line": {"color": INK, "width": 2.5}},
            hoverinfo="skip",
            name="Selected state",
        )
    )

    layout = _base_layout(660, margin={"l": 0, "r": 0, "t": 4, "b": 44})
    layout.update(
        {
            "geo": _MAP_GEO | {
                "uirevision": f"map-{metric_key}",
                "lonaxis": {"range": [-127.5, -65.5]},
                "lataxis": {"range": [23.0, 50.5]},
            },
            "showlegend": False,
            "hovermode": "closest",
            "uirevision": f"map-{metric_key}",
        }
    )
    fig.update_layout(**layout)
    return fig


# Small eastern jurisdictions whose centroid labels would collide; they are
# listed in a key line under the map and resolved in the fixed state panel.
TURNING_MAP_SMALL_STATES = ("CT", "DC", "DE", "MA", "MD", "NH", "NJ", "RI", "VT")


def turning_map_classes(
    color_by: str, scenario: str = "policy"
) -> tuple[str, dict[str, str], dict[str, str]]:
    """Return (class column, color map, label map) for the landing map.

    ``color_by="turning_point"`` is not a class fill and has no class map: the
    landing map fills by the turning-point YEAR, which is ordinal, and the
    states with no turning point by 2075 take one flat sentinel that
    ``make_turning_point_map`` draws as its own trace.  It is returned here
    anyway, with the sentinel as its only entry, so the page draws exactly one
    legend and cannot forget the sentinel.
    """
    if color_by == "turning_point":
        return (
            "has_turning_point",
            {"none": TURNING_POINT_NONE_FILL},
            {"none": TURNING_POINT_NONE_LABEL},
        )
    if scenario == "market":
        if color_by == "grid":
            return "grid_bridge_class", MARKET_GRID_CLASS_COLORS, MARKET_GRID_CLASS_LABELS
        return "elec_bridge_class", MARKET_VEHICLE_CLASS_COLORS, MARKET_VEHICLE_CLASS_LABELS
    if scenario == "expert":
        if color_by == "grid":
            return "grid_bridge_class", EXPERT_GRID_CLASS_COLORS, EXPERT_GRID_CLASS_LABELS
        return "elec_bridge_class", EXPERT_VEHICLE_CLASS_COLORS, EXPERT_VEHICLE_CLASS_LABELS
    if color_by == "grid":
        return "grid_bridge_class", GRID_CLASS_COLORS, GRID_CLASS_LABELS
    return "elec_bridge_class", VEHICLE_CLASS_COLORS, VEHICLE_CLASS_LABELS


def make_turning_point_map(
    frame: pd.DataFrame, color_by: str, selected_state: str,
    scenario: str = "policy",
) -> go.Figure:
    """National turning-point map for the selected scenario family.

    Each state (and DC) is filled by its bridge class (manuscript-adjacent
    colors, no red-green pair). Exact turning-point years are available in
    the hover/tap card and the selected-state panel rather than printed over
    small state polygons; this keeps the map readable from desktop to phone
    width. Values are registered deterministic scenarios, never
    probabilities. On the market-calibrated frame, a state with no turning
    point by 2075 is reported in words (``TURNING_POINT_NONE_TOKEN``), never
    imputed as a year and never printed in the symbol form the vocabulary
    contract retires (D2, 2026-09-04).
    """
    if color_by == "turning_point":
        return _make_turning_point_year_map(frame, selected_state, scenario)
    class_column, class_colors, class_labels = turning_map_classes(color_by, scenario)
    if "onset_label" in frame.columns:
        onset_labels = frame["onset_label"].astype(str)
    else:
        onset_labels = frame["onset_year"].astype(int).astype(str)
    frame = frame.assign(_onset_label=onset_labels)
    fig = go.Figure()
    for class_key, color in class_colors.items():
        piece = frame.loc[frame[class_column] == class_key]
        if piece.empty:
            continue
        custom = np.column_stack(
            [
                piece["state_name"],
                piece["_onset_label"],
            ]
        )
        fig.add_trace(
            go.Choropleth(
                locations=piece["state"],
                z=np.ones(len(piece)),
                locationmode="USA-states",
                colorscale=[[0, color], [1, color]],
                showscale=False,
                marker={"line": {"color": PAPER, "width": 0.85}},
                customdata=custom,
                hovertemplate=(
                    "<b>%{customdata[0]}</b>"
                    "<br>Turning point: %{customdata[1]}"
                    f"<br>{_turning_scenario_label(scenario)}"
                    "<extra></extra>"
                ),
                name=class_labels[class_key],
            )
        )

    fig.add_trace(
        go.Choropleth(
            locations=[selected_state],
            z=[1],
            locationmode="USA-states",
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False,
            marker={"line": {"color": INK, "width": 2.5}},
            hoverinfo="skip",
            name="Selected state",
        )
    )

    # X8: the albers-usa projection left 71% of the frame as empty paper at
    # 520 px tall (colour histogram of the rendered element). A tighter
    # frame plus a lon/lat window fitted to the 50 states + DC puts the map
    # on the canvas instead of floating in it.
    layout = _base_layout(560, margin={"l": 0, "r": 0, "t": 4, "b": 12})
    layout.update(
        {
            "geo": _MAP_GEO | {
                "uirevision": f"turning-map-{scenario}-{color_by}",
                "lonaxis": {"range": [-127.5, -65.5]},
                "lataxis": {"range": [23.0, 50.5]},
            },
            "showlegend": False,
            "hovermode": "closest",
            "uirevision": f"turning-map-{scenario}-{color_by}",
        }
    )
    fig.update_layout(**layout)
    return fig


def _turning_scenario_label(scenario: str) -> str:
    return {
        "expert": "Delivered central", "policy": "Policy-registered",
        "market": "Market-trend", "noaccii": "No ACC II comparison",
    }.get(scenario, "Selected scenario")


def _make_turning_point_year_map(
    frame: pd.DataFrame, selected_state: str, scenario: str
) -> go.Figure:
    """The landing map: fill by turning-point YEAR, with a named sentinel.

    Two traces, deliberately:

      * the states that turn, on the discrete sequential ramp
        ``_onset_colorscale`` builds -- one flat block per modelled year,
        because the quantity is ordinal time at one-year resolution, and a
        monotone single hue, because a later turning point is not "more" of
        anything the warm ramp encodes;
      * the states with no turning point by 2075, in ONE flat sentinel
        with a heavy outline and its own legend entry.  They are never given
        a year, never pushed to the dark end of the ramp, and never dropped
        from the map -- all three of which would tell the reader something
        the model does not say.
    """
    turns = frame.loc[frame["has_turning_point"]]
    none_by = frame.loc[~frame["has_turning_point"]]
    fig = go.Figure()
    if len(turns):
        years = turns["onset_year"].astype(float)
        zmin, zmax = float(years.min()), float(years.max())
        # THINNED, so the labels cannot overprint each other.  The nine
        # delivered turning points span 2034 to 2060 with six of them inside
        # eight years, and at 390 px those six labels collide on a colorbar
        # 0.62 of the plot tall.  A tick is kept when it is at least this
        # fraction of the range from the last kept one; the first and the last
        # are always kept, because they are the ends of the scale.
        _MINIMUM_TICK_SEPARATION = 0.09
        _all_years = sorted({int(year) for year in years})
        span = max(zmax - zmin, 1.0)
        ticks = [_all_years[0]]
        for candidate in _all_years[1:-1]:
            if (candidate - ticks[-1]) / span >= _MINIMUM_TICK_SEPARATION:
                ticks.append(candidate)
        if len(_all_years) > 1:
            if (_all_years[-1] - ticks[-1]) / span < _MINIMUM_TICK_SEPARATION:
                ticks.pop()
            ticks.append(_all_years[-1])
        fig.add_trace(
            go.Choropleth(
                locations=turns["state"],
                z=years,
                zmin=zmin - 0.5,
                zmax=zmax + 0.5,
                locationmode="USA-states",
                colorscale=_onset_colorscale(zmin, zmax),
                showscale=True,
                colorbar={
                    # Keep the title and every tick inside a phone-width canvas.
                    # The former vertical bar put its title beyond the right edge
                    # at 390 px even though the map itself remained responsive.
                    "title": {
                        "text": "Turning point year",
                        "side": "top",
                        "font": {"size": 11, "family": PLOT_FONT, "color": INK},
                    },
                    "orientation": "h",
                    "x": 0.5,
                    "xanchor": "center",
                    "y": -0.03,
                    "yanchor": "top",
                    "tickmode": "array",
                    "tickvals": ticks,
                    "ticktext": [str(year) for year in ticks],
                    "thickness": 10,
                    "len": 0.62,
                    "outlinewidth": 0,
                    "tickfont": {"size": 11, "family": PLOT_FONT, "color": INK},
                },
                marker={"line": {"color": PAPER, "width": 0.85}},
                customdata=np.column_stack(
                    [
                        turns["state_name"],
                        turns["onset_label"],
                    ]
                ),
                hovertemplate=(
                    "<b>%{customdata[0]}</b>"
                    "<br>Turning point: %{customdata[1]}"
                    f"<br>{_turning_scenario_label(scenario)}"
                    "<extra></extra>"
                ),
                name="Turning point year",
            )
        )
    if len(none_by):
        fig.add_trace(
            go.Choropleth(
                locations=none_by["state"],
                z=np.ones(len(none_by)),
                locationmode="USA-states",
                colorscale=[[0, TURNING_POINT_NONE_FILL], [1, TURNING_POINT_NONE_FILL]],
                showscale=False,
                marker={"line": {"color": TURNING_POINT_NONE_OUTLINE, "width": 1.6}},
                customdata=np.column_stack(
                    [
                        none_by["state_name"],
                        none_by["onset_label"],
                    ]
                ),
                hovertemplate=(
                    "<b>%{customdata[0]}</b>"
                    "<br>Turning point: %{customdata[1]}"
                    f"<br>{_turning_scenario_label(scenario)}"
                    "<extra></extra>"
                ),
                name=TURNING_POINT_NONE_LABEL,
            )
        )
    fig.add_trace(
        go.Choropleth(
            locations=[selected_state],
            z=[1],
            locationmode="USA-states",
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False,
            marker={"line": {"color": INK, "width": 2.5}},
            hoverinfo="skip",
            name="Selected state",
        )
    )
    layout = _base_layout(560, margin={"l": 0, "r": 0, "t": 4, "b": 76})
    layout.update(
        {
            "geo": _MAP_GEO | {
                "uirevision": f"turning-map-{scenario}-turning-point",
                "lonaxis": {"range": [-127.5, -65.5]},
                "lataxis": {"range": [23.0, 50.5]},
            },
            "showlegend": False,
            "hovermode": "closest",
            "uirevision": f"turning-map-{scenario}-turning-point",
        }
    )
    fig.update_layout(**layout)
    return fig


def make_ranking(frame: pd.DataFrame, metric_key: str, selected_state: str) -> go.Figure:
    """Clickable 50-state ordering as a data-anchored dot plot; DC excluded.

    A10 defect 18 / X2: this was a zero-anchored bar chart.  For the flagship
    energy metric the 50 values span 41,105 -> 41,689 MWh-eq -- a 1.4% spread
    drawn on an axis running from 0 to 43,883 -- so all fifty bars were the
    same length and the ordering the panel exists to show was invisible.  A
    dot plot anchored to the DATA range, with each value printed at its dot,
    makes the ordering legible without implying a zero baseline the metric
    does not have.  Click-to-select still works: the state code stays in
    customdata[0], which is what ``_extract_location`` reads.
    """
    spec = metric_spec(metric_key)
    ranked = frame.loc[(frame["scope_role"] == PRIMARY_SCOPE) & frame["value"].notna()].copy()
    ranked = ranked.sort_values(["value", "state"], ascending=[True, True]).reset_index(drop=True)
    ranked["rank"] = np.arange(1, len(ranked) + 1)
    zmin, zmax = _primary_domain(frame, spec)
    if np.isclose(zmin, zmax):
        normalized = np.repeat(0.5, len(ranked))
    else:
        normalized = np.clip((ranked["value"].to_numpy() - zmin) / (zmax - zmin), 0, 1)
    scale = _metric_colorscale(spec)
    if spec.key == "onset_year":
        start, stop = int(np.floor(zmin)), int(np.ceil(zmax))
        count = max(stop - start + 1, 1)
        year_palette = sample_colorscale(
            SEQUENTIAL_BLUE, np.linspace(0, 1, count).tolist()
        )
        colors = [year_palette[int(value) - start] for value in ranked["value"]]
    else:
        colors = sample_colorscale(scale, normalized.tolist())
    marker_line_width = [2.2 if code == selected_state else 0.8 for code in ranked["state"]]
    marker_line_color = [INK if code == selected_state else "#8d8b85" for code in ranked["state"]]
    custom = np.column_stack(
        [ranked["state"], ranked["state_name"], ranked["display_value"], ranked["rank"]]
    )
    fig = go.Figure(
        go.Scatter(
            x=ranked["value"],
            y=ranked["state"],
            mode="markers+text",
            marker={
                "color": colors,
                "size": 11,
                "line": {"color": marker_line_color, "width": marker_line_width},
            },
            text=ranked["display_value"],
            textposition="middle right",
            textfont={"size": 10, "color": MUTED},
            cliponaxis=False,
            customdata=custom,
            hovertemplate=(
                "<b>%{customdata[1]} (%{customdata[0]})</b><br>"
                "50-state order: %{customdata[3]} of 50<br>"
                + spec.compact_label
                + ": %{customdata[2]}<br>"
                + _hover_unit_lines(spec.unit)
                + "<extra></extra>"
            ),
            name=spec.label,
        )
    )
    # Anchor the axis to the DATA range with symmetric padding, plus extra
    # room on the right for the printed value at each dot.
    span = float(zmax - zmin)
    if span <= 0:
        span = max(abs(float(zmax)), 1.0) * 0.02
    pad_low = span * 0.08
    pad_high = span * 0.45
    layout = _base_layout(1020, margin={"l": 42, "r": 16, "t": 10, "b": 104})
    layout.update(
        {
            "showlegend": False,
            "xaxis": {
                **_axis(_hover_unit_lines(spec.unit)),
                "range": [zmin - pad_low, zmax + pad_high],
                "showgrid": True,
            },
            "yaxis": {
                **_axis(""),
                "categoryorder": "array",
                "categoryarray": ranked["state"].tolist(),
                "tickfont": {"size": 11, "color": MUTED},
                "showgrid": False,
            },
            "hovermode": "closest",
        }
    )
    if spec.diverging:
        layout["xaxis"]["zeroline"] = True
        layout["xaxis"]["zerolinecolor"] = "#777570"
        layout["xaxis"]["zerolinewidth"] = 1
    if spec.key == "onset_year":
        layout["xaxis"]["tickformat"] = "d"
    fig.update_layout(**layout)
    return fig


def make_bundle_trajectory(
    data: Mapping[str, Any],
    state: str,
    detail_scenario: str,
    *,
    compare_scenarios: bool = False,
) -> go.Figure:
    """Plot a conditioned bundle path, with optional deterministic comparators."""
    source = state_slice(data, state)
    pivot = source.pivot(index="year", columns="scenario_bundle",
                         values="normalized_bundle_direct_co2_metric_tonnes").sort_index()
    fig = go.Figure()
    scenario_roster = ("low", "medium", "high") if compare_scenarios else (detail_scenario,)
    for scenario in scenario_roster:
        selected = scenario == detail_scenario
        fig.add_trace(
            go.Scatter(
                x=pivot.index,
                y=pivot[scenario],
                mode="lines",
                line={
                    "color": scenario_color(scenario),
                    "width": 3.0 if selected else 1.35,
                    "dash": scenario_dash(scenario),
                },
                name=scenario.title(),
                hovertemplate=f"{scenario.title()}: %{{y:,.0f}} t CO₂<extra></extra>",
            )
        )
    median = national_median(data, detail_scenario, "normalized_bundle_direct_co2_metric_tonnes")
    fig.add_trace(
        go.Scatter(
            x=median["year"],
            y=median["national_median"],
            mode="lines",
            line={"color": "#777570", "width": 1.25, "dash": "dash"},
            name="50-state-only median",
            hovertemplate="50-state-only median: %{y:,.0f} t CO₂<extra></extra>",
        )
    )
    layout = _base_layout(410, margin={"l": 70, "r": 18, "t": 82, "b": 56})
    layout.update(
        {
            "xaxis": {**_axis("Modeled year"), "dtick": 10, "showgrid": False},
            "yaxis": _axis("t CO₂ yr⁻¹ on the equal-size comparison (1M vehicles + 1k STI units)"),
            "title": {
                "text": "Equal-size comparison trajectory",
                "x": 0,
                "xanchor": "left",
                "y": 0.99,
                "yanchor": "top",
                "font": {"family": PLOT_FONT, "size": 13, "color": INK},
            },
            "legend": {
                "orientation": "h",
                "x": 0,
                "xanchor": "left",
                "y": 1.13,
                "yanchor": "bottom",
                # X6 / A10 defects 8-11: entrywidth 0 means "size each entry to
                # its own characters". It must be stated EXPLICITLY: the host
                # injects entrywidthmode="pixels" into the Plotly layout, so
                # with no entrywidth the entries were laid out on slots
                # narrower than their text -- each name over-printed by the
                # next swatch, the last one cut mid-word.
                "entrywidth": 0,
                # X6: fixed pixel entry slots over-printed longer legend
                # names after the web font swapped in.  Plotly sizes each
                # entry to its own text instead.
                "font": {"size": 11},
                "bgcolor": "rgba(0,0,0,0)",
            },
        }
    )
    fig.update_layout(**layout)
    return fig


def make_driver_trajectory(data: Mapping[str, Any], state: str, scenario: str,
                           *, column: str, title: str, y_title: str,
                           scale: float = 1.0, percent: bool = False) -> go.Figure:
    source = state_slice(data, state)
    selected = source.loc[source["scenario_bundle"] == scenario].sort_values("year")
    median = national_median(data, scenario, column)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=selected["year"],
            y=selected[column] * scale,
            mode="lines",
            line={"color": scenario_color(scenario), "width": 2.4},
            name=state,
            hovertemplate=f"{state}: %{{y:,.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=median["year"],
            y=median["national_median"] * scale,
            mode="lines",
            line={"color": "#777570", "width": 1.2, "dash": "dash"},
            name="50-state-only median",
            hovertemplate="50-state-only median: %{y:,.2f}<extra></extra>",
        )
    )
    # Reserve a separate top row for Plotly's toolbar on narrow screens.
    layout = _base_layout(320, margin={"l": 64, "r": 12, "t": 108, "b": 50})
    layout.update(
        {
            "xaxis": {**_axis("Modeled year"), "dtick": 10, "showgrid": False},
            "yaxis": _axis(y_title, percent=percent),
            "title": {
                "text": title,
                "x": 0,
                "xanchor": "left",
                "y": 0.88,
                "yanchor": "top",
                "font": {"family": PLOT_FONT, "size": 12, "color": INK},
            },
            "legend": {
                "orientation": "h",
                "x": 0,
                "xanchor": "left",
                "y": 1.15,
                "yanchor": "bottom",
                # X6 / A10 defects 8-11: entrywidth 0 means "size each entry to
                # its own characters". It must be stated EXPLICITLY: the host
                # injects entrywidthmode="pixels" into the Plotly layout, so
                # with no entrywidth the entries were laid out on slots
                # narrower than their text -- each name over-printed by the
                # next swatch, the last one cut mid-word.
                "entrywidth": 0,
                # X6: fixed pixel entry slots over-printed longer legend
                # names after the web font swapped in.  Plotly sizes each
                # entry to its own text instead.
                "font": {"size": 11},
                "bgcolor": "rgba(0,0,0,0)",
            },
        }
    )
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# THE NATIONAL TRAJECTORY, WITH ITS INTERVAL AND ITS NAMED DEPLOYMENT LINES.
#
# NEW AT v3.3.  The landing page shows the national line, the 5th-95th
# percentile interval around it, and the two DECLARED DEPLOYMENT LEVELS as
# named lines.  The two levels are NOT interval width and must never be drawn
# as a ribbon: the model is exactly linear in the deployment scale, so each
# named line is the central rescaled by its own level over 0.30, and the build
# gates that equality by RUNNING the harness at the declared level rather than
# asserting it.  Drawing them inside the ribbon would price a quantity the
# interval deliberately does not price.
#
# The ink is the manuscript palette: the central takes the deep cool ink, the
# two declared levels take the two paler cool inks, and nothing here is green,
# so no red is paired with a green.
# ---------------------------------------------------------------------------
NATIONAL_DEPLOYMENT_LINES = {
    "NAMED_LINE_DEPLOYMENT_SCALE_LOW_15PCT": (
        "Deployment 15% by 2075 (named line)", MANUSCRIPT_STEEL_BLUE, "dashdot",
    ),
    "NAMED_LINE_DEPLOYMENT_SCALE_HIGH_45PCT": (
        "Deployment 45% by 2075 (named line)", MANUSCRIPT_MAUVE, "dot",
    ),
}


def make_national_trajectory(
    national_band: pd.DataFrame,
    named_lines: pd.DataFrame,
    metric: str,
    basis: str,
    *,
    y_title: str,
    scale: float = 1.0,
) -> go.Figure:
    """The national central, its interval, and the two declared deployment lines."""
    band = national_band.loc[
        (national_band["metric"] == metric)
        & (national_band["capacity_basis"] == basis)
    ].sort_values("year")
    figure = go.Figure()
    if band.empty:
        figure.update_layout(**_base_layout(320))
        figure.add_annotation(
            text="No interval is packaged for this metric on this basis.",
            showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper",
            font={"size": 12, "color": MUTED},
        )
        return figure
    years = band["year"].tolist()
    figure.add_trace(
        go.Scatter(
            x=years + years[::-1],
            y=(band["p95"] / scale).tolist()
            + (band["p05"] / scale).tolist()[::-1],
            fill="toself",
            fillcolor="rgba(51, 105, 123, 0.16)",
            line={"color": "rgba(0,0,0,0)"},
            hoverinfo="skip",
            name="5th–95th percentile interval",
            showlegend=True,
        )
    )
    figure.add_trace(
        go.Scatter(
            x=years,
            y=(band["central"] / scale),
            mode="lines",
            line={"color": MANUSCRIPT_DEEP_TEAL, "width": 2.4},
            name="The delivered central",
            hovertemplate=(
                "<b>Delivered central</b><br>Year: %{x}"
                "<br>Value: %{y:,.3f}<extra></extra>"
            ),
        )
    )
    for line_key, (label, color, dash) in NATIONAL_DEPLOYMENT_LINES.items():
        piece = named_lines.loc[
            (named_lines["line"] == line_key)
            & (named_lines["metric"] == metric)
            & (named_lines["capacity_basis"] == basis)
        ].sort_values("year")
        if piece.empty:
            continue
        hover_label = label.removesuffix(" (named line)")
        figure.add_trace(
            go.Scatter(
                x=piece["year"],
                y=(piece["national_total"] / scale),
                mode="lines",
                line={"color": color, "width": 1.6, "dash": dash},
                name=label,
                hovertemplate=(
                    f"<b>{hover_label}</b><br>Named line"
                    "<br>Year: %{x}<br>Value: %{y:,.3f}<extra></extra>"
                ),
            )
        )
    layout = _base_layout(360)
    layout["xaxis"] = _axis("Year")
    layout["yaxis"] = _axis(y_title)
    figure.update_layout(**layout)
    # The published projection ends at 2050; everything after it is the
    # authors' continuation, and the shading says so on the figure itself.
    figure.add_vrect(
        x0=2050.5, x1=max(years), fillcolor="#151515", opacity=0.05,
        line_width=0, layer="below",
        annotation_text="authors' continuation", annotation_position="top left",
        annotation_font_size=10, annotation_font_color=MUTED,
    )
    return figure
