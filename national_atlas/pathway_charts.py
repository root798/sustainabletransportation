"""Article-style pathway and retained-sensitivity charts for the dashboard."""
from __future__ import annotations

import re
import textwrap
from typing import Any, Mapping

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from atlas_io import (
    band_metric_is_packaged,
    BAND_HORIZON_ANCHOR_YEAR,
    PRIMARY_SCOPE,
    band_annotation_text,
    band_has_ceiling_prior,
    engineering_band,
    policy_central_band,
    policy_central_band_max_width,
    policy_central_state_slice,
    policy_central_turning_row,
    relative_pct_text,
    state_slice,
)
from case_study_io import BAND_OBJECTS, PATHWAY_METRICS, case_band, case_central
from metric_names import (
    AXIS_UNITS,
    BASIS_FOOTNOTES,
    CASE_AXIS_UNITS,
    METRIC_DISPLAY_NAMES,
    PANEL_LETTERS,
    STATE_SCALED_PANEL_NAMES,
    TURNING_POINT_LOWER,
    panel_title,
)
from style import HAIRLINE, INK, MUTED, PAPER


# A10 defects 8-13, root cause (measured 2026-09-03 in headless Chrome):
# Plotly measures every legend entry and annotation box by laying the string
# out in the requested font at draw time and caching the result.  The page's
# Source Sans faces are injected as @font-face by st.markdown, so at that
# moment the browser is still falling back to Arial -- Plotly reserved an
# Arial-width slot and then RE-RENDERED the same string in Source Sans, about
# 6% wider.  Deterministically reproducible (identical to 0.1 px across
# reloads, unaffected by a forced relayout, and not a cold-cache race):
#
#   "author-model conditional band"  slot 189.0 px, rendered 199.8 px
#   "Expert central (v2.2)"          slot 136.2 px, rendered 145.8 px
#
# so each name was over-printed by the next entry's swatch. Charts therefore
# use a stack whose first family is always resolvable, which makes the
# measured width and the drawn width the same number by construction. Page
# chrome (headings, body, tiles) keeps Source Sans / Source Serif.
PLOT_SANS = "Arial, Helvetica, sans-serif"
HOVER_LABEL_STYLE = {
    "align": "left",
    "font": {"family": PLOT_SANS, "size": 12, "color": INK},
    "bgcolor": "#ffffff",
    "bordercolor": "#b9b7b0",
}

# V2-08 (2026-09-03): the horizontal legends were laid out on ONE row's worth
# of vertical room.  Sizing each entry to its own text (entrywidth 0) stopped
# the entries over-printing EACH OTHER, but a legend wider than the plot
# still wraps -- and a wrapped legend grew upward into a top margin that had
# room for exactly one row, so on the state-scaled triptych the second row
# was clipped by the paper edge at 1440 px and the third and fourth rows at
# mobile widths.  The fix is room, not shorter honesty: every stacked-panel
# legend now reserves as many rows as it actually wraps onto.
#
# Row height and entry width use the numbers measured for this app in
# headless Chrome (see the A10 block above: "author-model conditional band",
# 29 characters, occupies a 189.0 px Arial slot, i.e. ~6.5 px per character
# plus a ~40 px swatch-and-gutter).  ``estimated_legend_width`` applies that
# model so a test can fail when a new legend name pushes a figure past the
# rows it reserves, instead of the overrun being found in a screenshot.
LEGEND_ROW_HEIGHT_PX = 20
LEGEND_CHAR_WIDTH_PX = 6.52
LEGEND_ENTRY_CHROME_PX = 40.0
# The narrowest plot area the app is captured at (mobile viewport minus the
# Streamlit gutters) and the desktop capture width; "both widths" in the
# finding.  reserve_legend_rows() sizes the top margin for the WORSE of
# the two.
LEGEND_PLOT_WIDTH_MOBILE_PX = 350.0
LEGEND_PLOT_WIDTH_DESKTOP_PX = 1130.0
# One-row top-margin allowance shared by every stacked-panel figure.
TRIPTYCH_BASE_TOP_MARGIN_PX = 82


def estimated_legend_width(names) -> float:
    """Total horizontal px a one-row horizontal legend would need."""
    return sum(
        LEGEND_CHAR_WIDTH_PX * len(str(name)) + LEGEND_ENTRY_CHROME_PX
        for name in names
    )


def estimated_legend_rows(names, plot_width_px: float) -> int:
    """Rows the legend wraps onto at ``plot_width_px`` (greedy, as Plotly)."""
    rows, used = 1, 0.0
    for name in names:
        entry = LEGEND_CHAR_WIDTH_PX * len(str(name)) + LEGEND_ENTRY_CHROME_PX
        if used > 0 and used + entry > plot_width_px:
            rows += 1
            used = entry
        else:
            used += entry
    return rows


def legend_names(fig: go.Figure) -> list[str]:
    """Every name this figure will put in its legend, in draw order."""
    return [
        str(trace.name)
        for trace in fig.data
        if trace.name and getattr(trace, "showlegend", None) is not False
    ]


def reserve_legend_rows(fig: go.Figure) -> None:
    """Grow the top margin and the figure to fit the WRAPPED legend (V2-08).

    Sizing each entry to its own text (``entrywidth`` 0) stopped the entries
    over-printing each other, but a legend wider than the plot still wraps,
    and the wrapped rows grew upward into a top margin sized for exactly one
    row -- so the extra rows were clipped by the paper edge.  Rows are
    estimated at BOTH capture widths from the app's own measured Arial
    metrics and the worst case wins; the figure grows by the extra rows so no
    panel loses height to the fix.
    """
    names = legend_names(fig)
    if not names:
        return
    rows = max(
        estimated_legend_rows(names, LEGEND_PLOT_WIDTH_MOBILE_PX),
        estimated_legend_rows(names, LEGEND_PLOT_WIDTH_DESKTOP_PX),
    )
    extra = LEGEND_ROW_HEIGHT_PX * (rows - 1)
    if extra <= 0:
        return
    # The figure's CURRENT top margin is the one-row allowance, whatever the
    # builder chose (the compare overlay already reserves a two-row top band
    # for its title); add to it rather than overwriting it.
    margin = fig.layout.margin.to_plotly_json() or {}
    margin["t"] = int(margin.get("t", TRIPTYCH_BASE_TOP_MARGIN_PX)) + extra
    fig.update_layout(height=int(fig.layout.height) + extra, margin=margin)
# Metric-color a11y pass (cherry-picked from the publish_ready audit,
# 2026-09-03): energy moved off the near-neutral gray to an unambiguous blue
# and intensity to a violet so the three metrics stay separable for
# color-vision-deficient readers; emissions unchanged.
METRIC_COLORS = {
    "energy": "#27618c",
    "emissions": "#a6463d",
    "carbon_intensity": "#6e5a87",
}
SCENARIO_DASHES = {"low": "dot", "medium": "solid", "high": "longdash"}
SCENARIO_OPACITY = {"low": 0.68, "medium": 1.0, "high": 0.75}

# Owner requirement B1/B2: one manuscript name per metric, everywhere.
PANEL_TITLES = {key: panel_title(key) for key in METRIC_DISPLAY_NAMES}

NATIONAL_RANGE_LABELS = {
    "conditioned_grid_conversion": "3-case conditioned support",
    "full_conversion_factorial": "9-case full conversion stress",
}


def _compact_panel_annotation(text: str) -> str:
    """Wrap band-width readouts without dropping their basis or direction."""
    match = re.fullmatch(
        r"one-sided (.+?) of central \((\d{4}→\d{4})\) · absolute ×(.+)",
        text,
    )
    if match:
        relative, years, ratio = match.groups()
        zero_central = " (the central is zero)" in relative
        relative = relative.replace(" (the central is zero)", "")
        lines = [
            f"one-sided {relative} of central",
            f"{years} · absolute width ×{ratio}",
        ]
        if zero_central:
            lines.append("central is zero at the horizon")
        return "<br>".join(lines)
    return "<br>".join(
        textwrap.wrap(text, width=42, break_long_words=False, break_on_hyphens=False)
    )


def _panel_band_annotation(fig: go.Figure, row_index: int,
                           max_side: float | None = None, *,
                           text: str | None = None) -> None:
    """Stamp one panel with its maximum one-sided deviation.

    The envelopes can be asymmetric, so a ``±`` label would be false.  State
    the larger of the lower and upper relative deviations explicitly.  Pass
    ``text`` to override the classic label — the v4 band uses the registered
    two-basis wording from ``atlas_io.band_annotation_text`` (same-year basis
    inside the scoped window, peak basis beyond it).
    """
    if text is None:
        if max_side is None:
            raise ValueError("Either max_side or text is required")
        text = f"max one-sided deviation {relative_pct_text(max_side)}"
    text = _compact_panel_annotation(text)
    fig.add_annotation(
        text=text,
        row=row_index,
        col=1,
        xref="x domain",
        yref="y domain",
        x=0.99,
        y=0.97,
        xanchor="right",
        yanchor="top",
        showarrow=False,
        font={"family": PLOT_SANS, "size": 10, "color": MUTED},
        bgcolor="rgba(252,252,250,0.85)",
        bordercolor=HAIRLINE,
        borderwidth=0.5,
        # A10 defect 13: Plotly measures the box with the fallback font and
        # the text is re-laid out once Source Sans arrives, so the glyphs
        # spilled out of their own frame.  Padding absorbs the metric
        # difference; the text itself is also shorter now.
        borderpad=4,
        align="right",
    )


def _declare_offscale_comparators(fig: go.Figure, row_index: int,
                                  series: Mapping[str, pd.Series],
                                  low: float, high: float, horizon: int,
                                  hover_format: str) -> None:
    """Name any CONTEXT line the fitted y-range cannot show (X3 / A10 #19).

    The panel range is fitted to the panel's registered subject -- the
    emphasized central and its displayed band -- so nothing drawn for context
    can crush it (CX-21, extended to every mode by V2-10).  That left the
    legend advertising lines that exit the frame with nothing on screen
    saying so.  Declare each one, with its value at the displayed horizon.

    ``series`` is keyed by the name to print.  Scenario keys ("low",
    "medium", "high") are title-cased; any other key -- e.g. the
    50-state-only median -- is printed verbatim, because title-casing it
    produces "50-State-Only Median".
    """
    offscale = []
    for name, values in series.items():
        if values is None or not len(values):
            continue
        if float(values.max()) > high or float(values.min()) < low:
            try:
                at_horizon = float(values.loc[horizon])
            except KeyError:
                at_horizon = float(values.iloc[-1])
            label = name.title() if name in {"low", "medium", "high"} else name
            offscale.append(f"{label} {at_horizon:,.4g} at {horizon}")
    if not offscale:
        return
    fig.add_annotation(
        text="off scale: " + " · ".join(offscale),
        row=row_index, col=1,
        xref="x domain", yref="y domain",
        x=0.99, y=0.03, xanchor="right", yanchor="bottom",
        showarrow=False,
        font={"family": PLOT_SANS, "size": 10, "color": MUTED},
        bgcolor="rgba(252,252,250,0.85)",
        bordercolor=HAIRLINE, borderwidth=0.5, borderpad=4, align="right",
    )


def _zoom_range(
    central: pd.Series,
    lower: pd.Series,
    upper: pd.Series,
    years: pd.Series | None = None,
    focus_year: int | None = None,
) -> list[float]:
    """Y-range fitted to the band near the inspected year.

    Fitting the full-series envelope made zoom a near no-op — the widest
    late-horizon years set the range (CX-22).  When ``years`` and
    ``focus_year`` are given, the fit window is the decade ending at the
    inspected year (clamped inside the series), so zoom inspects the band
    where the cursor sits; pointwise central ± 1.5× each band side.
    """
    central = pd.Series(central).reset_index(drop=True)
    lower = pd.Series(lower).reset_index(drop=True)
    upper = pd.Series(upper).reset_index(drop=True)
    if years is not None and focus_year is not None and len(years):
        year_series = pd.Series(years).astype(int).reset_index(drop=True)
        window_end = int(
            min(max(int(focus_year), int(year_series.min()) + 9), int(year_series.max()))
        )
        mask = (year_series >= window_end - 9) & (year_series <= window_end)
        if bool(mask.any()):
            central = central[mask]
            lower = lower[mask]
            upper = upper[mask]
    low = float((central - 1.5 * (central - lower)).min())
    high = float((central + 1.5 * (upper - central)).max())
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        return [float(lower.min()), float(upper.max())]
    return [low, high]


