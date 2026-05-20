"""CLEAR-ATS v5 dashboard core.

Thin re-export of v4's tested core helpers with v5-specific corrections:

1. `load_parameter_contribution_experiment()` is repointed to the
   PARAMETER_CONTRIBUTION_EXPERIMENT.csv file, which covers California
   AND Ohio. The v4 loader preferred PARAMETER_IMPORTANCE_EXPERIMENT.csv,
   which is California-only; any Ohio selection silently fell back to
   California and only surfaced a small caption. See
   audits/final_consistency/SILENT_FAILURE_SCAN.md.

2. `apply_assumption_templates` threads Block 3 CAV/STI level-mix and
   retire-year / fleet-growth-form choices into the runtime config.

3. `v5_allowed_levels(param_id)` simplifies Block 4 uncertainty radios
   per audits/final_consistency/V5_PARAMETER_CONTROL_SIMPLIFICATION.md.

4. `compute_live_residual_band(cfg, years, n_samples, seed)` runs an
   on-demand Monte Carlo over the current runtime config and returns
   p05/p50/p95 for ATS Emissions. Used by the "Recompute residual band"
   button in the Scenario Explorer.

5. `plotly_layout_defaults()`, `year_axis_defaults()`, the Nature-family
   palettes, and `apply_matplotlib_style()` are re-exported from
   `figure_style` so pages can import everything from `core`.

No backend math is changed. Monte Carlo sampling, parameter
classification, and the four-block structure are identical to v4.
"""
from __future__ import annotations

import copy as _copy
import importlib.util
import io as _io
import sys
from contextlib import redirect_stdout as _redirect_stdout
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

V5_DIR = Path(__file__).resolve().parent
REPO_DIR = V5_DIR.parent
V4_DIR = REPO_DIR / "v4_streamlit_app"

# Load v4's core module under an alias so we do not collide with v8's own
# top-level `core` module when Streamlit places v8 first on sys.path.
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))
_v4_core_spec = importlib.util.spec_from_file_location(
    "_v4_core", V4_DIR / "core.py"
)
_v4_core = importlib.util.module_from_spec(_v4_core_spec)
assert _v4_core_spec and _v4_core_spec.loader
sys.modules["_v4_core"] = _v4_core
_v4_core_spec.loader.exec_module(_v4_core)

from _v4_core import (  # type: ignore[import-not-found]  # noqa: F401,E402
    CONTROL_SPECS,
    DEFAULT_HORIZON,
    INTERP_START_YEAR,
    INTERP_THRESHOLD,
    POLICY_LABELS,
    POLICY_ORDER,
    REGION_LABELS,
    REGION_NOTES,
    REGION_ORDER,
    REGION_PAPER_SAFETY,
    apply_controls,
    apply_parameter_choices,
    band_metadata,
    baseline_controls,
    bundle_mc_sample_count,
    controls_from_config,
    controls_match,
    deep_merge,
    fmt_count,
    fmt_emissions,
    fmt_energy,
    interpretation_boundary,
    label as display_label,
    load_base_config,
    load_bundle_quantiles as _v4_load_bundle_quantiles,
    load_layer_contribution_experiment,
    load_parameter_registry,
    load_quantiles as _v4_load_quantiles,
    load_runtime_config,
    parameter_default_choices,
    parameter_exploratory_choices,
    parameter_paper_safe_choices,
    region_paper_safety,
    rgba as core_rgba,
    run_simulation as _v4_run_simulation_base,  # superseded below for v11
    runtime_diagnostics,
    scale,
    validate_parameter_registry,
)

# ---------------------------------------------------------------------
# v11 — manuscript-aligned hybrid energy model: experiment-based
# computing (Tables 5/8) + product-spec sensing/communication (registry)
# ---------------------------------------------------------------------
# v11 routes the utility-phase energy calculation through the hybrid model:
# component registry (deployed-silicon power × counts × duty × utilization ×
# scenario) instead of the flat consumption_rates.ecav_power / sti_power config
# aggregates. The earlier dashboards (v3-v9) are untouched: this only affects
# the v11 app dir. See v11_streamlit_app/component_registry.py,
# v11_streamlit_app/experiment_computing_baseline.py, and
# audits/step_09_manuscript_method_alignment/.
if str(V5_DIR) not in sys.path:
    sys.path.insert(0, str(V5_DIR))
from component_registry import (  # noqa: E402
    ComponentRegistryEnergyModel as _CRModel,
    sample_power_overrides as _sample_power_overrides,
    sample_duty_hours as _sample_duty_hours,
)


def _v11_run_simulation(cfg: dict[str, Any], years: int = DEFAULT_HORIZON) -> pd.DataFrame:
    """v11 deterministic run: TransportModel with the component-registry energy
    model (median per-component power, base-case scenario, 3 h/day CAV duty)."""
    variants = cfg.get("model_variants") or []
    variant = variants[0] if isinstance(variants, list) and variants else (variants or {})
    if not isinstance(variant, dict):
        variant = {"type": str(variant), "name": str(variant)}
    model = _TransportModel(
        cfg["initial_data"],
        cfg["growth_rates"],
        cfg["consumption_rates"],
        cfg["emission_factors"],
        model_variants=variant or None,
        energy_model=_CRModel(),
    )
    with _redirect_stdout(_io.StringIO()):
        model.run_simulation(years=years)
    return pd.DataFrame(model.results)


