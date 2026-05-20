"""Monte Carlo + scenario-envelope band plumbing for the Scenario Explorer.

Why this exists
---------------
v11's Scenario Explorer page (``pages/03_Scenario_Explorer.py``) cached the
Monte Carlo run with ``@st.cache_data`` but every cache-key argument was
underscore-prefixed (``_sig``, ``_live_cfg``, ``_n_samples``, ``_region``).
Streamlit treats leading-underscore args as **unhashable** and excludes
them from the cache key, so the cache effectively collapsed to one entry
per process. Every slider change (CAV target, STI coverage, BEV growth,
clean-electricity growth, hardware-efficiency doubling time, hardware-
deployment lag) updated the deterministic line but reused the stale band.

Separately, the cumulative metric path read pre-computed quantile CSVs and
never re-percentile-d after ``cumsum``, so cumulative bands appeared
implausibly narrow at 2074. The correct path integrates each Monte Carlo
trajectory first, then takes p05 / p50 / p95 across the integrated curves.

This module is the canonical plumbing: a frozen ``ScenarioSettings``
record, a single ``settings_hash`` cache key, and a ``BandSource``
contract that delivers both percentiles and raw trajectories so any
metric (annual / cumulative / dual-axis) can re-percentile cleanly.

The Monte Carlo physics and the seed defaults are unchanged; this module
adds plumbing only.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Dict, Literal, Optional

import numpy as np
import pandas as pd


# Public metric IDs. These map to the radio labels used in the page module.
MetricId = Literal[
    "annual_co2", "annual_energy", "both",
    "cumulative_co2", "cumulative_energy",
]
UncertaintyObject = Literal["Residual", "Scenario envelope"]


# The two underlying numeric metrics in the Monte Carlo output frame.
EMISSIONS_COL = "ATS Emissions (kg CO2)"
ENERGY_COL    = "ATS Total Power (kWh)"


# =====================================================================
# ScenarioSettings — single source of truth for cache invalidation
# =====================================================================
@dataclass(frozen=True)
class ScenarioSettings:
    """Everything the Scenario Explorer band depends on.

    Frozen so it is hashable and so any drift between the cached band
    and the live page state is exactly the difference between two
    ``settings_hash`` values.

    Fields beyond the user's brief — ``levers_blob``, ``radios_blob``,
    ``templates_blob``, ``weather_blob`` — exist so v11's many residual
    layers (Block 1 sliders, structural assumptions, weather centroid /
    kappa, residual L1-only / L2-only choices) all participate in the
    cache key. They are tuples of (name, rounded-float-or-string) so
    every change to *any* slider invalidates the band.
    """
    state: str
    policy: str
    uncertainty_object: str        # "Residual" | "Scenario envelope"
    metric: str                    # MetricId
    n_monte_carlo: int
    random_seed: int = 20260518

    # The six sliders the brief calls out explicitly. Rounding to 8
    # decimal places matches the page-level signature so floating-point
    # noise from a no-op slider drag does not invalidate the cache.
    cav_target_2075:        float = 0.0
    sti_coverage_2075:      float = 0.0
    bev_share_growth:       float = 0.0
    low_carbon_elec_growth: float = 0.0
    hw_doubling_years:      float = 0.0
    hw_deployment_lag_years: float = 0.0

    # The rest of the residual + structural layers, captured as JSON
    # blobs so ``ScenarioSettings`` stays hashable. The blobs come from
    # ``_current_signature()`` in the page module and are reformatted
    # here.
    levers_blob:    str = ""       # sorted lever name → rounded float
    radios_blob:    str = ""       # residual-prior radio choices
    templates_blob: str = ""       # CAV/STI templates + retire + fleet form
    weather_blob:   str = ""       # weather mode + centroid + kappa
    custom_blob:    str = ""       # custom-payload signatures

    # Bundle display selector (which committed Monte Carlo bundle to
    # show alongside the live band).
    bundle_display: str = "default"


def settings_hash(settings: ScenarioSettings) -> str:
    """SHA-1 (12 hex chars) of the JSON-serialised settings dict.

    The hash is the *only* argument that needs to participate in the
    Streamlit cache key. Any change to any field — slider, radio,
    template, weather, region, policy, seed, Monte Carlo run count, or
    bundle selection — produces a different hash and thus a fresh MC run.
    """
    blob = json.dumps(asdict(settings), sort_keys=True, default=str)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


# =====================================================================
# BandSource contract
# =====================================================================
@dataclass(frozen=True)
class TrajectorySet:
    """A single metric's quantiles + raw trajectories.

    ``trajectories`` has shape ``(n_runs, T)`` so callers can apply
    ``cumsum`` (or any other transformation) per-run and re-percentile.
    """
    years: np.ndarray
    p05: np.ndarray
    p50: np.ndarray
    p95: np.ndarray
    trajectories: np.ndarray   # shape (n_runs, T)

    def n_runs(self) -> int:
        return int(self.trajectories.shape[0])

    def horizon(self) -> int:
        return int(self.trajectories.shape[1])


@dataclass(frozen=True)
class BandSource:
    """Container for one or more ``TrajectorySet`` objects keyed by
    metric column name (e.g. ``"ATS Emissions (kg CO2)"``).

    A single Monte Carlo run produces one ``BandSource`` covering every
    requested metric; cumulative views and dual-axis views read from the
    same object so they cannot drift.
    """
    label: str                                 # "residual" | "scenario_envelope"
    n_runs: int
    seed: int
    by_metric: Dict[str, TrajectorySet] = field(default_factory=dict)

    def __contains__(self, metric: str) -> bool:
        return metric in self.by_metric

    def for_metric(self, metric: str) -> Optional[TrajectorySet]:
        return self.by_metric.get(metric)


# =====================================================================
# Compute helpers (wrap core.compute_live_residual_band / envelope)
# =====================================================================
def _build_band_source(
    label: str,
    n_samples: int,
    seed: int,
    quantile_df: pd.DataFrame,
    trajectories: Dict[str, np.ndarray],
) -> BandSource:
    by_metric: Dict[str, TrajectorySet] = {}
    if quantile_df is None or quantile_df.empty:
        return BandSource(label=label, n_runs=int(n_samples), seed=int(seed))
    years_arr = np.asarray(quantile_df.index.to_numpy(), dtype=int)
    for metric, traj in trajectories.items():
        p05_col = f"{metric}_p05"
        p50_col = f"{metric}_p50"
        p95_col = f"{metric}_p95"
        if not all(c in quantile_df.columns for c in (p05_col, p50_col, p95_col)):
            continue
        by_metric[metric] = TrajectorySet(
            years=years_arr,
            p05=np.asarray(quantile_df[p05_col].to_numpy(), dtype=float),
            p50=np.asarray(quantile_df[p50_col].to_numpy(), dtype=float),
            p95=np.asarray(quantile_df[p95_col].to_numpy(), dtype=float),
            trajectories=np.asarray(traj, dtype=float),
        )
    return BandSource(
        label=label, n_runs=int(n_samples), seed=int(seed),
        by_metric=by_metric,
    )


def compute_residual_band(
    settings_hash_value: str,             # primary cache key
    settings_dict: Dict[str, Any],        # carried for traceability
    *,
    live_cfg: Dict[str, Any],
    region: str,
    n_samples: int,
    seed: int,
    years: int = 68,
    metrics: tuple = (EMISSIONS_COL, ENERGY_COL),
    runner: Optional[Callable[..., Any]] = None,
) -> BandSource:
    """Run a residual-band Monte Carlo and return a ``BandSource``.

    ``settings_hash_value`` is the only argument that needs to be hashable
    for caching purposes — pass it as the primary positional / keyword
    argument to ``@st.cache_data``. ``settings_dict`` is carried so the
    cached result records exactly which settings produced it (useful for
    inspection in tests). ``live_cfg`` and ``runner`` are kept as
    keyword-only so Streamlit's hash does not try to descend into the
    config dict — they are uniquely determined by ``settings_hash_value``.
    """
    del settings_dict  # documentary
    if runner is None:
        # Late import so the module imports cleanly in test environments
        # that don't have streamlit_app on path.
        import sys
        from pathlib import Path
        _app = Path(__file__).resolve().parent.parent.parent / "v11_streamlit_app"
        if str(_app) not in sys.path:
            sys.path.insert(0, str(_app))
        from core import compute_live_residual_band as runner  # type: ignore
    quantile_df, trajectories = runner(
        live_cfg, years=int(years), n_samples=int(n_samples),
        seed=int(seed), metric=metrics, return_trajectories=True,
    )
    return _build_band_source(
        "residual", int(n_samples), int(seed), quantile_df, trajectories,
    )


def compute_scenario_envelope_band(
    settings_hash_value: str,
    settings_dict: Dict[str, Any],
    *,
    live_cfg: Dict[str, Any],
    region: str,
    n_samples: int,
    seed: int,
    years: int = 68,
    metrics: tuple = (EMISSIONS_COL, ENERGY_COL),
    envelope_level: str = "medium",
    runner: Optional[Callable[..., Any]] = None,
) -> BandSource:
    """Run a scenario-envelope Monte Carlo and return a ``BandSource``."""
    del settings_dict
    if runner is None:
        import sys
        from pathlib import Path
        _app = Path(__file__).resolve().parent.parent.parent / "v11_streamlit_app"
        if str(_app) not in sys.path:
            sys.path.insert(0, str(_app))
        from core import compute_scenario_envelope_band as runner  # type: ignore
    quantile_df, trajectories = runner(
        live_cfg, region=region, years=int(years), n_samples=int(n_samples),
        seed=int(seed), metric=metrics, envelope_level=envelope_level,
        return_trajectories=True,
    )
    return _build_band_source(
        "scenario_envelope", int(n_samples), int(seed),
        quantile_df, trajectories,
    )


# =====================================================================
# Cumulative re-percentile helper
# =====================================================================
def cumulative_percentiles(trajectories: np.ndarray,
                            dt_years: float = 1.0) -> Dict[str, np.ndarray]:
    """Integrate each trajectory, then re-percentile.

    ``trajectories`` has shape ``(n_runs, T)``. Returns ``{"p05", "p50",
    "p95"}`` arrays of shape ``(T,)``. The crucial property — and the
    reason this function exists — is that the band widens monotonically
    over time, because ``np.cumsum(..., axis=1)`` is applied per-run
    *before* taking percentiles across runs. Integrating the percentile
    envelope instead understates the tail because the per-run rank order
    is not preserved across years.
    """
    if trajectories.size == 0:
        empty = np.array([], dtype=float)
        return {"p05": empty, "p50": empty, "p95": empty}
    cum = np.cumsum(np.asarray(trajectories, dtype=float), axis=1) * float(dt_years)
    return {
        "p05": np.quantile(cum, 0.05, axis=0),
        "p50": np.quantile(cum, 0.50, axis=0),
        "p95": np.quantile(cum, 0.95, axis=0),
    }


def cumulative_trajectory_set(ts: TrajectorySet,
                               dt_years: float = 1.0) -> TrajectorySet:
    """Return a new TrajectorySet whose values are cumulative through
    time. Cumulative trajectories are kept on the dataclass so callers
    can chain transformations or inspect the per-run cumulative draws."""
    cum = np.cumsum(ts.trajectories, axis=1) * float(dt_years)
    return TrajectorySet(
        years=ts.years,
        p05=np.quantile(cum, 0.05, axis=0),
        p50=np.quantile(cum, 0.50, axis=0),
        p95=np.quantile(cum, 0.95, axis=0),
        trajectories=cum,
    )


# =====================================================================
# Convenience constructor used by the page module
# =====================================================================
def settings_from_session(session_state: Any, defaults: Dict[str, Any]
                          ) -> ScenarioSettings:
    """Build a ``ScenarioSettings`` from Streamlit session state.

    The page module knows the canonical key names; this helper just
    rounds floats consistently with ``settings_hash``. Anything not
    present falls back to ``defaults``.
    """
    g = session_state.get if hasattr(session_state, "get") else session_state.__getitem__

    def f(key: str, default: float) -> float:
        v = g(key, default) if hasattr(session_state, "get") else default
        try:
            return round(float(v), 8)
        except (TypeError, ValueError):
            return float(default)

    return ScenarioSettings(
        state=str(defaults.get("state", "california")),
        policy=str(defaults.get("policy", "baseline")),
        uncertainty_object=str(defaults.get("uncertainty_object", "Residual")),
        metric=str(defaults.get("metric", "annual_co2")),
        n_monte_carlo=int(defaults.get("n_monte_carlo", 100)),
        random_seed=int(defaults.get("random_seed", 20260518)),
        cav_target_2075=f("expv5_cv_cav_growth_rate",
                          defaults.get("cav_target_2075", 0.45)),
        sti_coverage_2075=f("expv5_cv_sti_growth_rate",
                            defaults.get("sti_coverage_2075", 0.50)),
        bev_share_growth=f("expv5_cv_ev_growth_rate",
                           defaults.get("bev_share_growth", 0.07)),
        low_carbon_elec_growth=f("expv5_cv_clean_energy_growth_rate",
                                  defaults.get("low_carbon_elec_growth", 0.05)),
        hw_doubling_years=f("expv5_cv_efficiency_doubling_years",
                             defaults.get("hw_doubling_years", 2.8)),
        hw_deployment_lag_years=f("expv5_cv_hardware_deployment_lag_years",
                                    defaults.get("hw_deployment_lag_years", 2.0)),
        levers_blob=str(defaults.get("levers_blob", "")),
        radios_blob=str(defaults.get("radios_blob", "")),
        templates_blob=str(defaults.get("templates_blob", "")),
        weather_blob=str(defaults.get("weather_blob", "")),
        custom_blob=str(defaults.get("custom_blob", "")),
        bundle_display=str(defaults.get("bundle_display", "default")),
    )