def _range_plot_values(frame: pd.DataFrame, metric: str) -> tuple[pd.Series, pd.Series, pd.Series]:
    scale = 1e6 if metric in {"energy", "emissions"} else 1.0
    return (
        frame["lower"] / scale,
        frame["central"] / scale,
        frame["upper"] / scale,
    )


def _axis(title: str) -> dict[str, Any]:
    return {
        # A10 defects 2, 4, 5: a 8px standoff let the rotated title sit on top
        # of the widest tick label once the web font swapped in. 16px clears
        # every tick label this app draws.
        "title": {"text": title, "font": {"size": 11, "color": MUTED}, "standoff": 16},
        "showline": True,
        "linecolor": "#4a4945",
        "linewidth": 0.8,
        "ticks": "outside",
        "tickfont": {"size": 11, "color": MUTED},
        "gridcolor": HAIRLINE,
        "gridwidth": 0.55,
        "zeroline": False,
        "automargin": True,
    }


def _layout(title: str, y_title: str, *, height: int = 350) -> dict[str, Any]:
    return {
        "height": height,
        "paper_bgcolor": PAPER,
        "plot_bgcolor": PAPER,
        "font": {"family": PLOT_SANS, "size": 11, "color": INK},
        "margin": {"l": 64, "r": 12, "t": 58, "b": 52},
        "title": {
            "text": title,
            "x": 0,
            "xanchor": "left",
            "font": {"family": PLOT_SANS, "size": 14, "color": INK},
        },
        "xaxis": {**_axis("Modeled year"), "dtick": 10, "showgrid": False},
        "yaxis": _axis(y_title),
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
        "hoverlabel": HOVER_LABEL_STYLE,
        "hovermode": "x unified",
    }


def _hover_unit_lines(unit: str) -> str:
    """Keep a complete unit/basis readable inside a narrow hover card."""
    actual_fleet = " · actual FHWA MV-1 2024 fleet (STI excluded)"
    if actual_fleet in unit:
        measure = unit.replace(actual_fleet, "")
        return f"{measure}<br>actual FHWA MV-1 2024 fleet<br>STI excluded"
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


def _normalized_values(frame: pd.DataFrame, metric: str, scope: str) -> pd.Series:
    if scope == "cav":
        if metric == "energy":
            return frame["cav_carrier_input_kwh_eq"] / 1e6
        if metric == "emissions":
            return frame["cav_direct_co2_kg"] / 1e6
        return frame["cav_direct_co2_kg"] / frame["cav_carrier_input_kwh_eq"]
    if scope == "sti":
        if metric == "energy":
            return frame["sti_incremental_electricity_kwh"] / 1e6
        if metric == "emissions":
            return frame["sti_grid_direct_co2_kg"] / 1e6
        return frame["sti_grid_direct_co2_kg"] / frame["sti_incremental_electricity_kwh"]
    if metric == "energy":
        return frame["normalized_bundle_carrier_input_kwh_eq"] / 1e6
    if metric == "emissions":
        return frame["normalized_bundle_direct_co2_kg"] / 1e6
    return frame["normalized_bundle_direct_co2_kg"] / frame[
        "normalized_bundle_carrier_input_kwh_eq"
    ]


# The registered reference bundle of the uniform comparator layer, which did
# not move at v3.1c.  Used only where no frame is available to read from.
ATLAS_REFERENCE_STI_UNITS = 1000


def _sti_units_in(frame: "pd.DataFrame | None") -> int | None:
    """The STI unit count this frame is normalized on, or None.

    Read rather than assumed: the uniform comparator bundles carry 1,000
    standardized reference-site equivalents and the delivered central's
    equal-size companion carries the measured national ratio of 2,988 units
    per million vehicles, and both are drawn by the same functions.
    """
    if frame is None or "sti_capacity_intersections" not in getattr(
        frame, "columns", []
    ):
        return None
    unique = frame["sti_capacity_intersections"].dropna().unique()
    if len(unique) != 1:
        return None
    return int(round(float(unique[0])))


def normalized_metric_unit(
    metric: str, scope: str, sti_units: int | None = None
) -> str:
    units = ATLAS_REFERENCE_STI_UNITS if sti_units is None else sti_units
    suffix = {
        "cav": "per 1M registered vehicles",
        "sti": f"per {units:,} STI units",
        "bundle": f"on the equal-size comparison (1M vehicles + {units:,} STI units)",
    }[scope]
    if metric == "energy":
        return f"GWh-eq yr⁻¹ {suffix}"
    if metric == "emissions":
        return f"kt CO₂ yr⁻¹ {suffix}"
    return "kg CO₂ kWh-eq⁻¹"


def _normalized_triptych_axis_titles(scope: str) -> dict[str, str]:
    """Unit-only rotated axis titles.

    A10 defects 1-3, 6-7: the retired two-line titles repeated the metric
    name AND the normalization denominator inside every stacked panel.  The
    rotated string was taller than one panel, so panel a's title collided
    glyph-on-glyph with panel b's and the second line struck through the
    tick labels.  The name now lives in the panel title (once) and the
    denominator in one figure footnote (once), leaving the axis to carry
    only its unit.
    """
    del scope  # the denominator is stated once, in the figure footnote
    return dict(AXIS_UNITS)


CASE_TRIPTYCH_AXIS_TITLES = dict(CASE_AXIS_UNITS)


def _basis_footnote(
    fig: go.Figure, basis_key: str, frame: "pd.DataFrame | None" = None,
    *, cav_only: bool = False,
) -> None:
    """State the normalization denominator once, under the panels.

    The denominator is READ from the frame being drawn where the frame carries
    it, because two different equal-size normalizations are live (1,000 units
    for the uniform comparator bundles, 2,988 for the delivered central's
    companion) and one hard-coded number would be wrong under one of them.
    """
    text = BASIS_FOOTNOTES[basis_key]
    if basis_key == "state_scaled" and cav_only:
        text = "Actual FHWA MV-1 2024 fleet per state.\nCAV only; STI excluded."
    # A frame that carries no site count is on the registered reference bundle
    # of the uniform comparator layer (1,000 standardized reference-site
    # equivalents, ``state_atlas_summary_v1.json``); the delivered central's
    # companion carries its own count and is read from the frame.
    units = _sti_units_in(frame)
    if units is None and frame is not None:
        units = ATLAS_REFERENCE_STI_UNITS
    if units is not None and basis_key in {"bundle", "sti"}:
        text = (
            "Equal-size comparison (per entry):\n"
            f"1M registered vehicles + {units:,} STI units."
            if basis_key == "bundle"
            else f"Normalized basis: {units:,} STI units."
        )
    # Plotly annotations never wrap automatically. The old sentence was
    # wider than a state-panel column (and a phone), so its denominator was
    # cut off. Reserve the required bottom space without shrinking the data.
    lines = [
        line
        for paragraph in text.splitlines()
        for line in textwrap.wrap(paragraph, width=44, break_long_words=False, break_on_hyphens=False)
    ]
    previous_bottom = int(fig.layout.margin.b or 0)
    bottom = max(previous_bottom, 56 + 14 * len(lines))
    if bottom > previous_bottom:
        fig.update_layout(
            margin={"b": bottom},
            height=int(fig.layout.height or 350) + bottom - previous_bottom,
        )
    fig.add_annotation(
        text="<br>".join(lines),
        xref="paper", yref="paper",
        x=0, y=0, xanchor="left", yanchor="top", yshift=-46,
        showarrow=False,
        align="left",
        font={"family": PLOT_SANS, "size": 10, "color": MUTED},
    )


def normalized_value(data: Mapping[str, Any], state: str, scenario: str, year: int,
                     metric: str, scope: str) -> float:
    frame = state_slice(data, state)
    row = frame.loc[
        (frame["scenario_bundle"] == scenario) & (frame["year"] == year)
    ]
    if len(row) != 1:
        raise ValueError(f"Expected one normalized row for {state}/{scenario}/{year}")
    return float(_normalized_values(row, metric, scope).iloc[0])


def _triptych(*, height: int) -> go.Figure:
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.065,
        subplot_titles=[PANEL_TITLES[key] for key in PATHWAY_METRICS],
    )
    for annotation in fig.layout.annotations:
        annotation.update(
            x=0,
            xanchor="left",
            font={"family": PLOT_SANS, "size": 14, "color": INK},
        )
    fig.update_layout(
        height=height,
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        font={"family": PLOT_SANS, "size": 11, "color": INK},
        # b=88 leaves room for the one-line normalization-basis footnote
        # that replaced the denominator repeated inside all three rotated
        # axis titles (A10 defects 1-3).
        # t=82 is the ONE-ROW legend allowance; every builder that fills this
        # figure calls reserve_legend_rows() once its traces exist, which
        # grows t (and the figure) to the rows the legend actually wraps onto
        # at both capture widths (V2-08).
        margin={"l": 72, "r": 14, "t": TRIPTYCH_BASE_TOP_MARGIN_PX, "b": 88},
        legend={
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": 1.065,
            "yanchor": "bottom",
            # X6 / A10 defects 8-11: entrywidth 0 means "size each entry to
            # its own characters". It must be stated EXPLICITLY: the host
            # injects entrywidthmode="pixels" into the Plotly layout, so
            # with no entrywidth the entries were laid out on slots
            # narrower than their text -- each name over-printed by the
            # next swatch, the last one cut mid-word.
            "entrywidth": 0,
            # X6 / A10 defects 8-11: the retired fixed 190 px entry slot
            # over-printed every legend name longer than the slot
            # ("relative widths unchaStgted-scaled central") and truncated
            # the last entry mid-word.  Plotly sizes each entry to its own
            # text instead; every legend name in this module is kept short
            # enough to wrap cleanly.
            "font": {"size": 11},
            "bgcolor": "rgba(0,0,0,0)",
        },
        hoverlabel=HOVER_LABEL_STYLE,
        hovermode="x unified",
        hoversubplots="axis",
    )
    return fig