# Every downstream deterministic call (`run_simulation`,
# `per_unit_l5_annual_utility_kwh`, the Scenario Explorer pages) now routes
# through the registry. The v9 dashboard's import is a separate module object;
# it is not affected.
_v4_run_simulation = _v11_run_simulation

# ---------------------------------------------------------------------
# v8 weather module
# ---------------------------------------------------------------------
import weather_module as _weather  # noqa: E402

WEATHER_REGION_KEY = "_weather_region"
WEATHER_CENTROID_KEY = "_weather_centroid_override"
WEATHER_KAPPA_KEY = "_weather_kappa_override"


def attach_weather_region(cfg: dict[str, Any], region: str,
                          centroid_override: list[float] | None = None,
                          kappa_override: float | None = None,
                          ) -> dict[str, Any]:
    """Tag a runtime config with the region used for weather lookup.

    The core simulation engine reads this tag to route each state-level
    run through the correct annual weather-share prior. ``centroid_override``
    (a 3-vector summing to 1) replaces the loaded p_state for both the
    deterministic line and the Dirichlet draw centre. ``kappa_override``
    replaces the loaded concentration when supplied.
    """
    cfg[WEATHER_REGION_KEY] = str(region).strip().lower()
    if centroid_override is not None:
        cfg[WEATHER_CENTROID_KEY] = [float(x) for x in centroid_override]
    else:
        cfg.pop(WEATHER_CENTROID_KEY, None)
    if kappa_override is not None:
        cfg[WEATHER_KAPPA_KEY] = float(kappa_override)
    else:
        cfg.pop(WEATHER_KAPPA_KEY, None)
    return cfg


def _cfg_region(cfg: dict[str, Any]) -> str | None:
    r = cfg.get(WEATHER_REGION_KEY)
    return str(r).strip().lower() if r else None


def _cfg_weather_overrides(cfg: dict[str, Any]):
    centroid = cfg.get(WEATHER_CENTROID_KEY)
    kappa = cfg.get(WEATHER_KAPPA_KEY)
    cv = None
    if centroid is not None:
        try:
            cv = np.asarray(list(centroid), dtype=float)
            if cv.size != 3 or float(cv.sum()) <= 0:
                cv = None
        except Exception:
            cv = None
    kv = None
    if kappa is not None:
        try:
            kv = float(kappa)
            if kv <= 0:
                kv = None
        except Exception:
            kv = None
    return cv, kv


def run_simulation(cfg: dict[str, Any], years: int = DEFAULT_HORIZON) -> pd.DataFrame:
    """v8 run_simulation: v4 deterministic sim + annual-mean weather factor.

    The deterministic path applies f_bar = p_state (or the user-supplied
    centroid override) so the main line is centred on the chosen
    expected weather share. The Dirichlet draw is reserved for the
    Monte Carlo band paths.
    """
    df = _v4_run_simulation(cfg, years=years)
    region = _cfg_region(cfg)
    if region is None:
        return df
    centroid, kappa = _cfg_weather_overrides(cfg)
    return _weather.apply_weather_to_results(
        df, region=region, cfg=cfg, deterministic=True,
        centroid_override=centroid, kappa_override=kappa,
    )


def _weather_adjusted_quantiles_from_mc_runs(
    region: str, policy: str, bundle: str,
) -> pd.DataFrame | None:
    """Recompute per-year quantiles from the committed MC runs after
    applying the v8 annual weather-share factor to every run/year.

    Returns a wide DataFrame indexed by Year with `{metric}_p05/p50/p95`
    columns for every numeric metric available in the mc_runs CSV, or
    ``None`` if the mc_runs file is missing.
    """
    path = (REPO_DIR / "results" /
            f"{region}__policy-{policy}__bundle-{bundle}_mc_runs.csv")
    if not path.exists():
        return None
    try:
        full = pd.read_csv(path)
    except Exception:
        return None
    if "run_id" not in full.columns or "Year" not in full.columns:
        return None
    try:
        cfg_for_weather = load_runtime_config(region, policy)
    except Exception:
        cfg_for_weather = None
    rng = np.random.default_rng(
        hash((str(region), str(policy), str(bundle), "q")) & 0xFFFFFFFF,
    )
    reweighted = _weather.apply_weather_to_mc_runs(
        full, region=region, cfg=cfg_for_weather, rng=rng,
    )
    metric_cols = [c for c in reweighted.columns
                   if c not in ("run_id", "Year")
                   and pd.api.types.is_numeric_dtype(reweighted[c])]
    years = sorted(reweighted["Year"].unique())
    out: dict[str, list[float]] = {}
    for c in metric_cols:
        p05, p50, p95 = [], [], []
        grouped = reweighted.groupby("Year")[c]
        for y in years:
            v = grouped.get_group(y).to_numpy(dtype=float)
            p05.append(float(np.percentile(v, 5)))
            p50.append(float(np.percentile(v, 50)))
            p95.append(float(np.percentile(v, 95)))
        out[f"{c}_p05"] = p05
        out[f"{c}_p50"] = p50
        out[f"{c}_p95"] = p95
    return pd.DataFrame(out, index=pd.Index(years, name="Year"))


