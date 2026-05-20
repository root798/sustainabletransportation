"""Metric × Uncertainty-object dispatch for the Scenario Explorer.

Replaces the ad-hoc branching that left "Both (dual axis)" rendering
only one axis under the Scenario-envelope object, and left cumulative
metrics re-using the annual band without re-integrating.

Every metric/uncertainty cell goes through ``build_traces`` (single-axis)
or ``build_dual_axis`` (Both view), both backed by the same ``BandSource``
contract from ``bands.py``. There is no early return for one uncertainty
object that does not exist for the other.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .bands import (
    BandSource, MetricId, ScenarioSettings, TrajectorySet,
    EMISSIONS_COL, ENERGY_COL,
    cumulative_trajectory_set,
)


# =====================================================================
# Trace dataclasses (renderer-agnostic so tests can assert without Plotly)
# =====================================================================
@dataclass(frozen=True)
class Trace:
    """One drawable series. The page module converts these into Plotly
    Bar/Scatter/Heatmap traces; tests can inspect them without importing
    plotly."""
    kind: str                                # "band" | "line" | "deterministic"
    name: str
    metric: str
    axis: str = "y"                          # "y" | "y2"
    x: Optional[np.ndarray] = None
    y: Optional[np.ndarray] = None
    y_lower: Optional[np.ndarray] = None
    y_upper: Optional[np.ndarray] = None
    color: Optional[str] = None
    is_dashed: bool = False
    metadata: Tuple[Tuple[str, Any], ...] = ()


# =====================================================================
# Metric → metric-column resolver
# =====================================================================
_METRIC_TO_COLUMN: Dict[str, str] = {
    "annual_co2":       EMISSIONS_COL,
    "annual_energy":    ENERGY_COL,
    "cumulative_co2":   EMISSIONS_COL,
    "cumulative_energy": ENERGY_COL,
}

_IS_CUMULATIVE: Dict[str, bool] = {
    "annual_co2":       False,
    "annual_energy":    False,
    "cumulative_co2":   True,
    "cumulative_energy": True,
    "both":             False,
}


def trajectory_set_for_metric(band: BandSource, metric_id: str
                               ) -> Optional[TrajectorySet]:
    """Pull the right ``TrajectorySet`` from a ``BandSource`` for a
    given metric ID. Cumulative metrics get the per-run cumulative
    transform applied before returning, so the resulting p05/p50/p95
    widen monotonically with year."""
    col = _METRIC_TO_COLUMN.get(metric_id)
    if col is None:
        return None
    ts = band.for_metric(col)
    if ts is None:
        return None
    if _IS_CUMULATIVE.get(metric_id, False):
        return cumulative_trajectory_set(ts)
    return ts


# =====================================================================
# build_traces — single-axis dispatch (covers 4 of 5 metrics)
# =====================================================================
def build_traces(
    band: BandSource,
    deterministic: Optional[Dict[str, np.ndarray]] = None,
    *,
    settings: ScenarioSettings,
    primary_color: str = "#0F4C81",
    secondary_color: str = "#C44E52",
    accent_color: str = "#595959",
) -> List[Trace]:
    """Return the list of traces for any single-axis metric.

    The dispatch covers every cell:
        "annual_co2", "annual_energy",
        "cumulative_co2", "cumulative_energy"
    and is identical for both ``settings.uncertainty_object`` values —
    the only thing that changes is the ``BandSource`` passed in.

    "both" routes through ``build_dual_axis`` instead.
    """
    if settings.metric == "both":
        raise ValueError(
            "build_traces does not handle the 'both' metric; call "
            "build_dual_axis instead."
        )

    ts = trajectory_set_for_metric(band, settings.metric)
    if ts is None:
        return []

    col = _METRIC_TO_COLUMN[settings.metric]
    is_energy = (col == ENERGY_COL)
    band_color = primary_color if is_energy else secondary_color
    is_cum = _IS_CUMULATIVE[settings.metric]
    band_label = ("Cumulative residual band" if is_cum
                   and settings.uncertainty_object == "Residual"
                   else "Cumulative scenario envelope" if is_cum
                   else f"{settings.uncertainty_object} band")

    traces: List[Trace] = [
        Trace(
            kind="band",
            name=band_label,
            metric=col,
            axis="y",
            x=ts.years,
            y_lower=ts.p05,
            y_upper=ts.p95,
            color=band_color,
            metadata=(
                ("metric_id", settings.metric),
                ("uncertainty_object", settings.uncertainty_object),
                ("n_runs", band.n_runs),
                ("is_cumulative", is_cum),
            ),
        ),
        Trace(
            kind="line",
            name="Median (p50)",
            metric=col,
            axis="y",
            x=ts.years,
            y=ts.p50,
            color=band_color,
            metadata=(("series", "median"),),
        ),
    ]
    if deterministic is not None and col in deterministic:
        det_y = np.asarray(deterministic[col], dtype=float)
        if is_cum:
            det_y = np.cumsum(det_y)
        traces.append(Trace(
            kind="deterministic",
            name="Deterministic",
            metric=col,
            axis="y",
            x=ts.years,
            y=det_y,
            color=accent_color,
            is_dashed=True,
        ))
    return traces


# =====================================================================
# build_dual_axis — Both (dual axis), works for either uncertainty object
# =====================================================================
def build_dual_axis(
    band: BandSource,
    deterministic: Optional[Dict[str, np.ndarray]] = None,
    *,
    settings: ScenarioSettings,
    primary_color: str = "#0F4C81",
    secondary_color: str = "#C44E52",
    accent_color: str = "#595959",
) -> List[Trace]:
    """Return traces for the "Both (dual axis)" view.

    Builds a band on each y-axis independently:
      y  (left)  — CO₂ emissions  (red band, red median, accent dashed line)
      y2 (right) — energy demand  (blue band, blue median, accent dashed line)

    Critically, this branch *does not return early* under the Scenario
    envelope object — the band source on each axis is just whichever
    BandSource the caller passed in. The user reported that the dual
    axis silently dropped to a single axis under the Scenario envelope;
    that behaviour is now impossible because the rendering contract is
    identical for both uncertainty objects.
    """
    if settings.metric != "both":
        raise ValueError(
            f"build_dual_axis expects settings.metric == 'both', got "
            f"{settings.metric!r}."
        )

    out: List[Trace] = []

    # CO₂ on y-axis 1
    co2_ts = band.for_metric(EMISSIONS_COL)
    if co2_ts is not None:
        out.append(Trace(
            kind="band",
            name=f"{settings.uncertainty_object} band · CO₂",
            metric=EMISSIONS_COL, axis="y",
            x=co2_ts.years, y_lower=co2_ts.p05, y_upper=co2_ts.p95,
            color=secondary_color,
            metadata=(("metric_id", "annual_co2"), ("axis", "y"),
                      ("uncertainty_object", settings.uncertainty_object),
                      ("n_runs", band.n_runs)),
        ))
        out.append(Trace(
            kind="line",
            name="Median emissions",
            metric=EMISSIONS_COL, axis="y",
            x=co2_ts.years, y=co2_ts.p50, color=secondary_color,
        ))
        if deterministic is not None and EMISSIONS_COL in deterministic:
            out.append(Trace(
                kind="deterministic",
                name="Deterministic emissions",
                metric=EMISSIONS_COL, axis="y",
                x=co2_ts.years,
                y=np.asarray(deterministic[EMISSIONS_COL], dtype=float),
                color=accent_color, is_dashed=True,
            ))

    # Energy on y-axis 2
    e_ts = band.for_metric(ENERGY_COL)
    if e_ts is not None:
        out.append(Trace(
            kind="band",
            name=f"{settings.uncertainty_object} band · energy",
            metric=ENERGY_COL, axis="y2",
            x=e_ts.years, y_lower=e_ts.p05, y_upper=e_ts.p95,
            color=primary_color,
            metadata=(("metric_id", "annual_energy"), ("axis", "y2"),
                      ("uncertainty_object", settings.uncertainty_object),
                      ("n_runs", band.n_runs)),
        ))
        out.append(Trace(
            kind="line",
            name="Median energy",
            metric=ENERGY_COL, axis="y2",
            x=e_ts.years, y=e_ts.p50, color=primary_color,
        ))
        if deterministic is not None and ENERGY_COL in deterministic:
            out.append(Trace(
                kind="deterministic",
                name="Deterministic energy",
                metric=ENERGY_COL, axis="y2",
                x=e_ts.years,
                y=np.asarray(deterministic[ENERGY_COL], dtype=float),
                color=accent_color, is_dashed=True,
            ))

    return out


# =====================================================================
# Apply trace list to a Plotly figure
# =====================================================================
def render_to_plotly(traces: List[Trace], fig=None, *,
                      band_opacity: float = 0.16):
    """Convert a list of ``Trace`` objects into Plotly Scatter traces on
    ``fig``. Bands are rendered as fill-to-prev with low opacity; lines
    are solid; deterministic traces are dashed.
    """
    import plotly.graph_objects as go  # local import keeps tests light
    if fig is None:
        fig = go.Figure()
    # Render bands first (so lines draw on top).
    for tr in traces:
        if tr.kind != "band":
            continue
        # Upper bound, then lower bound with fill="tonexty".
        fig.add_trace(go.Scatter(
            x=list(map(int, tr.x)), y=list(map(float, tr.y_upper)),
            mode="lines",
            line=dict(color=tr.color or "#888", width=0.4),
            name=tr.name, showlegend=False, yaxis=tr.axis,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=list(map(int, tr.x)), y=list(map(float, tr.y_lower)),
            mode="lines",
            line=dict(color=tr.color or "#888", width=0.4),
            name=tr.name, showlegend=True, yaxis=tr.axis,
            fill="tonexty",
            fillcolor=_rgba(tr.color or "#888", band_opacity),
            hoverinfo="skip",
        ))
    for tr in traces:
        if tr.kind == "line":
            fig.add_trace(go.Scatter(
                x=list(map(int, tr.x)), y=list(map(float, tr.y)),
                mode="lines",
                line=dict(color=tr.color or "#333", width=1.6),
                name=tr.name, yaxis=tr.axis,
            ))
        elif tr.kind == "deterministic":
            fig.add_trace(go.Scatter(
                x=list(map(int, tr.x)), y=list(map(float, tr.y)),
                mode="lines",
                line=dict(color=tr.color or "#222", width=1.6, dash="dash"),
                name=tr.name, yaxis=tr.axis,
            ))
    return fig


def _rgba(color: str, alpha: float) -> str:
    """Turn a hex like ``"#0F4C81"`` into an rgba() string for the band fill."""
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    try:
        r = int(c[0:2], 16); g = int(c[2:4], 16); b = int(c[4:6], 16)
    except ValueError:
        r, g, b = 153, 153, 153
    return f"rgba({r},{g},{b},{alpha:.3f})"