def make_normalized_triptych(
    data: Mapping[str, Any],
    state: str,
    scope: str,
    emphasized_scenario: str,
    selected_year: int,
    *,
    horizon: int = 2050,
    compare_scenarios: bool = False,
    show_national_median: bool = True,
    range_object: str = "none",
    zoom_to_band: bool = False,
) -> go.Figure:
    """One synchronized three-panel figure for one normalized state.

    Registered scenarios are lines, never a probability ribbon.  Optional
    fills are exhaustive engineering support ranges around the selected
    deterministic path and are never labelled as statistical uncertainty.
    ``zoom_to_band`` fits each panel's y-range to the displayed support in
    the decade ending at the inspected year (central ± 1.5× each side) so
    narrow supports become inspectable where the cursor sits; comparator
    branches may clip in that mode.
    """
    source = state_slice(data, state).loc[lambda frame: frame["year"] <= horizon].copy()
    fig = _triptych(height=735 if horizon <= 2050 else 790)
    axis_titles = _normalized_triptych_axis_titles(scope)
    scenario_roster = ("low", "medium", "high") if compare_scenarios else (emphasized_scenario,)

    range_label = None
    # CX-26: the engineering fills were nearly invisible at alpha 0.11-0.14;
    # the fill is raised slightly and every support now carries visible edge
    # lines in the metric's own hue so the legend never advertises an object
    # the eye cannot find.
    band_alpha = 0.16
    if range_object != "none":
        if range_object not in NATIONAL_RANGE_LABELS:
            raise ValueError(f"Unknown national range object: {range_object}")
        range_label = NATIONAL_RANGE_LABELS[range_object]
        if range_object == "conditioned_grid_conversion":
            # Legibility: the conditioned support is deliberately narrow, so a
            # slightly stronger fill plus the frozen validated maximum
            # one-sided width keeps the legend honest about what to look for.
            band_alpha = 0.20
            max_side = float(
                data["engineering_validation"][
                    "maximum_conditioned_single_side_relative_to_central"
                ]
            )
            range_label = f"{range_label} (≤{max_side * 100:.1f}%)"

    for row_index, metric in enumerate(PATHWAY_METRICS, start=1):
        metric_spec = PATHWAY_METRICS[metric]
        source["plot_value"] = _normalized_values(source, metric, scope)
        pivot = source.pivot(
            index="year", columns="scenario_bundle", values="plot_value"
        ).sort_index()
        color = METRIC_COLORS[metric]
        # In compare mode the y-range is fitted to the emphasized scenario and
        # its selected support; distant comparator branches may clip.
        fit_values: list[pd.Series] = []
        zoom_bounds: list[float] | None = None
        if compare_scenarios:
            fit_values.append(pivot[emphasized_scenario])
        if range_object != "none":
            support = engineering_band(
                data, state, emphasized_scenario, scope, metric, range_object
            ).loc[lambda frame: frame["year"] <= horizon]
            lower, central_scaled, upper = _range_plot_values(support, metric)
            max_side = float(
                np.maximum(
                    (support["lower"] / support["central"] - 1.0).abs(),
                    (support["upper"] / support["central"] - 1.0).abs(),
                ).max()
            )
            _panel_band_annotation(fig, row_index, max_side)
            if zoom_to_band:
                zoom_bounds = _zoom_range(
                    central_scaled, lower, upper, support["year"], int(selected_year)
                )
            if compare_scenarios:
                fit_values.extend([lower, upper])
            edge_color = f"rgba({_BAND_RGB[metric]},{_BAND_EDGE_ALPHA})"
            fig.add_trace(
                go.Scatter(
                    x=support["year"],
                    y=lower,
                    mode="lines",
                    line={"width": 0.9, "color": edge_color},
                    hoverinfo="skip",
                    showlegend=False,
                    legendgroup=f"national-range-{range_object}",
                ),
                row=row_index,
                col=1,
            )
            fillcolor = f"rgba({_BAND_RGB[metric]},{band_alpha})"
            fig.add_trace(
                go.Scatter(
                    x=support["year"],
                    y=upper,
                    mode="lines",
                    line={"width": 0.9, "color": edge_color},
                    fill="tonexty",
                    fillcolor=fillcolor,
                    name=range_label,
                    legendgroup=f"national-range-{range_object}",
                    showlegend=row_index == 1,
                    customdata=np.column_stack([lower, upper]),
                    hovertemplate=(
                        f"<b>{metric_spec.short_label}</b><br>Scenario support"
                        f"<br>Lower: %{{customdata[0]:{metric_spec.hover_format}}}"
                        f"<br>Upper: %{{customdata[1]:{metric_spec.hover_format}}}"
                        "<extra></extra>"
                    ),
                ),
                row=row_index,
                col=1,
            )
        for scenario in scenario_roster:
            emphasized = scenario == emphasized_scenario
            fig.add_trace(
                go.Scatter(
                    x=pivot.index,
                    y=pivot[scenario],
                    mode="lines",
                    line={
                        "color": color,
                        "width": 2.8 if emphasized else 1.15,
                        "dash": SCENARIO_DASHES[scenario],
                    },
                    opacity=1.0 if emphasized else 0.55,
                    name=f"{scenario.title()} deterministic",
                    legendgroup=f"scenario-{scenario}",
                    showlegend=row_index == 1,
                    hovertemplate=(
                        f"<b>{metric_spec.short_label}</b><br>{scenario.title()}: "
                        f"%{{y:{metric_spec.hover_format}}}"
                        f"<br>{_hover_unit_lines(normalized_metric_unit(metric, scope))}"
                        "<extra></extra>"
                    ),
                ),
                row=row_index,
                col=1,
            )

        if show_national_median:
            annual = data["annual"].loc[
                (data["annual"]["scope_role"] == PRIMARY_SCOPE)
                & (data["annual"]["scenario_bundle"] == emphasized_scenario)
                & (data["annual"]["year"] <= horizon)
            ].copy()
            annual["plot_value"] = _normalized_values(annual, metric, scope)
            median = annual.groupby("year", as_index=False)["plot_value"].median()
            if compare_scenarios:
                fit_values.append(median["plot_value"])
            fig.add_trace(
                go.Scatter(
                    x=median["year"],
                    y=median["plot_value"],
                    mode="lines",
                    line={"color": "#85827c", "width": 1.0, "dash": "longdash"},
                    name="50-state-only median",
                    legendgroup="national-median",
                    showlegend=row_index == 1,
                    hovertemplate=(
                        f"<b>{metric_spec.short_label}</b><br>50-state median: "
                        f"%{{y:{metric_spec.hover_format}}}<extra></extra>"
                    ),
                ),
                row=row_index,
                col=1,
            )

        fig.update_yaxes(
            **_axis(axis_titles[metric]),
            row=row_index,
            col=1,
        )
        if fit_values:
            fit_low = float(min(series.min() for series in fit_values))
            fit_high = float(max(series.max() for series in fit_values))
            pad = (fit_high - fit_low) * 0.06
            if pad <= 0:
                pad = max(abs(fit_high), 1.0) * 0.05
            fig.update_yaxes(
                range=[fit_low - pad, fit_high + pad], row=row_index, col=1
            )
        # Zoom-to-band wins over the compare fit: it is an explicit request to
        # inspect the narrow support, so comparator branches may clip.
        if zoom_bounds is not None:
            fig.update_yaxes(range=zoom_bounds, row=row_index, col=1)

    if 2025 <= selected_year <= horizon:
        fig.add_vline(
            x=selected_year,
            line={"color": "#c96a3b", "width": 1.0, "dash": "dot"},
            row="all",
            col=1,
        )
    fig.update_xaxes(range=[2025, horizon], tick0=2030, dtick=10, showgrid=False)
    fig.update_xaxes(title_text="Modeled year", row=3, col=1)
    _basis_footnote(fig, scope, source)
    fig.update_layout(
        uirevision=(
            f"normalized-triptych-{state}-{scope}-{horizon}-{range_object}-{zoom_to_band}"
        )
    )
    reserve_legend_rows(fig)
    return fig


POLICY_CENTRAL_COLOR = "#2e6f7b"
_BAND_FILL_ALPHA = 0.20
_BAND_EDGE_ALPHA = 0.55
_BAND_RGB = {
    "energy": "39,97,140",
    "emissions": "166,70,61",
    "carbon_intensity": "110,90,135",
}


def policy_central_normalized_value(
    pc: Mapping[str, Any], state: str, year: int, metric: str, scope: str,
    *, weather: bool = False,
) -> float:
    """Point readout on the policy-central (or weather-variant) path."""
    frame = policy_central_state_slice(pc, state, weather=weather)
    row = frame.loc[frame["year"] == int(year)]
    if len(row) != 1:
        raise ValueError(f"Expected one policy-central row for {state}/{year}")
    return float(_normalized_values(row, metric, scope).iloc[0])