def load_bundle_quantiles(region: str, policy: str, bundle: str):
    """Return weather-adjusted bundle quantiles, falling back to the v4
    committed quantile CSV when the backing mc_runs file is absent."""
    q = _weather_adjusted_quantiles_from_mc_runs(region, policy, bundle)
    if q is not None and not q.empty:
        return q
    return _v4_load_bundle_quantiles(region, policy, bundle)


def load_quantiles(region: str, policy: str):
    q = _weather_adjusted_quantiles_from_mc_runs(region, policy, "default")
    if q is not None and not q.empty:
        return q
    return _v4_load_quantiles(region, policy)

from footprint_model import (  # noqa: E402
    TransportModel as _TransportModel,
    sample_config as _sample_config,
)

from figure_style import (  # noqa: E402
    NATURE_CATEGORICAL,
    NATURE_LAYER,
    NATURE_MITIGATION,
    apply_matplotlib_style,
    layer_colors,
    palette_for,
    plotly_layout_defaults,
    rgba,
    year_axis_defaults,
)

PARAM_EXPERIMENT_PATH = (
    REPO_DIR / "audits" / "uncertainty_governance"
    / "PARAMETER_CONTRIBUTION_EXPERIMENT.csv"
)

# ---------------------------------------------------------------------
# v5.1.2 simplified two-level UI: Published prior (= registry "low")
# and Custom (user-defined numerical spec). The registry still supports
# medium / high for the scenario-envelope path; the UI does not expose
# them in Block 4. See audits/final_consistency/UI_SIMPLIFICATION_VALIDATION.md.
# ---------------------------------------------------------------------

_PARAM_LABELS_PATH = V5_DIR / "configs" / "parameter_labels.json"
try:
    with open(_PARAM_LABELS_PATH, encoding="utf-8") as _fh:
        _PARAM_LABELS_JSON = _json_loads = __import__("json").load(_fh)
except Exception:
    _PARAM_LABELS_JSON = {"labels": {}, "hidden_reason": {}}

PARAMETER_SHORT_LABELS: dict[str, str] = _PARAM_LABELS_JSON.get("labels", {})
PARAMETER_HIDDEN_REASON: dict[str, str] = _PARAM_LABELS_JSON.get("hidden_reason", {})


def short_label(param_id: str) -> str:
    """Human-readable short label for a parameter; falls back to the F-number."""
    return PARAMETER_SHORT_LABELS.get(param_id, param_id)


def label_with_fnum(param_id: str) -> str:
    """Short label followed by the F-number in parentheses."""
    lbl = short_label(param_id)
    if lbl == param_id:
        return param_id
    return f"{lbl} ({param_id})"


def published_prior_spec(param_id: str, region: str) -> dict[str, Any] | None:
    """Return the registry's `low`-level distribution spec for a parameter,
    substituted for the region. Used as the canonical 'Published prior'
    spec on the v5.1.2 Block 4 UI.
    """
    for rec in load_parameter_registry():
        if rec["param_id"] != param_id:
            continue
        low = rec.get("levels", {}).get("low")
        if not isinstance(low, dict):
            return None
        spec = _copy.deepcopy(low)
        # Pop _regions sentinel and apply the region override if present
        regions = spec.pop("_regions", None)
        if isinstance(regions, dict) and region in regions:
            override = regions[region]
            if isinstance(override, dict):
                spec.update(override)
        # Resolve "mean": "__REGION_MEAN__" etc. sentinels.
        base_cfg = load_base_config(region)
        ini = base_cfg.get("data_uncertainty", {}).get("initial_data", {})
        region_means = {
            "f_clean":  (ini.get("f_clean", {}) or {}).get("mean"),
            "ev_share": (ini.get("ev_share", {}) or {}).get("mean"),
        }
        region_kappas = {
            "f_clean":  (ini.get("f_clean", {}) or {}).get("kappa"),
            "ev_share": (ini.get("ev_share", {}) or {}).get("kappa"),
        }
        field = rec["config_path"].rsplit(".", 1)[-1]
        # Use v4's _resolve_level_spec via the apply_parameter_choices path
        # indirectly; here we just resolve the common sentinels.
        for k, v in list(spec.items()):
            if isinstance(v, str):
                if v == "__REGION_MEAN__" and region_means.get(field) is not None:
                    spec[k] = region_means[field]
                elif k == "kappa" and v == "__REGION_KAPPA__" and region_kappas.get(field) is not None:
                    spec[k] = region_kappas[field]
                elif k == "kappa" and v == "__REGION_KAPPA_X2__" and region_kappas.get(field) is not None:
                    spec[k] = region_kappas[field] * 2.0
                elif v == "region_mean" and region_means.get(field) is not None:
                    spec[k] = region_means[field]
        return spec
    return None


def build_data_uncertainty_v5(
    choices: dict[str, str],
    custom_specs: dict[str, dict[str, Any]],
    region: str,
) -> dict[str, Any]:
    """Compose a `data_uncertainty` block for the v5.1.2 Block 4 UI.

    `choices[pid]` is one of:
      * 'fixed'      — parameter is omitted (deterministic centre).
      * 'published'  — use the registry `low` spec (paper-safe).
      * 'custom'     — use `custom_specs[pid]` as a literal distribution
                       spec. The custom spec must contain the 'dist' key
                       and the distribution-specific parameters.
    Non-residual params must be set to 'fixed' by the caller.
    """
    import copy as _cp
    merged: dict[str, Any] = {}
    for rec in load_parameter_registry():
        pid = rec["param_id"]
        level = choices.get(pid, "fixed")
        if level == "fixed":
            continue
        if level == "custom":
            spec = _cp.deepcopy(custom_specs.get(pid) or {})
            if not isinstance(spec, dict) or "dist" not in spec:
                # Silently fall through to published (defensive; the page
                # should have validated before calling).
                spec = published_prior_spec(pid, region) or {}
        else:  # 'published' or any other legacy label
            spec = published_prior_spec(pid, region) or {}
        if not isinstance(spec, dict) or "dist" not in spec:
            continue
        # Write into the nested data_uncertainty map at the registry path
        path = rec["config_path"]
        cur = merged
        keys = path.split(".")
        for k in keys[:-1]:
            cur = cur.setdefault(k, {})
        cur[keys[-1]] = spec
    return merged


def apply_v5_choices(
    cfg: dict[str, Any],
    choices: dict[str, str],
    custom_specs: dict[str, dict[str, Any]],
    region: str,
) -> dict[str, Any]:
    """Return a deep-copy of cfg with `data_uncertainty` built from v5.1.2
    Published/Custom choices.
    """
    import copy as _cp
    new_cfg = _cp.deepcopy(cfg)
    new_cfg["data_uncertainty"] = build_data_uncertainty_v5(
        choices, custom_specs, region,
    )
    new_cfg["_parameter_choices_v5"] = dict(choices)
    return new_cfg


def validate_custom_spec(spec: dict[str, Any]) -> str | None:
    """Return a human-readable error message if the custom spec is invalid;
    return None if valid. Used by the page to show an inline warning
    without silent fallback."""
    if not isinstance(spec, dict):
        return "custom spec must be a dictionary"
    dist = spec.get("dist")
    if not dist:
        return "missing 'dist' key"
    if dist == "triangular":
        lo = spec.get("low"); mode = spec.get("mode"); hi = spec.get("high")
        if None in (lo, mode, hi):
            return "triangular needs low, mode, high"
        if not (float(lo) <= float(mode) <= float(hi)):
            return "triangular requires low ≤ mode ≤ high"
        if float(lo) == float(hi):
            return "triangular support width is zero"
    elif dist == "lognormal":
        mean = spec.get("mean"); sigma = spec.get("sigma")
        if mean is None or sigma is None:
            return "lognormal needs mean, sigma"
        if float(sigma) < 0:
            return "sigma must be non-negative"
        if float(mean) <= 0:
            return "lognormal mean must be positive"
    elif dist == "beta":
        alpha = spec.get("alpha"); beta = spec.get("beta")
        if alpha is None or beta is None:
            # beta may also use mean+kappa parameterisation
            mean = spec.get("mean"); kappa = spec.get("kappa")
            if mean is None or kappa is None:
                return "beta needs alpha, beta or mean, kappa"
            if float(kappa) <= 0:
                return "beta kappa must be positive"
        else:
            if float(alpha) <= 0 or float(beta) <= 0:
                return "beta alpha, beta must be positive"
    elif dist == "truncated_normal":
        mean = spec.get("mean"); sd = spec.get("sd")
        lo = spec.get("min"); hi = spec.get("max")
        if mean is None or sd is None:
            return "truncated_normal needs mean, sd"
        if float(sd) < 0:
            return "sd must be non-negative"
        if lo is not None and hi is not None and float(lo) >= float(hi):
            return "truncated_normal needs min < max"
    elif dist == "dirichlet":
        alpha = spec.get("alpha")
        if not isinstance(alpha, (list, tuple)) or len(alpha) == 0:
            return "dirichlet needs alpha as a non-empty list"
        if any(float(a) <= 0 for a in alpha):
            return "dirichlet alpha values must be positive"
    return None


# ---------------------------------------------------------------------------
# Block 3 assumption templates
# ---------------------------------------------------------------------------

def apply_assumption_templates(
    cfg: dict[str, Any],
    cav_levels: list[float] | None = None,
    sti_levels: list[float] | None = None,
    retire_year: int | None = None,
    fleet_linear: bool = True,
) -> dict[str, Any]:
    new_cfg = _copy.deepcopy(cfg)
    if cav_levels is not None:
        new_cfg.setdefault("consumption_rates", {})["cav_levels"] = list(cav_levels)
    if sti_levels is not None:
        new_cfg.setdefault("consumption_rates", {})["sti_levels"] = list(sti_levels)
    if retire_year is not None:
        new_cfg.setdefault("growth_rates", {})["retire_year"] = int(retire_year)
    if not fleet_linear:
        new_cfg.setdefault("growth_rates", {})["total_car_increase"] = 0.0
    return new_cfg


CAV_LEVEL_TEMPLATES: dict[str, list[float]] = {
    "L3-heavy (default)": [0.60, 0.30, 0.10],
    "Balanced":           [0.50, 0.33, 0.17],
    "L4-forward":         [0.30, 0.50, 0.20],
    "L5-forward":         [0.20, 0.40, 0.40],
}

STI_LEVEL_TEMPLATES: dict[str, list[float]] = {
    "Basic-heavy (default)":     [0.60, 0.30, 0.10],
    "Balanced":                  [0.50, 0.33, 0.17],
    "Highly-automated-forward":  [0.20, 0.40, 0.40],
}