def make_policy_central_triptych(
    pc: Mapping[str, Any],
    atlas: Mapping[str, Any],
    state: str,
    scope: str,
    selected_year: int,
    *,
    horizon: int = 2050,
    compare_scenarios: bool = False,
    show_weather_variant: bool = False,
    show_national_median: bool = True,
    central_label: str = "Policy-central",
    show_sensitivity_envelope: bool = False,
    zoom_to_band: bool = False,
) -> go.Figure:
    """Per-state central pathway triptych with an optional sensitivity envelope.

    The optional shaded object is an author-model sensitivity
    envelope from the packaged load-model draws.  It is a sensitivity check
    rather than manuscript uncertainty, because the sampled priors are not
    current manuscript authority.  It is not a forecast,
    confidence interval, credible interval, or empirical prediction interval.
    Uniform low/medium/high comparator bundles appear as thin lines on demand.

    The same figure also renders the market-calibrated central: pass the
    market bundle as ``pc`` with ``central_label="Market-calibrated"``.  That
    bundle packages no sensitivity envelope, so no envelope is drawn, no
    weather variant exists, and a state with no turning point by 2075 (NaN)
    draws no marker.

    When requested, every enveloped panel is annotated with its maximum
    one-sided deviation, and ``zoom_to_band`` fits each panel's y-range to
    the band in the decade ending at the inspected year (central ± 1.5×
    each side) so the narrow intensity band becomes inspectable on demand;
    comparator lines and the 50-state-only median may clip in that mode.

    Every panel's y-range is fitted to the panel's registered SUBJECT — the
    emphasized central, its displayed band and the weather-adjusted variant
    of that same central — in every mode (CX-21, extended by V2-10).  Lines
    drawn for CONTEXT — the uniform comparator bundles and the 50-state-only
    median — may clip; each one that does is named, with its value at the
    displayed horizon, in the panel's "off scale" annotation, and all of them
    can be toggled in the legend.
    """
    source = policy_central_state_slice(pc, state).loc[
        lambda frame: frame["year"] <= horizon
    ]
    weather = (
        policy_central_state_slice(pc, state, weather=True).loc[
            lambda frame: frame["year"] <= horizon
        ]
        if show_weather_variant and "weather_annual" in pc
        else None
    )
    comparators = (
        state_slice(atlas, state).loc[lambda frame: frame["year"] <= horizon]
        if compare_scenarios
        else None
    )
    fig = _triptych(height=735 if horizon <= 2050 else 790)
    axis_titles = _normalized_triptych_axis_titles(scope)

    # The packaged author-model envelope is hidden by default and exists only
    # for bundles that explicitly carry it; never fabricate it for other paths.
    draw_band = (
        show_sensitivity_envelope
        and scope == "bundle"
        and "band_exact" in pc
    )
    band_label = None
    band_frames: dict[str, pd.DataFrame] = {}
    ceiling_prior_mode = False
    if draw_band:
        # A bundle's band need not carry every panel.  At v3.1c the expert
        # band carries energy consumption and direct CO2 emissions and no
        # carbon-intensity interval exists, so that panel draws its central
        # line with no fill rather than a fabricated one.
        band_frames = {
            metric: policy_central_band(pc, state, metric)
            for metric in PATHWAY_METRICS
            if band_metric_is_packaged(pc, metric)
        }
        draw_band = bool(band_frames)
        ceiling_prior_mode = band_has_ceiling_prior(next(iter(band_frames.values())))
        if ceiling_prior_mode:
            # Owner-approved v4 display: plain registered name; per-panel
            # annotations carry the near- and far-horizon widths on one
            # same-year basis (A5: never a smaller number further out).
            band_label = "5th-95th percentile interval"
        else:
            # V1-7: the per-panel annotations carry the one-sided widths, so
            # the legend entry stays short.
            band_label = "load-model (L2) sensitivity envelope"

    for row_index, metric in enumerate(PATHWAY_METRICS, start=1):
        metric_spec = PATHWAY_METRICS[metric]
        scale = 1e6 if metric in {"energy", "emissions"} else 1.0
        panel_zoom: list[float] | None = None
        # CX-21, extended by V2-10 (2026-09-03): the panel y-range is ALWAYS
        # fitted to the panel's registered SUBJECT -- the emphasized central,
        # its displayed band, and the weather-adjusted variant of that same
        # central.  CX-21 fitted it only in compare mode, so outside compare
        # the panel autoranged over every drawn trace, including the
        # always-on 50-state-only median.  That median is CONTEXT, not the
        # subject: on the reference-bundle basis through 2050 it inflates the
        # panel span by up to 2.2x for direct CO2 (CA) and 6.0x for carbon
        # intensity (ND), leaving the policy-registered central squeezed into
        # a sixth of the panel height with its band invisible.  Context lines
        # -- the comparator bundles and the median -- may now clip, and every
        # one that does is named in the "off scale" annotation, so nothing
        # leaves the frame silently.
        fit_values: list[pd.Series] = []
        offscale_series: dict[str, pd.Series] = {}
        if draw_band and metric in band_frames:
            full_band = band_frames[metric]
            band = full_band.loc[lambda frame: frame["year"] <= horizon]
            lower = band["lower"] / scale
            upper = band["upper"] / scale
            _panel_band_annotation(
                fig,
                row_index,
                text=band_annotation_text(full_band, metric, horizon=int(horizon)),
            )
            if zoom_to_band:
                panel_zoom = _zoom_range(
                    band["central"] / scale, lower, upper,
                    band["year"], int(selected_year),
                )
            fit_values.extend([lower, upper])
            rgb = _BAND_RGB[metric]
            fig.add_trace(
                go.Scatter(
                    x=band["year"],
                    y=lower,
                    mode="lines",
                    line={
                        "width": 0.9,
                        "color": f"rgba({rgb},{_BAND_EDGE_ALPHA})",
                    },
                    hoverinfo="skip",
                    showlegend=False,
                    legendgroup="pc-band",
                ),
                row=row_index,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=band["year"],
                    y=upper,
                    mode="lines",
                    line={
                        "width": 0.9,
                        "color": f"rgba({rgb},{_BAND_EDGE_ALPHA})",
                    },
                    fill="tonexty",
                    fillcolor=f"rgba({rgb},{_BAND_FILL_ALPHA})",
                    name=band_label,
                    legendgroup="pc-band",
                    showlegend=row_index == 1,
                    customdata=np.column_stack([lower, upper]),
                    hovertemplate=(
                        f"<b>{metric_spec.short_label}</b><br>"
                        + (
                            "5th–95th percentile interval"
                            if ceiling_prior_mode
                            else "Load-model sensitivity envelope"
                        )
                        + f"<br>p05: %{{customdata[0]:{metric_spec.hover_format}}}"
                        f"<br>p95: %{{customdata[1]:{metric_spec.hover_format}}}"
                        "<extra></extra>"
                    ),
                ),
                row=row_index,
                col=1,
            )

        if comparators is not None:
            pivot = comparators.copy()
            pivot["plot_value"] = _normalized_values(pivot, metric, scope)
            pivot = pivot.pivot(
                index="year", columns="scenario_bundle", values="plot_value"
            ).sort_index()
            for scenario in ("low", "medium", "high"):
                offscale_series[scenario] = pivot[scenario]
                fig.add_trace(
                    go.Scatter(
                        x=pivot.index,
                        y=pivot[scenario],
                        mode="lines",
                        line={
                            "color": METRIC_COLORS[metric],
                            "width": 1.05,
                            "dash": SCENARIO_DASHES[scenario],
                        },
                        opacity=0.5,
                        name=f"{scenario.title()} · comparator bundle",
                        legendgroup=f"comparator-{scenario}",
                        showlegend=row_index == 1,
                        hovertemplate=(
                            f"<b>{metric_spec.short_label}</b><br>"
                            f"{scenario.title()} comparator: "
                            f"%{{y:{metric_spec.hover_format}}}<extra></extra>"
                        ),
                    ),
                    row=row_index,
                    col=1,
                )

        if weather is not None:
            weather_values = _normalized_values(weather, metric, scope)
            # The weather variant is the SAME registered central under a
            # named deterministic workload, so it is part of the subject.
            fit_values.append(weather_values)
            fig.add_trace(
                go.Scatter(
                    x=weather["year"],
                    y=weather_values,
                    mode="lines",
                    line={
                        "color": METRIC_COLORS[metric],
                        "width": 1.5,
                        "dash": "dashdot",
                    },
                    opacity=0.85,
                    name="weather-adjusted variant",
                    legendgroup="pc-weather",
                    showlegend=row_index == 1,
                    hovertemplate=(
                        f"<b>{metric_spec.short_label}</b><br>Weather-adjusted: "
                        f"%{{y:{metric_spec.hover_format}}}<extra></extra>"
                    ),
                ),
                row=row_index,
                col=1,
            )

        central_values = _normalized_values(source, metric, scope)
        fit_values.append(central_values)
        fig.add_trace(
            go.Scatter(
                x=source["year"],
                y=central_values,
                mode="lines",
                line={"color": METRIC_COLORS[metric], "width": 2.8, "dash": "solid"},
                name=central_label,
                legendgroup="pc-central",
                showlegend=row_index == 1,
                hovertemplate=(
                    f"<b>{metric_spec.short_label}</b><br>{central_label}"
                    f"<br>%{{y:{metric_spec.hover_format}}}"
                    f"<br>{_hover_unit_lines(normalized_metric_unit(metric, scope, _sti_units_in(source)))}"
                    "<extra></extra>"
                ),
            ),
            row=row_index,
            col=1,
        )

        if show_national_median:
            annual = pc["annual"].loc[
                (pc["annual"]["scope_role"] == PRIMARY_SCOPE)
                & (pc["annual"]["year"] <= horizon)
            ].copy()
            annual["plot_value"] = _normalized_values(annual, metric, scope)
            median = annual.groupby("year", as_index=False)["plot_value"].median()
            # V2-10: context, not subject -- it may clip, and says so.
            offscale_series["50-state-only median"] = median.set_index("year")[
                "plot_value"
            ]
            fig.add_trace(
                go.Scatter(
                    x=median["year"],
                    y=median["plot_value"],
                    mode="lines",
                    line={"color": "#85827c", "width": 1.0, "dash": "longdash"},
                    name="50-state-only median",
                    legendgroup="national-median",
                    showlegend=row_index == 1,
                    hovertemplate=(
                        f"<b>{metric_spec.short_label}</b><br>{central_label}"
                        "<br>50-state median: "
                        f"%{{y:{metric_spec.hover_format}}}<extra></extra>"
                    ),
                ),
                row=row_index,
                col=1,
            )

        fig.update_yaxes(**_axis(axis_titles[metric]), row=row_index, col=1)
        if fit_values:
            fit_low = float(min(series.min() for series in fit_values))
            fit_high = float(max(series.max() for series in fit_values))
            pad = (fit_high - fit_low) * 0.06
            if pad <= 0:
                pad = max(abs(fit_high), 1.0) * 0.05
            fig.update_yaxes(
                range=[fit_low - pad, fit_high + pad], row=row_index, col=1
            )
            _declare_offscale_comparators(
                fig, row_index, offscale_series,
                fit_low - pad, fit_high + pad, int(horizon),
                metric_spec.hover_format,
            )
        # Zoom-to-band wins over the subject fit: it is an explicit request
        # to inspect the narrow band; context lines may clip.
        if panel_zoom is not None:
            fig.update_yaxes(range=panel_zoom, row=row_index, col=1)
            _declare_offscale_comparators(
                fig, row_index, offscale_series,
                panel_zoom[0], panel_zoom[1], int(horizon),
                metric_spec.hover_format,
            )

    if 2025 <= selected_year <= horizon:
        fig.add_vline(
            x=selected_year,
            line={"color": "#c96a3b", "width": 1.0, "dash": "dot"},
            row="all",
            col=1,
        )
    # A right-censored onset (NaN on the market-calibrated frame) draws no
    # marker: the absence of an onset is reported, never imputed as a year.
    onset_raw = pc["turning"].loc[
        pc["turning"]["state"] == str(state).upper(),
        "sustained_nonincrease_onset_year",
    ].iloc[0]
    if pd.notna(onset_raw):
        onset = int(onset_raw)
        if 2025 <= onset <= horizon:
            fig.add_vline(
                x=onset,
                line={"color": MUTED, "width": 1.0, "dash": "dashdot"},
                row="all",
                col=1,
            )
            fig.add_annotation(
                x=onset,
                # Anchor inside the lower edge of panel b, away from both its
                # title and the wrapped band readout at the upper-right.
                y=0.22,
                yref="y2 domain",
                text=f"{TURNING_POINT_LOWER}<br>{onset}",
                showarrow=False,
                xanchor="left" if onset <= (2025 + horizon) / 2 else "right",
                xshift=4 if onset <= (2025 + horizon) / 2 else -4,
                yanchor="bottom",
                align="left" if onset <= (2025 + horizon) / 2 else "right",
                font={"family": PLOT_SANS, "size": 9, "color": MUTED},
                bgcolor="rgba(252,252,250,0.82)",
                borderpad=2,
            )
    fig.update_xaxes(range=[2025, horizon], tick0=2030, dtick=10, showgrid=False)
    fig.update_xaxes(title_text="Modeled year", row=3, col=1)
    _basis_footnote(fig, scope, source)
    fig.update_layout(
        uirevision=(
            f"policy-central-triptych-{central_label}-{state}-{scope}-{horizon}-"
            f"{compare_scenarios}-{show_weather_variant}-"
            f"{show_sensitivity_envelope}-{zoom_to_band}"
        )
    )
    reserve_legend_rows(fig)
    return fig


# ---------------------------------------------------------------------------
# v2.2 live exploratory adapter.  This is intentionally separate from the
# frozen publication pathway renderer above: a live structural what-if must
# never silently replace the registered Expert-central line.
# ---------------------------------------------------------------------------
_EXPLORER_METRIC_COLUMNS = {
    "energy": "energy_kwh_eq",
    "emissions": "direct_co2_kg",
    "carbon_intensity": "intensity_kg_per_kwh_eq",
}


def make_v22_exploratory_triptych(
    exploratory: pd.DataFrame,
    frozen_expert_state: pd.DataFrame,
    metadata: Mapping[str, Any],
    selected_year: int,
    *,
    horizon: int = 2050,
) -> go.Figure:
    """Compare one live structural what-if with the frozen stated-policy scenario.

    ``exploratory`` is emitted by :mod:`v22_explorer_adapter`.  Its solid line
    is a deterministic scenario.  The dashed line is the immutable registered
    reference.  A p05-p95 fill is drawn only when at least one registered L2
    driver is active; those parameter draws are conditional on the fixed
    structural settings and are never mixed with named scenario paths.
    """

    required = {"state", "year"}
    required.update(
        f"{column}_{suffix}"
        for column in _EXPLORER_METRIC_COLUMNS.values()
        for suffix in ("central", "p05", "p50", "p95")
    )
    missing = sorted(required - set(exploratory.columns))
    if missing:
        raise ValueError(f"exploratory frame missing columns: {missing}")
    if exploratory["state"].nunique() != 1:
        raise ValueError("exploratory triptych expects exactly one state")

    live = exploratory.loc[
        (exploratory["year"] >= 2025) & (exploratory["year"] <= int(horizon))
    ].sort_values("year")
    frozen = frozen_expert_state.loc[
        (frozen_expert_state["year"] >= 2025)
        & (frozen_expert_state["year"] <= int(horizon))
    ].sort_values("year")
    if list(live["year"]) != list(frozen["year"]):
        raise ValueError("exploratory and frozen Expert-central year lattices differ")

    active_drivers = tuple(metadata.get("active_uncertainty_drivers", ()))
    show_band = bool(active_drivers)
    fig = _triptych(height=735 if horizon <= 2050 else 790)
    axis_titles = _normalized_triptych_axis_titles("bundle")

    for row_index, metric in enumerate(PATHWAY_METRICS, start=1):
        metric_spec = PATHWAY_METRICS[metric]
        adapter_metric = _EXPLORER_METRIC_COLUMNS[metric]
        scale = 1e6 if metric in {"energy", "emissions"} else 1.0
        central = live[f"{adapter_metric}_central"] / scale
        lower = live[f"{adapter_metric}_p05"] / scale
        median = live[f"{adapter_metric}_p50"] / scale
        upper = live[f"{adapter_metric}_p95"] / scale
        color = METRIC_COLORS[metric]

        if not ((lower <= median) & (median <= upper)).all():
            raise ValueError(f"{metric}: exploratory quantile order is invalid")
        if show_band:
            denominator = median.abs().replace(0.0, np.nan)
            full_width = ((upper - lower) / denominator).replace(
                [np.inf, -np.inf], np.nan
            )
            max_width = float(full_width.max())
            _panel_band_annotation(
                fig,
                row_index,
                text=f"max full p05–p95 / p50 {relative_pct_text(max_width)}",
            )
            rgb = _BAND_RGB[metric]
            fig.add_trace(
                go.Scatter(
                    x=live["year"],
                    y=lower,
                    mode="lines",
                    line={"width": 0.8, "color": f"rgba({rgb},0.55)"},
                    hoverinfo="skip",
                    showlegend=False,
                    legendgroup="v22-explorer-band",
                ),
                row=row_index,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=live["year"],
                    y=upper,
                    mode="lines",
                    line={"width": 0.8, "color": f"rgba({rgb},0.55)"},
                    fill="tonexty",
                    fillcolor=f"rgba({rgb},0.18)",
                    name="Registered L2 sensitivity envelope",
                    legendgroup="v22-explorer-band",
                    showlegend=row_index == 1,
                    customdata=np.column_stack([lower, median, upper]),
                    hovertemplate=(
                        f"<b>{metric_spec.short_label}</b>"
                        "<br>Conditional parameter band"
                        f"<br>p05: %{{customdata[0]:{metric_spec.hover_format}}}"
                        f"<br>p50: %{{customdata[1]:{metric_spec.hover_format}}}"
                        f"<br>p95: %{{customdata[2]:{metric_spec.hover_format}}}"
                        "<extra></extra>"
                    ),
                ),
                row=row_index,
                col=1,
            )

        # The frozen reference is deliberately drawn first: at default settings
        # the live solid line sits exactly on it, proving rather than implying
        # parity.  The legend still exposes both identities.
        frozen_values = _normalized_values(frozen, metric, "bundle")
        fig.add_trace(
            go.Scatter(
                x=frozen["year"],
                y=frozen_values,
                mode="lines",
                line={"color": "#6f7377", "width": 1.7, "dash": "dash"},
                name="Frozen delivered central",
                legendgroup="v22-frozen-reference",
                showlegend=row_index == 1,
                hovertemplate=(
                    f"<b>{metric_spec.short_label}</b><br>Frozen delivered central"
                    f"<br>%{{y:{metric_spec.hover_format}}}"
                    f"<br>{_hover_unit_lines(normalized_metric_unit(metric, 'bundle', _sti_units_in(frozen)))}"
                    "<extra></extra>"
                ),
            ),
            row=row_index,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=live["year"],
                y=central,
                mode="lines",
                line={"color": color, "width": 2.8, "dash": "solid"},
                name="Exploratory structural scenario",
                legendgroup="v22-live-scenario",
                showlegend=row_index == 1,
                hovertemplate=(
                    f"<b>{metric_spec.short_label}</b><br>Exploratory scenario"
                    f"<br>%{{y:{metric_spec.hover_format}}}"
                    f"<br>{_hover_unit_lines(normalized_metric_unit(metric, 'bundle', _sti_units_in(frozen)))}"
                    "<extra></extra>"
                ),
            ),
            row=row_index,
            col=1,
        )
        fig.update_yaxes(**_axis(axis_titles[metric]), row=row_index, col=1)

    if 2025 <= int(selected_year) <= int(horizon):
        fig.add_vline(
            x=int(selected_year),
            line={"color": "#c96a3b", "width": 1.0, "dash": "dot"},
            row="all",
            col=1,
        )
    fig.update_xaxes(range=[2025, int(horizon)], tick0=2030, dtick=10, showgrid=False)
    fig.update_xaxes(title_text="Modeled year", row=3, col=1)
    fig.update_layout(
        uirevision=(
            f"v22-explorer-{metadata.get('state', '')}-{horizon}-"
            f"{len(active_drivers)}"
        )
    )
    reserve_legend_rows(fig)
    return fig



# ---------------------------------------------------------------------------
# Multi-state comparison overlay ("Compare states" view).
#
# Fixed six-slot colorblind-validated categorical order.  Colors are assigned
# by SELECTION ORDER and are never recycled within one view: the selection cap
# equals the palette size, so slot i always belongs to the i-th picked state.
# ---------------------------------------------------------------------------
# v3.3: THE PALETTE IS THE MANUSCRIPT'S, AND IT HAS NO GREEN.
#
# The v3.1c slots were six saturated hues chosen for categorical separation,
# and slot 3 was an aqua at hue 159 with saturation 0.73.  Beside slot 2's
# orange that is a RED-GREEN PAIR on the same figure, which the owner ruling
# and the manuscript palette both forbid outright.  The six slots are now the
# manuscript's own measured inks -- the five case-study line inks plus the deep
# red at the top of the map ramp -- ordered so that consecutive slots differ in
# LUMINANCE as well as in hue.  Nothing here is green, so no red is paired with
# a green anywhere on this dashboard.
#
# Source: CLEAR_ATS_50state_expansion/figure_policy_map_v32_2026-09-06/
# PALETTE.md, where each hex is a pixel measurement off the manuscript figures.
COMPARE_STATE_COLORS = (
    "#33697B",  # deep teal   -- the manuscript's both-policies ink
    "#C77B6D",  # red         -- the manuscript's no-state-policy ink
    "#7199B7",  # steel blue
    "#7C3128",  # deep red    -- the top of the map ramp
    "#598798",  # mid teal
    "#8B6F74",  # mauve
)
COMPARE_MAX_STATES = len(COMPARE_STATE_COLORS)
# V2-11: state identity in the compare overlay was carried by HUE ALONE.
# That fails three ways at once here.  (1) Six inks on 2.4 px lines are not
# reliably separable under any colour-vision deficiency, and two of these six
# sit inside one hue family by construction -- the palette is a measured one
# and its cool inks are close.
# (2) The figure prints and screenshots to greyscale, where the six collapse
# to four grey levels.  (3) Worst, the overlay's own data make lines EXACTLY
# coincide: eleven jurisdictions run bitwise-identical direct-CO2 and
# intensity paths from 2052 (see the compare caption), so the last line drawn
# hides every line under it and hue cannot be read at all.
# Each palette slot therefore carries a hue AND a dash pattern AND an onset
# marker symbol.  The dash rides in the legend swatch, so identity survives
# in the legend too; on coincident segments the dash gaps interleave and both
# states stay visible.  The dash is a STATE channel and the symbol is a STATE
# channel; the weather-adjusted variant is a whole-figure MODE and keeps its
# own dash-dot on every line, where identity falls back to hue + symbol.
COMPARE_STATE_DASHES = (
    "solid", "dash", "dot", "longdash", "dashdot", "longdashdot",
)
COMPARE_STATE_SYMBOLS = (
    "circle", "square", "diamond", "triangle-up", "cross", "star",
)
COMPARE_BAND_MAX_STATES = 3
COMPARE_BAND_ALPHA = 0.15
# CX-15: three overlapping fills at 0.15 mix into an unreadable olive on
# coincident clean-grid lines, so the per-band alpha drops when more than two
# envelopes overlap.
COMPARE_BAND_ALPHA_DENSE = 0.08
# CX-15: coincident onset dots (same year, same value on converged lines)
# would overprint; stacked dots are spread across ±0.35 modeled years.  The
# hover always states the true onset year.
COMPARE_ONSET_JITTER_YEARS = 0.35

COMPARE_METRIC_TITLE_STEMS = dict(METRIC_DISPLAY_NAMES)

COMPARE_DEPLOYMENT_SCOPES = ("reference", "state_scaled")

# CX-14: the state-scaled compare basis plots the actual-fleet CAV columns
# (official FHWA MV-1 2024 registered automobiles); STI is excluded because
# its site counts are modeled, not a census.
_STATE_SCALED_COMPARE_UNITS = {
    "energy": "GWh-eq yr⁻¹ · actual FHWA MV-1 2024 fleet (STI excluded)",
    "emissions": "kt CO₂ yr⁻¹ · actual FHWA MV-1 2024 fleet (STI excluded)",
    "carbon_intensity": "kg CO₂ kWh-eq⁻¹ · actual-fleet CAV ratio",
}


def _state_scaled_compare_values(frame: pd.DataFrame, metric: str) -> pd.Series:
    if metric == "energy":
        return frame["cav_carrier_input_kwh_eq_actual_fleet"] / 1e6
    if metric == "emissions":
        return frame["cav_direct_co2_kg_actual_fleet"] / 1e6
    return (
        frame["cav_direct_co2_kg_actual_fleet"]
        / frame["cav_carrier_input_kwh_eq_actual_fleet"]
    )


def _hex_to_rgb_string(hex_color: str) -> str:
    value = hex_color.lstrip("#")
    return ",".join(str(int(value[i:i + 2], 16)) for i in (0, 2, 4))