RETIRE_YEAR_OPTIONS: list[int] = [10, 12, 15]

# ---------------------------------------------------------------------------
# v5 control simplification
# ---------------------------------------------------------------------------
# Block 4 shows only residual parameters and only the level radios we can
# defend with evidence. For each param_id we list the allowed levels that
# survive to the page. If the underlying registry offers more levels
# (e.g. MEDIUM for F09), the page clamps the user's choice into this
# smaller set. See audits/final_consistency/V5_PARAMETER_CONTROL_SIMPLIFICATION.md.
V5_ALLOWED_LEVELS: dict[str, list[str]] = {
    # L1 emission factors — retain {fixed, low, medium} because the
    # operational-only vs life-cycle-inclusive methodological spread is a
    # real evidence-based choice.
    "F03": ["fixed", "low", "medium"],
    "F04": ["fixed", "low", "medium"],
    # EPA-derived range, tight
    "F05": ["fixed", "low"],
    # L2 ECAV per-subsystem scale factors — MEDIUM is simply a wider
    # sigma over the same central spec without new evidence. Collapse to
    # {fixed, low}.
    "F09": ["fixed", "low"],
    "F10": ["fixed", "low"],
    "F11": ["fixed", "low"],
    # L2 STI per-subsystem scale factors — same reasoning.
    "F15": ["fixed", "low"],
    "F16": ["fixed", "low"],
    "F17": ["fixed", "low"],
    # L2 other load (pre-2024 cohort multiplier) — tight physical range.
    "F20": ["fixed", "low"],
}
V5_DEFAULT_LEVELS: dict[str, str] = {
    "F03": "low", "F04": "low", "F05": "low",
    "F09": "low", "F10": "low", "F11": "low",
    "F15": "low", "F16": "low", "F17": "low",
    "F20": "low",
}

# Parameters that belong elsewhere in the four-block taxonomy and must NOT
# appear as uncertainty radios in Block 4 (and must be filtered from
# residual-only driver charts). See audits/final_consistency/V5_RESIDUAL_DRIVER_SEMANTIC_FIX.md.
V5_MITIGATION_PARAMS = {"F23", "F24", "F25", "F26", "F27", "F29"}
V5_ASSUMPTION_PARAMS = {"F18", "F19", "F22", "F28"}
V5_FIXED_DATA_PARAMS = {"F01", "F02"}
V5_HIDDEN_PARAMS = {
    "F06", "F07", "F08", "F12", "F13", "F14", "F21",
    "F06_F07_F08_ecav_per_level", "F12_F13_F14_sti_per_level",
}
V5_NON_RESIDUAL_PARAMS = (
    V5_MITIGATION_PARAMS | V5_ASSUMPTION_PARAMS
    | V5_FIXED_DATA_PARAMS | V5_HIDDEN_PARAMS
)


def v5_allowed_levels(param_id: str, registry_allowed: list[str]) -> list[str]:
    simplified = V5_ALLOWED_LEVELS.get(param_id)
    if simplified is None:
        return list(registry_allowed)
    return [lvl for lvl in simplified if lvl in registry_allowed]


def v5_default_level(param_id: str, registry_default: str,
                     registry_allowed: list[str]) -> str:
    wanted = V5_DEFAULT_LEVELS.get(param_id, registry_default)
    allowed = v5_allowed_levels(param_id, registry_allowed)
    if wanted in allowed:
        return wanted
    return allowed[0] if allowed else "fixed"


def v5_parameter_default_choices() -> dict[str, str]:
    """Default Block-4 radio choices for v5.1 corrected design.

    Every parameter that the four-block taxonomy places outside Block 4
    (mitigation levers F23-F27, assumption parameters F18/F19/F22/F28,
    fixed-data anchors F01/F02, and hidden duplicates F06-F08 /
    F12-F14 / F21) is forced to FIXED in the residual-band path.
    Residual L1 and L2 parameters keep the registry's `low`
    evidence-anchored level.
    """
    out: dict[str, str] = {}
    for rec in load_parameter_registry():
        pid = rec["param_id"]
        if pid in V5_NON_RESIDUAL_PARAMS:
            out[pid] = "fixed"
        else:
            out[pid] = v5_default_level(pid, rec.get("default_level", "fixed"),
                                        rec.get("allowed_levels", []))
    return out


def v5_paper_safe_choices() -> dict[str, str]:
    """Paper-safe Block-4 radio choices for v5.1 corrected design.

    Non-residual parameters are fixed. Residual L1 and L2 parameters
    take the registry `paper_safe_level` clamped into the v5 simplified
    allowed-level set.
    """
    out: dict[str, str] = {}
    for rec in load_parameter_registry():
        pid = rec["param_id"]
        if pid in V5_NON_RESIDUAL_PARAMS:
            out[pid] = "fixed"
            continue
        allowed = v5_allowed_levels(pid, rec.get("allowed_levels", []))
        wanted = rec.get("paper_safe_level", "medium")
        if wanted not in allowed:
            for candidate in ("medium", "low", "fixed"):
                if candidate in allowed:
                    wanted = candidate
                    break
        out[pid] = wanted
    return out


# ---------------------------------------------------------------------------
# Live residual-band Monte Carlo recompute
# ---------------------------------------------------------------------------

def cumulative_band_from_mc_runs(
    region: str,
    policy: str = "baseline",
    bundle: str = "default",
    metric: str = "ATS Emissions (kg CO2)",
) -> pd.DataFrame | None:
    """Return the per-year cumulative-since-base-year p05/p50/p95
    band, computed from the per-run mc_runs CSV.

    The committed `_quantiles.csv` files only carry per-year
    percentiles; summing them across years would assume perfect
    rank correlation between MC samples and over-state the
    cumulative tail. The correct procedure is to (1) read the raw
    per-run series, (2) cumulatively sum per run, then (3) take
    percentiles across runs at each year.

    Returns a DataFrame indexed by Year with columns
    `{metric}_cum_p05`, `{metric}_cum_p50`, `{metric}_cum_p95`.
    Returns None if the mc_runs file is absent.
    """
    path = (REPO_DIR / "results" /
            f"{region}__policy-{policy}__bundle-{bundle}_mc_runs.csv")
    if not path.exists():
        return None
    try:
        full = pd.read_csv(path)
    except Exception:
        return None
    if "run_id" not in full.columns or "Year" not in full.columns:
        return None
    try:
        cfg_for_weather = load_runtime_config(region, policy)
    except Exception:
        cfg_for_weather = None
    rng = np.random.default_rng(
        hash((str(region), str(policy), str(bundle))) & 0xFFFFFFFF,
    )
    reweighted = _weather.apply_weather_to_mc_runs(
        full, region=region, cfg=cfg_for_weather, rng=rng,
    )
    if metric not in reweighted.columns:
        return None
    pivot = reweighted.pivot_table(index="Year", columns="run_id", values=metric)
    cum = pivot.cumsum(axis=0)
    arr = cum.values
    out = pd.DataFrame({
        f"{metric}_cum_p05": np.percentile(arr, 5, axis=1),
        f"{metric}_cum_p50": np.percentile(arr, 50, axis=1),
        f"{metric}_cum_p95": np.percentile(arr, 95, axis=1),
    }, index=cum.index)
    return out


def per_unit_l5_annual_utility_kwh(
    region: str = "california",
    year_offset: int = 0,
) -> float:
    """Derive per-unit L5 CAV annual utility energy from the simulator.

    Runs a minimal 1-year deterministic simulation in which the entire
    fleet is a single Level-5 CAV of the specified region at `BASE_YEAR
    + year_offset`. Returns the total ATS electricity demand for that
    single vehicle in kWh/yr. Used by the One-Time Energy inversion
    panel so the 18,232 kWh/yr figure is live-derivable rather than a
    hard-coded constant.

    Implementation note. The TransportModel's `_calculate_power` path
    returns a full fleet-level energy; to obtain a per-unit value we
    seed a 1-vehicle, 1-intersection fleet with full-L5 composition
    and a deterministic baseline configuration, then read the
    `ECAV Power (kWh)` column.
    """
    import copy as _cp
    cfg = _cp.deepcopy(load_runtime_config(region, "baseline"))
    # Collapse to a 1-vehicle / 1-intersection fleet of pure L5
    cfg["initial_data"]["total_cars"] = 1
    cfg["initial_data"]["total_ev"] = 1
    cfg["initial_data"]["total_cav"] = 1
    cfg["initial_data"]["total_sti"] = 0
    cfg["initial_data"]["total_intersections"] = 1
    # Force L5 composition
    cfg.setdefault("consumption_rates", {})["cav_levels"] = [0.0, 0.0, 1.0]
    # Disable growth so the 1-vehicle fleet does not expand
    cfg.setdefault("growth_rates", {})["total_car_increase"] = 0.0
    cfg["growth_rates"]["cav"] = 1.0
    cfg["growth_rates"]["ev"] = 0.0  # already at 1.0
    # Disable hardware-doubling compounding so we read the base-year load
    cfg["growth_rates"]["efficiency_doubling"] = 1e9
    df = _v4_run_simulation(cfg, years=max(year_offset, 0))
    df = df.set_index("Year")
    year = int(df.index[-1])
    return float(df.loc[year, "ECAV Power (kWh)"])


def compute_scenario_envelope_band(
    cfg: dict[str, Any],
    region: str,
    years: int = 68,
    n_samples: int = 120,
    seed: int = 4242,
    metric: "str | Sequence[str]" = (
        "ATS Emissions (kg CO2)", "ATS Total Power (kWh)",
    ),
    envelope_level: str = "medium",
    return_trajectories: bool = False,
):
    """Run a scenario-envelope Monte Carlo.

    Samples Block 1 mitigation levers (F23 to F27) over registry-defined
    MEDIUM priors in addition to the residual Block 4 priors at LOW.
    F22 (retire year) and F28 (fleet growth) remain fixed. F18, F19,
    F01, F02 remain fixed. The result is a "scenario envelope" band:
    wider than the residual-only band and intended to answer the
    long-horizon uncertainty question.

    `cfg` should be a runtime configuration with Block 3 templates
    already applied. This function rebuilds `data_uncertainty` from the
    composite envelope choice: LOW on residual params, MEDIUM on F23 to
    F27, FIXED everywhere else.
    """
    envelope_level = str(envelope_level).lower()
    if envelope_level not in {"low", "medium", "high"}:
        envelope_level = "medium"
    envelope_choices: dict[str, str] = {}
    registry = load_parameter_registry()
    v5_residual_defaults = v5_parameter_default_choices()
    for rec in registry:
        pid = rec["param_id"]
        reg_allowed = rec.get("allowed_levels", [])
        if pid in V5_MITIGATION_PARAMS:
            # Sample Block 1 lever uncertainty at envelope_level
            envelope_choices[pid] = (envelope_level
                                     if envelope_level in reg_allowed
                                     else "low" if "low" in reg_allowed
                                     else "fixed")
        elif pid in V5_NON_RESIDUAL_PARAMS:
            envelope_choices[pid] = "fixed"
        else:
            envelope_choices[pid] = v5_residual_defaults.get(pid, "low")
    cfg_env = apply_parameter_choices(_copy.deepcopy(cfg), envelope_choices, region)
    attach_weather_region(cfg_env, region)
    return compute_live_residual_band(cfg_env, years=years,
                                      n_samples=n_samples, seed=seed,
                                      metric=metric,
                                      return_trajectories=return_trajectories)