def make_state_comparison(
    pc: Mapping[str, Any],
    states: list[str] | tuple[str, ...],
    metric: str,
    *,
    show_bands: bool = False,
    weather: bool = False,
    state_names: Mapping[str, str] | None = None,
    height: int = 470,
    central_label: str = "policy-central",
    deployment_scope: str = "reference",
    state_scaled: Mapping[str, Any] | None = None,
) -> go.Figure:
    """Overlay up to six states' central trajectories, 2025-2075.

    Lines are the deterministic per-state central paths, keyed by selection
    order to the fixed six-slot palette.  Each slot carries THREE redundant
    identity channels, never hue alone (V2-11): a hue, a dash pattern (the
    weather variant spends the dash on the mode instead) and a turning-point
    dot symbol.  There is one uncluttered legend and one turning-point dot per
    state at its turning point year.
    Redundant line-end labels are intentionally omitted because
    near-identical endpoints otherwise overprint; dots that would coincide
    exactly (same year AND same value on converged lines) are spread across
    ±0.35 modeled years — the hover states the true turning point year (CX-15).

    ``deployment_scope`` selects the plotted basis (CX-14).  The default
    reference scope plots the equal-size comparison, where
    late-horizon energy convergence is BY DESIGN (identical modelled
    capacity on a common deployment and hardware path).  The state-scaled
    scope requires the packaged state-scaled bundle and plots the actual-fleet
    CAV columns (official FHWA MV-1 2024 registered vehicles; STI
    excluded — modeled units), restoring late-horizon magnitude differences;
    turning point years stay defined on the equal-size comparison (linear
    capacity scaling leaves every turning point unchanged).

    When ``show_bands`` is on and at most ``COMPARE_BAND_MAX_STATES`` states
    are selected, each state's packaged envelope (the displayed
    5th-95th percentile interval for the stated-policy scenario; the
    L2 sensitivity envelope for policy-registered) is filled in the line's own color at
    alpha 0.15, dropping to 0.08 when more than two envelopes overlap
    (CX-15).  D4 (2026-09-04): envelopes are not overlaid in the state-scaled
    scope OF THIS MULTI-STATE COMPARISON -- the qualifier is load-bearing,
    because :func:`make_state_scaled_triptych` does draw them at that same
    basis for a single state, transported at unchanged relative width, and the
    unqualified sentence used to contradict it in front of the reader.
    ``weather`` swaps every line to the
    named deterministic weather-adjusted variant (relabeled, drawn dash-dot);
    envelopes are packaged around the policy-central line, so they are not
    drawn in that mode.  Passing the market-calibrated (v2) bundle draws NO
    envelope (none is packaged — envelopes stay with the applicable central
    lines and are never fabricated), supports no weather variant, and skips
    the turning-point dot for a state with no turning point by 2075 (a
    NaN turning year, reported in words and never as a symbol).
    Nothing here is a forecast or a probability interval.
    """
    roster = [str(state).upper() for state in states]
    if not 1 <= len(roster) <= COMPARE_MAX_STATES:
        raise ValueError(
            f"Compare view accepts 1-{COMPARE_MAX_STATES} states; got {len(roster)}"
        )
    if len(set(roster)) != len(roster):
        raise ValueError(f"Compare view received duplicate states: {roster}")
    if metric not in PATHWAY_METRICS:
        raise ValueError(f"Unknown compare metric: {metric}")
    if deployment_scope not in COMPARE_DEPLOYMENT_SCOPES:
        raise ValueError(f"Unknown compare deployment scale: {deployment_scope}")
    state_scaled_scope = deployment_scope == "state_scaled"
    # See the turning-point dot below: the table has to match the basis.
    turning_source: Mapping[str, Any] = pc
    if not state_scaled_scope and "turning_equal_size" in pc:
        turning_source = dict(pc)
        turning_source["turning"] = pc["turning_equal_size"]
    if state_scaled_scope and state_scaled is None:
        raise ValueError(
            "The state-scaled compare basis requires the packaged state-scaled "
            "bundle; none was provided"
        )
    if state_scaled_scope and weather:
        raise ValueError(
            "The weather-adjusted variant is registered on the reference "
            "policy-central line only; it has no state-scaled basis"
        )
    if weather and "weather_annual" not in pc:
        raise ValueError(
            "No weather-adjusted variant is packaged for this central bundle"
        )

    metric_spec = PATHWAY_METRICS[metric]
    scale = 1e6 if metric in {"energy", "emissions"} else 1.0
    # A10 defects 1-5: the rotated axis title carries the UNIT only. The
    # normalization basis used to ride along inside it ("... per synthetic
    # 1M:1k reference bundle"), which made the rotated string longer than the
    # plot is tall and ran it through the tick labels. It is now stated once,
    # under the frame, by _basis_footnote.
    unit = AXIS_UNITS[metric]
    hover_unit = (
        _STATE_SCALED_COMPARE_UNITS[metric]
        if state_scaled_scope
        else normalized_metric_unit(
            metric, "bundle", _sti_units_in(pc.get("annual"))
        )
    )
    # Envelopes exist only in bundles that package band_exact (expert central
    # and policy-registered); never fabricated for v2, and reference-scope
    # only — the state-scaled basis draws central lines without fills.
    draw_bands = (
        show_bands
        and len(roster) <= COMPARE_BAND_MAX_STATES
        and not weather
        and not state_scaled_scope
        and "band_exact" in pc
        # The overlay draws ONE panel metric, so it asks for that one metric
        # rather than for the whole roster: at v3.1c the expert band has no
        # carbon-intensity interval and that panel simply carries no fill.
        and band_metric_is_packaged(pc, metric)
    )
    band_alpha = COMPARE_BAND_ALPHA_DENSE if len(roster) > 2 else COMPARE_BAND_ALPHA
    names = state_names or {}

    fig = go.Figure()

    # Band fills first so every line draws above every fill.
    if draw_bands:
        for index, state in enumerate(roster):
            rgb = _hex_to_rgb_string(COMPARE_STATE_COLORS[index])
            band = policy_central_band(pc, state, metric)
            band_detail = (
                "5th-95th percentile interval"
                if band_has_ceiling_prior(band)
                else "load-model sensitivity envelope"
            )
            band_name = f"{state} {band_detail}"
            lower = band["lower"] / scale
            upper = band["upper"] / scale
            fig.add_trace(
                go.Scatter(
                    x=band["year"],
                    y=lower,
                    mode="lines",
                    line={"width": 0, "color": "rgba(0,0,0,0)"},
                    hoverinfo="skip",
                    showlegend=False,
                    legendgroup=f"compare-{state}",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=band["year"],
                    y=upper,
                    mode="lines",
                    line={"width": 0, "color": "rgba(0,0,0,0)"},
                    fill="tonexty",
                    fillcolor=f"rgba({rgb},{band_alpha})",
                    name=band_name,
                    legendgroup=f"compare-{state}",
                    showlegend=False,
                    customdata=np.column_stack([lower, upper]),
                    hovertemplate=(
                        f"<b>{state}</b><br>{band_detail}"
                        + f"<br>p05: %{{customdata[0]:{metric_spec.hover_format}}}"
                        f"<br>p95: %{{customdata[1]:{metric_spec.hover_format}}}"
                        "<extra></extra>"
                    ),
                )
            )

    onset_dots: list[tuple[str, str, str, int, float]] = []
    for index, state in enumerate(roster):
        color = COMPARE_STATE_COLORS[index]
        dash = COMPARE_STATE_DASHES[index]
        symbol = COMPARE_STATE_SYMBOLS[index]
        if state_scaled_scope:
            from atlas_io import state_scaled_state_slice  # local import, no cycle

            assert state_scaled is not None
            frame = state_scaled_state_slice(state_scaled, state)
            values = _state_scaled_compare_values(frame, metric)
        else:
            frame = policy_central_state_slice(pc, state, weather=weather)
            # _normalized_values already returns GWh-eq / kt for the bundle
            # scope, matching the band values divided by `scale` above.
            values = _normalized_values(frame, metric, "bundle")
        # A10 defect 11: the " (actual fleet)" suffix pushed every legend entry
        # past the (now retired) fixed slot and truncated the last one mid-word
        # ("Texas (actual fle"). The basis is stated once, in the chart title
        # and the basis footnote, so the legend carries the state name alone.
        line_label = str(names.get(state, state)) + (
            " (weather-adjusted)" if weather else ""
        )
        fig.add_trace(
            go.Scatter(
                x=frame["year"],
                y=values,
                mode="lines",
                line={
                    "color": color,
                    "width": 2.4,
                    # V2-11: per-slot dash so identity is not hue-only.  In
                    # the weather variant the dash is the MODE signal (every
                    # line is weather-adjusted), so it wins there.
                    "dash": "dashdot" if weather else dash,
                },
                name=line_label,
                legendgroup=f"compare-{state}",
                hovertemplate=(
                    f"<b>{line_label}</b><br>{metric_spec.short_label}: "
                    f"%{{y:{metric_spec.hover_format}}}"
                    f"<br>{_hover_unit_lines(hover_unit)}"
                    "<extra></extra>"
                ),
            )
        )
        # Turning-point dot, on THIS state's line and on THIS basis.  The two
        # deployment scales agree in every state but Oklahoma (2068 at its own
        # fleet size, 2067 on the equal-size comparison), so the dot is read
        # from the turning table that matches the basis being drawn rather
        # than from whichever one the bundle happens to key as default.
        # A state with no turning point gets NO dot: it is reported in words,
        # never drawn as a year.
        onset_raw = policy_central_turning_row(turning_source, state)[
            "sustained_nonincrease_onset_year"
        ]
        if pd.notna(onset_raw):
            onset = int(onset_raw)
            onset_value = float(values.loc[frame["year"] == onset].iloc[0])
            onset_dots.append((state, color, symbol, onset, onset_value))

    # CX-15: group exactly coincident dots (same year AND same plotted value
    # on converged lines) and spread each group across ±0.35 modeled years so
    # every dot stays visible.  Hover text always reports the true year.
    dot_groups: list[list[int]] = []
    for dot_index, (_, _, _, onset, value) in enumerate(onset_dots):
        for group in dot_groups:
            _, _, _, ref_onset, ref_value = onset_dots[group[0]]
            if onset == ref_onset and np.isclose(
                value, ref_value, rtol=1e-9, atol=1e-12
            ):
                group.append(dot_index)
                break
        else:
            dot_groups.append([dot_index])
    for group in dot_groups:
        offsets = (
            np.linspace(-COMPARE_ONSET_JITTER_YEARS, COMPARE_ONSET_JITTER_YEARS, len(group))
            if len(group) > 1
            else [0.0]
        )
        for offset, dot_index in zip(offsets, group):
            state, color, symbol, onset, onset_value = onset_dots[dot_index]
            jitter_note = (
                "<br><span style='color:#64625d'>Marker offset for visibility</span>"
                if len(group) > 1
                else ""
            )
            fig.add_trace(
                go.Scatter(
                    x=[onset + float(offset)],
                    y=[onset_value],
                    mode="markers",
                    marker={
                        "color": color,
                        "size": 9,
                        # V2-11: per-slot symbol, so the onset dot carries
                        # state identity without hue -- the channel that
                        # still works in the weather variant, where the dash
                        # is spent on the mode.
                        "symbol": symbol,
                        "line": {"color": "#fcfcfa", "width": 1.2},
                    },
                    showlegend=False,
                    legendgroup=f"compare-{state}",
                    hovertemplate=(
                        f"<b>{state}</b><br>Turning point: {onset}"
                        f"{jitter_note}<extra></extra>"
                    ),
                )
            )
    subtitle_lines = textwrap.wrap(
        central_label, width=40, break_long_words=False, break_on_hyphens=False
    )
    subtitle_lines.extend(
        ["CAV only · STI excluded", "actual FHWA MV-1 2024 fleet"]
        if state_scaled_scope
        else ["matched equal-size comparison"]
    )
    wrapped_subtitle = "<br>".join(subtitle_lines)
    layout = _layout(
        (
            f"{COMPARE_METRIC_TITLE_STEMS[metric]}<br>"
            f"<span style='font-size:11px'>{wrapped_subtitle}</span>"
        ),
        unit,
        height=height + 34,
    )
    # Multi-line title above a separate legend band. The explicit wraps keep
    # long scenario names and the actual-fleet qualifier inside 390 px.
    layout["margin"] = {"l": 60, "r": 24, "t": 118, "b": 82}
    layout["title"] = {
        **layout["title"],
        "y": 0.95,
        "yanchor": "top",
        "pad": {"b": 6},
    }
    layout["legend"] = {**layout["legend"], "y": 1.02, "yanchor": "bottom"}
    fig.update_layout(**layout)
    _basis_footnote(
        fig, "state_scaled" if state_scaled_scope else "bundle", pc.get("annual"),
        cav_only=state_scaled_scope,
    )
    fig.update_xaxes(range=[2024.5, 2076.5], tick0=2030, dtick=10)
    fig.update_layout(
        uirevision=(
            f"compare-{central_label}-{'-'.join(roster)}-{metric}-{draw_bands}-"
            f"{weather}-{deployment_scope}"
        )
    )
    reserve_legend_rows(fig)
    return fig


def make_case_triptych(
    bundle: Mapping[str, Any],
    state: str,
    band_object: str,
    emphasized_scenario: str,
    selected_year: int,
    *,
    horizon: int = 2050,
    compare_scenarios: bool = False,
    zoom_to_band: bool = False,
) -> go.Figure:
    """One synchronized CA/OH figure with one explicitly named range object.

    Every banded panel is annotated with its own maximum one-sided width
    ('band ±X.X%'); ``zoom_to_band`` fits each panel's y-range to the band
    in the decade ending at the inspected year (centre ± 1.5× each side) so
    narrow supports become inspectable where the cursor sits.
    """
    central = case_central(bundle, state).loc[lambda frame: frame["year"] <= horizon]
    fig = _triptych(height=735 if horizon <= 2050 else 790)
    if band_object != "none" and band_object not in BAND_OBJECTS:
        raise ValueError(f"Unknown case-study display object: {band_object}")
    scenario_roster = (
        ("low", "medium", "high")
        if compare_scenarios or band_object == "deterministic_scenario_span"
        else (emphasized_scenario,)
    )
    draw_band = band_object not in {"none", "deterministic_scenario_span"}
    band_label = BAND_OBJECTS[band_object].compact_label if band_object != "none" else None
    # CX-26: alphas 0.11-0.14 were nearly invisible; every band fill is
    # raised to a findable level and carries visible edge lines below.
    band_alpha_by_metric = {"energy": 0.16, "emissions": 0.16, "carbon_intensity": 0.16}
    if band_object == "conditioned_conversion_support":
        # Legibility: strengthen the deliberately narrow conditioned fill and
        # state its maximum one-sided width in the legend entry itself.
        band_alpha_by_metric = {key: 0.20 for key in band_alpha_by_metric}
        conditioned = pd.concat(
            [case_band(bundle, state, metric, band_object) for metric in PATHWAY_METRICS]
        )
        max_side = float(
            np.maximum(
                (conditioned["lower"] / conditioned["centre"] - 1.0).abs(),
                (conditioned["upper"] / conditioned["centre"] - 1.0).abs(),
            ).max()
        )
        band_label = f"{band_label} (≤{max_side * 100:.1f}%)"
    # In compare mode the y-range is fitted to the emphasized scenario and the
    # displayed band; distant comparator branches may clip. The compulsory
    # scenario-span object is exempt because the three lines are the object.
    fit_to_emphasized = compare_scenarios and band_object != "deterministic_scenario_span"

    for row_index, metric in enumerate(PATHWAY_METRICS, start=1):
        metric_spec = PATHWAY_METRICS[metric]
        pivot = central.pivot(
            index="year", columns="scenario_bundle", values=metric_spec.central_column
        ).sort_index()
        band = (
            case_band(bundle, state, metric, band_object).loc[
                lambda frame: frame["year"] <= horizon
            ]
            if draw_band
            else None
        )
        color = METRIC_COLORS[metric]

        if draw_band:
            assert band is not None
            _panel_band_annotation(
                fig,
                row_index,
                float(
                    np.maximum(
                        (band["lower"] / band["centre"] - 1.0).abs(),
                        (band["upper"] / band["centre"] - 1.0).abs(),
                    ).max()
                ),
            )
            case_edge_color = f"rgba({_BAND_RGB[metric]},{_BAND_EDGE_ALPHA})"
            fig.add_trace(
                go.Scatter(
                    x=band["year"],
                    y=band["lower"],
                    mode="lines",
                    line={"width": 0.9, "color": case_edge_color},
                    hoverinfo="skip",
                    showlegend=False,
                    legendgroup=f"band-{band_object}",
                ),
                row=row_index,
                col=1,
            )
            fillcolor = f"rgba({_BAND_RGB[metric]},{band_alpha_by_metric[metric]})"
            fig.add_trace(
                go.Scatter(
                    x=band["year"],
                    y=band["upper"],
                    mode="lines",
                    line={"width": 0.9, "color": case_edge_color},
                    fill="tonexty",
                    fillcolor=fillcolor,
                    name=band_label,
                    legendgroup=f"band-{band_object}",
                    showlegend=row_index == 1,
                    hoverinfo="skip",
                ),
                row=row_index,
                col=1,
            )

        for scenario in scenario_roster:
            emphasized = scenario == emphasized_scenario
            fig.add_trace(
                go.Scatter(
                    x=pivot.index,
                    y=pivot[scenario],
                    mode="lines",
                    line={
                        "color": color,
                        "width": 2.8 if emphasized else 1.1,
                        "dash": SCENARIO_DASHES[scenario],
                    },
                    opacity=1.0 if emphasized else 0.55,
                    name=f"{scenario.title()} deterministic",
                    legendgroup=f"scenario-{scenario}",
                    showlegend=row_index == 1,
                    hovertemplate=(
                        f"<b>{metric_spec.short_label}</b><br>{scenario.title()}: "
                        f"%{{y:{metric_spec.hover_format}}} {metric_spec.unit}"
                        "<extra></extra>"
                    ),
                ),
                row=row_index,
                col=1,
            )

        # Energy and emissions p50 are median-preserved to the Medium path.
        # Ratio quantiles are computed per paired draw and can legitimately
        # differ, so only that distinct centre is drawn.
        if draw_band and metric == "carbon_intensity" and band is not None and not np.allclose(
            band["centre"].to_numpy(),
            pivot[emphasized_scenario].to_numpy(),
            rtol=1e-4,
            atol=1e-9,
        ):
            fig.add_trace(
                go.Scatter(
                    x=band["year"],
                    y=band["centre"],
                    mode="lines",
                    line={"color": INK, "width": 1.0, "dash": "dot"},
                    name="Paired-draw p50 intensity · legacy audit series",
                    legendgroup="ratio-p50",
                    showlegend=True,
                    hovertemplate=(
                        "<b>Paired-draw p50 intensity</b>"
                        "<br>Legacy audit: %{y:.3f}"
                        "<extra></extra>"
                    ),
                ),
                row=row_index,
                col=1,
            )

        fig.update_yaxes(
            **_axis(CASE_TRIPTYCH_AXIS_TITLES[metric]),
            row=row_index,
            col=1,
        )
        if fit_to_emphasized:
            fit_values = [pivot[emphasized_scenario]]
            if draw_band and band is not None:
                fit_values.extend([band["lower"], band["centre"], band["upper"]])
            fit_low = float(min(series.min() for series in fit_values))
            fit_high = float(max(series.max() for series in fit_values))
            pad = (fit_high - fit_low) * 0.06
            if pad <= 0:
                pad = max(abs(fit_high), 1.0) * 0.05
            fig.update_yaxes(
                range=[fit_low - pad, fit_high + pad], row=row_index, col=1
            )
        # Zoom-to-band wins over the compare fit: an explicit request to
        # inspect the narrow band; comparator branches may clip.
        if zoom_to_band and draw_band and band is not None:
            fig.update_yaxes(
                range=_zoom_range(
                    band["centre"], band["lower"], band["upper"],
                    band["year"], int(selected_year),
                ),
                row=row_index,
                col=1,
            )

    zero_rows = central.loc[
        central["scenario_bundle"].isin(scenario_roster)
        & (central["total_scope_matched_direct_co2_kt"] <= 1e-12)
        & (central["total_carrier_input_twh_eq"] > 0)
    ]
    if not zero_rows.empty:
        first_zero_year = int(zero_rows["year"].min())
        # CX-25: whenever the zero-year sits in the right half of the
        # horizon, the label is flipped to the left of the arrow so its
        # ~230px of text can never run past the right plot edge (the old
        # `horizon - 8` rule under-covered narrow renders).
        x_fraction = (first_zero_year - 2025) / max(int(horizon) - 2025, 1)
        near_right_edge = x_fraction > 0.5
        fig.add_annotation(
            x=first_zero_year,
            y=0,
            row=2,
            col=1,
            text="zero direct boundary ≠ lifecycle net zero",
            showarrow=True,
            arrowhead=0,
            ax=-64 if near_right_edge else 64,
            ay=-34,
            xanchor="right" if near_right_edge else "left",
            font={"family": PLOT_SANS, "size": 10, "color": MUTED},
            bgcolor="rgba(252,252,250,0.92)",
            bordercolor=HAIRLINE,
            borderwidth=1,
        )

    if 2025 <= selected_year <= horizon:
        fig.add_vline(
            x=selected_year,
            line={"color": "#c96a3b", "width": 1.0, "dash": "dot"},
            row="all",
            col=1,
        )
    fig.update_xaxes(range=[2025, horizon], tick0=2030, dtick=10, showgrid=False)
    fig.update_xaxes(title_text="Modeled year", row=3, col=1)
    _basis_footnote(fig, "case")
    fig.update_layout(
        uirevision=f"case-triptych-{state}-{band_object}-{horizon}-{zoom_to_band}"
    )
    reserve_legend_rows(fig)
    return fig