def compute_live_residual_band(
    cfg: dict[str, Any],
    years: int = 68,
    n_samples: int = 80,
    seed: int = 12345,
    metric: "str | Sequence[str]" = (
        "ATS Emissions (kg CO2)", "ATS Total Power (kWh)",
    ),
    return_trajectories: bool = False,
    *,
    computing_sigma_cap: float | None = None,
    sensing_comm_sigma_cap: float | None = None,
    skip_weather: bool = False,
    skip_config_sampling: bool = False,
):
    """v8 live residual-band MC.

    For each Monte Carlo sample:
      1. ``sample_config`` draws the existing Block 4 residual priors.
      2. The deterministic engine runs to produce the subsystem/emissions
         DataFrame.
      3. A fresh sequence of annual weather-share draws is applied to that
         DataFrame so the Dirichlet weather factor becomes part of the
         standard residual-band sample path.

    v9 change: ``metric`` may now be a single string (legacy behaviour) or
    a sequence of column names. When a sequence is passed the returned
    DataFrame carries one ``{metric}_p05`` / ``_p50`` / ``_p95`` triple
    per entry, all derived from the same Monte Carlo runs (no extra MC
    cost). Default is the (emissions, energy) pair so Figure A on the
    Scenario Explorer can switch metric without losing the band.
    """
    rng = np.random.default_rng(int(seed))
    variants = cfg.get("model_variants") or []
    variant = variants[0] if isinstance(variants, list) and variants else (variants or {})
    if not isinstance(variant, dict):
        variant = {"type": str(variant), "name": str(variant)}
    region = _cfg_region(cfg)
    weather_centroid, weather_kappa = _cfg_weather_overrides(cfg)

    # v11.1: optional sigma-cap overrides. When None, the dashboard
    # defaults from component_registry are used; the manuscript-figure
    # builder ``scripts/build_figure8cf_v11_residual.py`` passes tighter
    # caps reflecting the measurement-grade Extended Data Tables 5/8 +
    # vendor-datasheet ranges (the "academically-correct small
    # residual" definition).
    _po_kwargs: dict[str, Any] = {}
    if computing_sigma_cap is not None:
        _po_kwargs["computing_sigma_cap"] = float(computing_sigma_cap)
    if sensing_comm_sigma_cap is not None:
        _po_kwargs["sensing_comm_sigma_cap"] = float(sensing_comm_sigma_cap)

    per_run_frames: list[pd.DataFrame] = []
    for _ in range(int(n_samples)):
        # v11.1: optionally bypass Block-4 residual config sampling. This
        # yields the *measurement-grade* residual band — the per-component
        # power / duty load-model layer only, with data-source and
        # trajectory priors held at their committed values. The
        # manuscript-figure script uses this so the published residual
        # band reflects the genuine narrow spread of Extended Data Tables
        # 5/8 + vendor datasheets, not the wider Block-4 prior envelope.
        if skip_config_sampling:
            sampled = cfg
        else:
            sampled = _sample_config(cfg, rng)
        # v11: perturb the *physical* component parameters (per-component power,
        # CAV duty hours) and run with the bottom-up registry model. The legacy
        # flat-table scale-factor priors in sampled["consumption_rates"] are
        # inert under the registry model (they perturb tables it does not read);
        # they are kept in the config only so the v3-v9 apps still work.
        _pov = _sample_power_overrides(rng, **_po_kwargs)
        _cav_hrs = _sample_duty_hours(rng, "CAV_personal_baseline")
        model = _TransportModel(
            sampled["initial_data"],
            sampled["growth_rates"],
            sampled["consumption_rates"],
            sampled["emission_factors"],
            model_variants=variant or None,
            energy_model=_CRModel(cav_hours=_cav_hrs, power_overrides=_pov),
        )
        buf = _io.StringIO()
        with _redirect_stdout(buf):
            model.run_simulation(years=years)
        df_run = pd.DataFrame(list(model.results))
        if region is not None and not skip_weather:
            df_run = _weather.apply_weather_to_results(
                df_run, region=region, cfg=sampled, deterministic=False, rng=rng,
                centroid_override=weather_centroid,
                kappa_override=weather_kappa,
            )
        per_run_frames.append(df_run)

    if not per_run_frames:
        return pd.DataFrame()

    years_axis = per_run_frames[0]["Year"].tolist()
    # v9: support multi-metric extraction. Same MC runs, multiple
    # output columns. Numeric content is unchanged for any single
    # metric (the legacy default behaviour).
    if isinstance(metric, str):
        metric_list = [metric]
    else:
        metric_list = list(metric)
    cols: dict[str, np.ndarray] = {}
    # v11: optional per-metric trajectory array (shape (n_runs, T)) so
    # callers that need to re-percentile after a transformation (e.g.
    # cumulative cumsum) can do so faithfully — integrating the
    # percentile envelopes overstates the cumulative tail because the
    # runs are not perfectly rank-correlated across years.
    trajectories: dict[str, np.ndarray] = {}
    for _m in metric_list:
        if _m not in per_run_frames[0].columns:
            continue
        arr = np.array([df[_m].to_numpy(dtype=float) for df in per_run_frames])
        cols[f"{_m}_p05"] = np.percentile(arr,  5, axis=0)
        cols[f"{_m}_p50"] = np.percentile(arr, 50, axis=0)
        cols[f"{_m}_p95"] = np.percentile(arr, 95, axis=0)
        if return_trajectories:
            trajectories[_m] = arr
    quantile_df = pd.DataFrame(cols, index=pd.Index(years_axis, name="Year"))
    if return_trajectories:
        return quantile_df, trajectories
    return quantile_df