def make_normalized_pathway(data: Mapping[str, Any], state: str, metric: str,
                            scope: str, emphasized_scenario: str,
                            selected_year: int) -> go.Figure:
    """Deprecated single-metric deterministic comparator; never draws a ribbon."""
    metric_spec = PATHWAY_METRICS[metric]
    source = state_slice(data, state).copy()
    source["plot_value"] = _normalized_values(source, metric, scope)
    pivot = source.pivot(index="year", columns="scenario_bundle", values="plot_value").sort_index()
    color = METRIC_COLORS[metric]
    fig = go.Figure()
    for scenario in ("low", "medium", "high"):
        emphasized = scenario == emphasized_scenario
        fig.add_trace(
            go.Scatter(
                x=pivot.index,
                y=pivot[scenario],
                mode="lines",
                line={
                    "color": color,
                    "width": 2.8 if emphasized else 1.25,
                    "dash": SCENARIO_DASHES[scenario],
                },
                opacity=1.0 if emphasized else SCENARIO_OPACITY[scenario],
                name=f"{scenario.title()} deterministic",
                hovertemplate=(
                    f"<b>{scenario.title()}</b><br>"
                    f"%{{y:{metric_spec.hover_format}}}"
                    f"<br>{_hover_unit_lines(normalized_metric_unit(metric, scope))}"
                    "<extra></extra>"
                ),
            )
        )

    # Same estimand, explicitly labeled 50-state-only median; DC remains a
    # supplemental jurisdiction: in the 51-jurisdiction display, excluded from
    # this state-only statistic.
    annual = data["annual"].loc[
        (data["annual"]["scope_role"] == PRIMARY_SCOPE)
        & (data["annual"]["scenario_bundle"] == emphasized_scenario)
    ].copy()
    annual["plot_value"] = _normalized_values(annual, metric, scope)
    median = annual.groupby("year", as_index=False)["plot_value"].median()
    fig.add_trace(
        go.Scatter(
            x=median["year"],
            y=median["plot_value"],
            mode="lines",
            line={"color": "#85827c", "width": 1.0, "dash": "longdash"},
            name=f"50-state-only median · {emphasized_scenario}",
            hovertemplate="50-state-only median: %{y:.3f}<extra></extra>",
        )
    )
    fig.add_vline(x=selected_year, line={"color": "#c96a3b", "width": 1.0, "dash": "dot"})
    fig.update_layout(
        **_layout(metric_spec.label, normalized_metric_unit(metric, scope)),
        uirevision=f"normalized-{state}-{metric}-{scope}",
    )
    return fig


def make_case_pathway(bundle: Mapping[str, Any], state: str, metric: str,
                      band_object: str, emphasized_scenario: str,
                      selected_year: int) -> go.Figure:
    """Deprecated single-metric CA/OH view with one explicitly named object."""
    metric_spec = PATHWAY_METRICS[metric]
    central = case_central(bundle, state)
    pivot = central.pivot(
        index="year", columns="scenario_bundle", values=metric_spec.central_column
    ).sort_index()
    band = case_band(bundle, state, metric, band_object)
    color = METRIC_COLORS[metric]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=band["year"],
            y=band["lower"],
            mode="lines",
            line={"width": 0, "color": "rgba(0,0,0,0)"},
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=band["year"],
            y=band["upper"],
            mode="lines",
            line={"width": 0, "color": "rgba(0,0,0,0)"},
            fill="tonexty",
            fillcolor=(
                "rgba(166,70,61,0.12)" if metric == "emissions" else
                "rgba(79,89,101,0.11)" if metric == "energy" else
                "rgba(39,97,140,0.11)"
            ),
            name=BAND_OBJECTS[band_object].compact_label,
            hoverinfo="skip",
        )
    )
    for scenario in ("low", "medium", "high"):
        emphasized = scenario == emphasized_scenario
        fig.add_trace(
            go.Scatter(
                x=pivot.index,
                y=pivot[scenario],
                mode="lines",
                line={
                    "color": color,
                    "width": 2.8 if emphasized else 1.15,
                    "dash": SCENARIO_DASHES[scenario],
                },
                opacity=1.0 if emphasized else SCENARIO_OPACITY[scenario],
                name=f"{scenario.title()} deterministic",
                hovertemplate=(
                    f"<b>{scenario.title()}</b><br>"
                    f"%{{y:{metric_spec.hover_format}}} {metric_spec.unit}"
                    "<extra></extra>"
                ),
            )
        )
    if band_object not in {"deterministic_scenario_span"}:
        centre_name = (
            "Paired-draw p50 intensity · legacy audit"
            if metric == "carbon_intensity"
            and BAND_OBJECTS[band_object].legacy_monte_carlo
            else "Legacy ensemble p50 · audit only"
            if BAND_OBJECTS[band_object].legacy_monte_carlo
            else "Registered Medium reference"
        )
        fig.add_trace(
            go.Scatter(
                x=band["year"],
                y=band["centre"],
                mode="lines",
                line={"color": INK, "width": 1.0, "dash": "dot"},
                name=centre_name,
                hovertemplate="Band centre: %{y:.3f}<extra></extra>",
            )
        )
    fig.add_vline(x=selected_year, line={"color": "#c96a3b", "width": 1.0, "dash": "dot"})
    fig.update_layout(
        **_layout(metric_spec.label, metric_spec.unit),
        uirevision=f"case-{state}-{metric}-{band_object}",
    )
    return fig