# ---------------------------------------------------------------------------
# v5 safety net for the parameter-contribution loader (dual-region CSV).
# ---------------------------------------------------------------------------

def _filter_to_residual(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None or df.empty:
        return df
    mask = ~df["param_id"].isin(V5_NON_RESIDUAL_PARAMS)
    return df[mask].copy()


def load_parameter_contribution_experiment(
    residual_only: bool = False,
) -> pd.DataFrame | None:
    """Return the dual-region parameter-contribution table.

    residual_only=True filters out mitigation levers (F23–F27), assumption
    parameters (F18, F19, F22, F28), fixed-data anchors (F01, F02), and
    hidden scale/level axes (F06–F08, F12–F14, F21 and the compound IDs).
    Use this mode for Figure B and Figure C so the residual-only semantic
    is preserved.
    """
    if PARAM_EXPERIMENT_PATH.exists():
        try:
            df = pd.read_csv(PARAM_EXPERIMENT_PATH)
            return _filter_to_residual(df) if residual_only else df
        except Exception:
            pass
    # Safety net: fall through to the v4 loader if the primary CSV is missing.
    df = _v4_core.load_parameter_contribution_experiment()
    return _filter_to_residual(df) if residual_only else df


__all__ = [
    "CAV_LEVEL_TEMPLATES",
    "CONTROL_SPECS",
    "DEFAULT_HORIZON",
    "INTERP_START_YEAR",
    "INTERP_THRESHOLD",
    "NATURE_CATEGORICAL",
    "NATURE_LAYER",
    "NATURE_MITIGATION",
    "POLICY_LABELS",
    "POLICY_ORDER",
    "REGION_LABELS",
    "REGION_NOTES",
    "REGION_ORDER",
    "REGION_PAPER_SAFETY",
    "RETIRE_YEAR_OPTIONS",
    "STI_LEVEL_TEMPLATES",
    "V5_ALLOWED_LEVELS",
    "V5_ASSUMPTION_PARAMS",
    "V5_DEFAULT_LEVELS",
    "V5_FIXED_DATA_PARAMS",
    "V5_HIDDEN_PARAMS",
    "V5_MITIGATION_PARAMS",
    "V5_NON_RESIDUAL_PARAMS",
    "apply_assumption_templates",
    "attach_weather_region",
    "apply_controls",
    "apply_matplotlib_style",
    "apply_parameter_choices",
    "band_metadata",
    "baseline_controls",
    "bundle_mc_sample_count",
    "compute_live_residual_band",
    "compute_scenario_envelope_band",
    "cumulative_band_from_mc_runs",
    "per_unit_l5_annual_utility_kwh",
    "PARAMETER_HIDDEN_REASON",
    "PARAMETER_SHORT_LABELS",
    "apply_v5_choices",
    "build_data_uncertainty_v5",
    "label_with_fnum",
    "published_prior_spec",
    "short_label",
    "validate_custom_spec",
    "controls_from_config",
    "controls_match",
    "deep_merge",
    "display_label",
    "fmt_count",
    "fmt_emissions",
    "fmt_energy",
    "interpretation_boundary",
    "layer_colors",
    "load_base_config",
    "load_bundle_quantiles",
    "load_layer_contribution_experiment",
    "load_parameter_contribution_experiment",
    "load_parameter_registry",
    "load_quantiles",
    "load_runtime_config",
    "palette_for",
    "parameter_default_choices",
    "parameter_exploratory_choices",
    "parameter_paper_safe_choices",
    "plotly_layout_defaults",
    "region_paper_safety",
    "rgba",
    "core_rgba",
    "run_simulation",
    "runtime_diagnostics",
    "scale",
    "v5_allowed_levels",
    "v5_default_level",
    "v5_paper_safe_choices",
    "v5_parameter_default_choices",
    "validate_parameter_registry",
    "year_axis_defaults",
]