def make_uncertainty_widths(bundle: Mapping[str, Any], state: str, year: int) -> go.Figure:
    """Show each p05/p95 side relative to p50, not their misleading sum."""
    layers = ["l1_state_condition", "l2_load_model", "l3_trajectory"]
    labels = {
        "l1_state_condition": "L1 · state",
        "l2_load_model": "L2 · load",
        "l3_trajectory": "L3 · trajectory",
    }
    metric_labels = {
        "energy": "Energy",
        "emissions": "CO₂",
        "carbon_intensity": "Intensity",
    }
    metric_symbols = {
        "energy": "circle",
        "emissions": "square",
        "carbon_intensity": "triangle-up",
    }
    metric_dashes = {
        "energy": "solid",
        "emissions": "dash",
        "carbon_intensity": "dot",
    }
    fig = go.Figure()
    for metric in PATHWAY_METRICS:
        x_values: list[float | None] = []
        y_values: list[str | None] = []
        endpoint_labels: list[str | None] = []
        for layer in layers:
            row = case_band(bundle, state, metric, layer)
            row = row.loc[row["year"] == year].iloc[0]
            centre = float(row["centre"])
            lower = (float(row["lower"]) / centre - 1.0) * 100.0
            upper = (float(row["upper"]) / centre - 1.0) * 100.0
            category = f"{labels[layer]} · {metric_labels[metric]}"
            x_values.extend([lower, upper, None])
            y_values.extend([category, category, None])
            endpoint_labels.extend(["p05", "p95", None])
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines+markers",
                name=metric_labels[metric],
                line={"color": "#333333", "width": 1.8, "dash": metric_dashes[metric]},
                marker={
                    "color": "#333333",
                    "size": 7,
                    "symbol": metric_symbols[metric],
                },
                customdata=endpoint_labels,
                hovertemplate=(
                    "%{y}<br>%{customdata}: %{x:+.1f}% relative to p50<extra></extra>"
                ),
            )
        )
    fig.add_vline(x=0, line={"color": INK, "width": 1.0})
    for guard in (-50, 50):
        fig.add_vline(
            x=guard,
            line={"color": "#8a8882", "width": 0.9, "dash": "dot"},
        )
    fig.add_annotation(
        x=0.5,
        y=-0.17,
        xref="paper",
        yref="paper",
        text="Gray ±50% guides = display review<br>not a validity threshold",
        showarrow=False,
        xanchor="center",
        yanchor="top",
        font={"family": PLOT_SANS, "size": 11, "color": MUTED},
    )
    layout = _layout(
        "",
        "Deviation from p50 (%)",
        height=455,
    )
    layout.update(
        {
            "xaxis": _axis("p05 / p95 deviation from p50 (%)"),
            "yaxis": {
                **_axis(""),
                "showgrid": False,
                "categoryorder": "array",
                "categoryarray": [
                    f"{labels[layer]} · {metric_labels[metric]}"
                    for layer in reversed(layers)
                    for metric in PATHWAY_METRICS
                ],
                "tickfont": {"size": 11, "color": MUTED},
            },
            "hovermode": "closest",
            "legend": {
                "orientation": "h",
                "x": 0,
                "xanchor": "left",
                "y": 1.035,
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
            "margin": {"l": 146, "r": 18, "t": 48, "b": 104},
        }
    )
    fig.update_layout(**layout)
    return fig


def make_case_decomposition(bundle: Mapping[str, Any], state: str,
                            scenario: str, year: int) -> go.Figure:
    """Selected-year carrier and CO2 source composition using separate axes."""
    central = case_central(bundle, state)
    row = central.loc[
        (central["scenario_bundle"] == scenario) & (central["year"] == year)
    ].iloc[0]
    energy = {
        "E-CAV wall electricity": float(row["ecav_wall_electricity_twh"]),
        "STI site electricity": float(row["sti_site_electricity_twh"]),
        "ICE-CAV gasoline input": float(row["icecav_gasoline_input_twh_eq"]),
    }
    emissions = {
        "Low-carbon electricity": float(row["low_carbon_direct_co2_kt"]),
        "Fossil electricity": float(row["fossil_electricity_direct_co2_kt"]),
        "Gasoline tailpipe": float(row["gasoline_tailpipe_direct_co2_kt"]),
    }
    fig = go.Figure()
    for label, value in energy.items():
        fig.add_trace(
            go.Bar(
                y=["Energy consumption"],
                x=[value],
                orientation="h",
                name=label,
                hovertemplate=f"{label}: %{{x:.3f}} TWh-eq<extra></extra>",
            )
        )
    # Emissions are normalized to their own row total so unlike physical units
    # are never placed on a shared numeric axis.
    total_emissions = sum(emissions.values())
    for label, value in emissions.items():
        fig.add_trace(
            go.Bar(
                y=["Direct CO₂ composition"],
                x=[value / total_emissions * 100 if total_emissions else 0],
                orientation="h",
                name=label,
                visible="legendonly",
                hovertemplate=f"{label}: {value:.2f} kt CO₂<extra></extra>",
            )
        )
    layout = _layout("Selected-year energy and CO₂ composition", "", height=300)
    layout.update(
        {
            "barmode": "stack",
            "xaxis": _axis("TWh-eq yr⁻¹ for the visible energy-consumption row"),
            "yaxis": {**_axis(""), "showgrid": False},
            "hovermode": "closest",
        }
    )
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# State-scaled view (owner fix 2026-09-02): CAV panels at each state's ACTUAL
# FHWA MV-1 2024 fleet (official statistic) with the DISPLAYED v4
# ceiling-prior conditional band transported at unchanged relative width
# (linear scaling preserves relative widths; the retired v3 columns stay
# packaged as audit only), and an STI panel shaded across the modeled
# low/central/high site counts (MODELED_SITE_ESTIMATE_NOT_A_CENSUS).
# ---------------------------------------------------------------------------

# V2-09: the state-scaled panel names are published by metric_names, the same
# module that publishes the reference triple, so the page heading and the
# panel titles can never drift apart again.  The letters are the standard
# a/b/c; the NAMES are deliberately different because the quantities are.
STATE_SCALED_PANEL_TITLES = tuple(
    f"{letter} · {name}"
    for letter, name in zip(PANEL_LETTERS.values(), STATE_SCALED_PANEL_NAMES)
)


def make_state_scaled_triptych(
    ss: Mapping[str, Any],
    state: str,
    selected_year: int,
    *,
    horizon: int = 2050,
) -> go.Figure:
    """Per-state pathway triptych at data-based capacities.

    Panels a/b scale the CAV pathway by the state's actual registered-
    vehicle total; their shading is the DISPLAYED 5th-95th percentile interval
    (ceiling prior inside) transported at unchanged RELATIVE width (every
    draw is linear in capacity, so a constant capacity factor multiplies
    draws and central alike; the retired envelope stays packaged as audit
    columns).  Width annotations quote one same-year basis at both ends of
    the displayed horizon plus the drawn absolute width ratio.  Panel c
    shades the STI electricity pathway across the modeled low/central/high
    intersection counts — an estimator range, not a probability band and not a census.
    """
    from atlas_io import state_scaled_state_slice  # local import, no cycle

    full_frame = state_scaled_state_slice(ss, state)
    frame = full_frame.loc[lambda f: f["year"] <= horizon]

    def _horizon_width_annotation(central_col: str, lo_col: str, hi_col: str,
                                  rel_col: str) -> str:
        """Near- and far-horizon width on ONE basis (owner requirement A5).

        The retired two-basis text switched to a peak-year denominator past
        the scoped window and therefore printed a SMALLER number for the
        farther year, which read as "more certain further out".  Both ends of
        the displayed horizon are now quoted on the same-year central basis,
        with the drawn absolute width ratio alongside.
        """
        del central_col  # the peak-year denominator is retired from display
        anchor = min(int(BAND_HORIZON_ANCHOR_YEAR), int(horizon))
        start = full_frame.loc[full_frame["year"] == anchor].iloc[0]
        end = full_frame.loc[full_frame["year"] == int(horizon)].iloc[0]
        abs_start = float(start[hi_col]) - float(start[lo_col])
        abs_end = float(end[hi_col]) - float(end[lo_col])
        ratio = abs_end / abs_start if abs_start > 0 else float("nan")
        ratio_text = (
            f"absolute ×{ratio:.1f}" if np.isfinite(ratio)
            else "absolute width zero at the start"
        )
        return (
            f"one-sided {relative_pct_text(start[rel_col])}→"
            f"{relative_pct_text(end[rel_col])} of central "
            f"({anchor}→{int(horizon)}) · {ratio_text}"
        )
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.065,
        subplot_titles=list(STATE_SCALED_PANEL_TITLES),
    )
    for annotation in fig.layout.annotations:
        annotation.update(
            x=0,
            xanchor="left",
            font={"family": PLOT_SANS, "size": 13, "color": INK},
        )
    fig.update_layout(
        height=790,
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        font={"family": PLOT_SANS, "size": 11, "color": INK},
        # b=88 leaves room for the one-line normalization-basis footnote
        # that replaced the denominator repeated inside all three rotated
        # axis titles (A10 defects 1-3).
        # V2-08: t is the one-row allowance; reserve_legend_rows() at the end
        # of this builder grows it to the rows this legend really needs --
        # four state-scaled names total ~779 px, one row at the 1440 px
        # capture and four at mobile widths.
        margin={"l": 72, "r": 14, "t": TRIPTYCH_BASE_TOP_MARGIN_PX, "b": 88},
        legend={
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": 1.065,
            "yanchor": "bottom",
            # X6 / A10 defects 8-11: entrywidth 0 means "size each entry to
            # its own characters". It must be stated EXPLICITLY: the host
            # injects entrywidthmode="pixels" into the Plotly layout, so
            # with no entrywidth the entries were laid out on slots
            # narrower than their text -- each name over-printed by the
            # next swatch, the last one cut mid-word.
            "entrywidth": 0,
            # X6: see _triptych — no fixed entry slot.
            "font": {"size": 11},
            "bgcolor": "rgba(0,0,0,0)",
        },
        hoverlabel=HOVER_LABEL_STYLE,
        hovermode="x unified",
        hoversubplots="axis",
    )

    cav_panels = (
        (
            1,
            "energy",
            frame["cav_carrier_input_kwh_eq_actual_fleet"] / 1e6,
            frame["cav_carrier_input_kwh_eq_actual_fleet_p05_v33"] / 1e6,
            frame["cav_carrier_input_kwh_eq_actual_fleet_p95_v33"] / 1e6,
            _horizon_width_annotation(
                "cav_carrier_input_kwh_eq_actual_fleet",
                "cav_carrier_input_kwh_eq_actual_fleet_p05_v33",
                "cav_carrier_input_kwh_eq_actual_fleet_p95_v33",
                "band_v33_rel_halfwidth_max_energy",
            ),
            "CAV energy consumption · actual fleet",
            "GWh-eq yr⁻¹",
            "GWh-eq yr⁻¹",
        ),
        (
            2,
            "emissions",
            frame["cav_direct_co2_kg_actual_fleet"] / 1e6,
            frame["cav_direct_co2_kg_actual_fleet_p05_v33"] / 1e6,
            frame["cav_direct_co2_kg_actual_fleet_p95_v33"] / 1e6,
            _horizon_width_annotation(
                "cav_direct_co2_kg_actual_fleet",
                "cav_direct_co2_kg_actual_fleet_p05_v33",
                "cav_direct_co2_kg_actual_fleet_p95_v33",
                "band_v33_rel_halfwidth_max_co2",
            ),
            "CAV direct CO₂ emissions · actual fleet",
            "kt CO₂ yr⁻¹",
            "kt CO₂ yr⁻¹",
        ),
    )
    for row_index, metric, central, lower, upper, annotation, name, unit, axis_title in cav_panels:
        rgb = _BAND_RGB[metric]
        _panel_band_annotation(fig, row_index, text=annotation)
        fig.add_trace(
            go.Scatter(
                x=frame["year"], y=lower, mode="lines",
                line={"width": 0.9, "color": f"rgba({rgb},{_BAND_EDGE_ALPHA})"},
                hoverinfo="skip", showlegend=False, legendgroup="ss-band",
            ),
            row=row_index, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=frame["year"], y=upper, mode="lines",
                line={"width": 0.9, "color": f"rgba({rgb},{_BAND_EDGE_ALPHA})"},
                fill="tonexty", fillcolor=f"rgba({rgb},{_BAND_FILL_ALPHA})",
                name="5th-95th percentile interval",
                legendgroup="ss-band", showlegend=row_index == 1,
                customdata=np.column_stack([lower, upper]),
                hovertemplate=(
                    f"<b>{name.replace(' · ', '<br>')}</b>"
                    "<br>5th–95th percentile interval"
                    "<br>p05: %{customdata[0]:,.1f}"
                    "<br>p95: %{customdata[1]:,.1f}<extra></extra>"
                ),
            ),
            row=row_index, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=frame["year"], y=central, mode="lines",
                line={"color": METRIC_COLORS[metric], "width": 2.8},
                name="State-scaled central",
                legendgroup="ss-central", showlegend=row_index == 1,
                hovertemplate=(
                    f"<b>{name.replace(' · ', '<br>')}</b>"
                    f"<br>%{{y:,.1f}} {unit}<extra></extra>"
                ),
            ),
            row=row_index, col=1,
        )
        fig.update_yaxes(**_axis(axis_title), row=row_index, col=1)

    sti_rgb = _BAND_RGB["carbon_intensity"]
    sti_low = frame["sti_electricity_kwh_sites_low"] / 1e6
    sti_central = frame["sti_electricity_kwh_sites_central"] / 1e6
    sti_high = frame["sti_electricity_kwh_sites_high"] / 1e6
    fig.add_trace(
        go.Scatter(
            x=frame["year"], y=sti_low, mode="lines",
            line={"width": 0.9, "color": f"rgba({sti_rgb},{_BAND_EDGE_ALPHA})"},
            hoverinfo="skip", showlegend=False, legendgroup="ss-sti-range",
        ),
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=frame["year"], y=sti_high, mode="lines",
            line={"width": 0.9, "color": f"rgba({sti_rgb},{_BAND_EDGE_ALPHA})"},
            fill="tonexty", fillcolor=f"rgba({sti_rgb},{_BAND_FILL_ALPHA})",
            name="Site-count range (low–high)",
            legendgroup="ss-sti-range", showlegend=True,
            customdata=np.column_stack([sti_low, sti_high]),
            hovertemplate=(
                "<b>STI electricity</b><br>Site-count range"
                "<br>Low: %{customdata[0]:,.2f}"
                "<br>High: %{customdata[1]:,.2f}<extra></extra>"
            ),
        ),
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=frame["year"], y=sti_central, mode="lines",
            line={"color": METRIC_COLORS["carbon_intensity"], "width": 2.8},
            name="STI central",
            legendgroup="ss-sti-central", showlegend=True,
            hovertemplate=(
                "<b>STI electricity</b><br>Modeled central"
                "<br>%{y:,.2f} GWh yr⁻¹<extra></extra>"
            ),
        ),
        row=3, col=1,
    )
    fig.update_yaxes(**_axis("GWh yr⁻¹"), row=3, col=1)
    _basis_footnote(fig, "state_scaled")

    if 2025 <= selected_year <= horizon:
        fig.add_vline(
            x=selected_year,
            line={"color": "#c96a3b", "width": 1.0, "dash": "dot"},
            row="all", col=1,
        )
    fig.update_xaxes(range=[2025, horizon], tick0=2030, dtick=10, showgrid=False)
    fig.update_xaxes(title_text="Modeled year", row=3, col=1)
    fig.update_layout(
        uirevision=f"state-scaled-triptych-{state}-{horizon}"
    )
    reserve_legend_rows(fig)
    return fig
