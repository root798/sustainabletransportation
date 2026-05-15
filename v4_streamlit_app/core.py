"""
CLEAR-ATS v4 dashboard core — shared logic for all pages.

Terminology rules enforced in this module:
 - "energy" not "power" for annual kWh quantities
 - "annual" vs "cumulative" always explicit
 - "scenario-conditioned projection" not "forecast/prediction"
"""
from __future__ import annotations

import copy
import io
import json
import math
import sys
from collections import OrderedDict
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
REPO_DIR = APP_DIR.parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from footprint_model import (  # noqa: E402
    TransportModel,
    BASE_YEAR as FM_BASE_YEAR,
    TARGET_YEAR as FM_TARGET_YEAR,
    INTERP_BOUNDARY_THRESHOLD as FM_INTERP_THRESHOLD,
    INTERP_BOUNDARY_START_YEAR as FM_INTERP_START_YEAR,
    INTERP_BOUNDARY_METRIC as FM_INTERP_METRIC,
    TURNING_YEAR_DECLINE_RATIO as FM_TURNING_RATIO,
    compute_interpretation_boundary as fm_compute_interpretation_boundary,
)

RESULTS_DIR = REPO_DIR / "results"
# Canonical scenario source-of-truth lives in scenarios/{region}/scenario.json.
# CONFIGS_DIR is preserved as a legacy fallback path.
SCENARIOS_DIR = REPO_DIR / "scenarios"
CONFIGS_DIR = REPO_DIR / "configs"
UI_PRESETS_DIR = REPO_DIR / "configs" / "ui_presets"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REGION_ORDER = ["california", "ohio", "us_average"]
REGION_LABELS = {
    "california": "California",
    "ohio": "Ohio",
    "us_average": "U.S. Average (synthetic CA/OH midpoint)",
}
REGION_NOTES = {
    "california": "Baseline vehicle stock and BEV count cross-checked to DOE AFDC 2024 light-duty registrations.  Initial low-carbon electricity share cross-checked to 2024 EIA California electricity data.",
    "ohio": "Baseline vehicle stock and BEV count cross-checked to DOE AFDC 2024 light-duty registrations.  Initial low-carbon electricity share cross-checked to 2024 EIA Ohio electricity data.",
    "us_average": (
        "Distinct synthetic scenario — NOT an official national total. Initial-state "
        "fields are arithmetic midpoints of CA and OH; growth rates, CAV/STI targets, "
        "efficiency, and consumption-rate tables are independent assumptions (NOT midpoints). "
        "U.S. Average sensing/communication consumption values diverge 10–30× from CA/OH; "
        "treat U.S. Average energy and emissions as scenario-illustrative only until the "
        "anomaly is resolved. See US_AVERAGE_DECISION_NOTE.md."
    ),
}
POLICY_ORDER = ["baseline", "aggressive", "conservative"]
POLICY_LABELS = {
    "baseline": "Baseline",
    "aggressive": "Aggressive",
    "conservative": "Conservative",
}
MODEL_ORDER = ["fixed_table"]
BASE_YEAR = FM_BASE_YEAR  # single source of truth in footprint_model
DEFAULT_HORIZON = 68  # years from BASE_YEAR → 2092

# Interpretation-boundary constants are now centralized in footprint_model.
# Re-exported here so existing page imports continue to work.
INTERP_THRESHOLD = FM_INTERP_THRESHOLD
INTERP_START_YEAR = FM_INTERP_START_YEAR

# ---------------------------------------------------------------------------
# Control specs — one definition for every slider/input
# ---------------------------------------------------------------------------
CONTROL_SPECS = OrderedDict([
    ("cav_growth_rate", {
        "label": "CAV target fraction by 2075",
        "path": ("growth_rates", "cav"),
        "kind": "float", "min": 0.0, "max": 0.95, "step": 0.01,
        "help": "Target autonomous-vehicle fleet fraction reached by 2075 (not an annual growth exponent).",
    }),
    ("sti_growth_rate", {
        "label": "STI coverage target by 2075",
        "path": ("growth_rates", "sti"),
        "kind": "float", "min": 0.0, "max": 0.95, "step": 0.01,
        "help": "Target smart-infrastructure coverage fraction reached by 2075.",
    }),
    ("ev_growth_rate", {
        "label": "Annual BEV-share growth",
        "path": ("growth_rates", "ev"),
        "kind": "float", "min": 0.0, "max": 0.50, "step": 0.01,
    }),
    ("clean_energy_growth_rate", {
        "label": "Annual low-carbon electricity share growth",
        "path": ("growth_rates", "clean_energy"),
        "kind": "float", "min": 0.0, "max": 0.30, "step": 0.005,
    }),
    ("fleet_growth_rate", {
        "label": "Annual fleet growth rate",
        "path": ("growth_rates", "total_car_increase"),
        "kind": "float", "min": -0.01, "max": 0.03, "step": 0.001,
    }),
    ("efficiency_doubling_years", {
        "label": "Hardware efficiency doubling time (years)",
        "path": ("growth_rates", "efficiency_doubling"),
        "kind": "float", "min": 1.0, "max": 20.0, "step": 0.1,
    }),
    ("hardware_deployment_lag_years", {
        "label": "Hardware deployment lag (years)",
        "path": ("growth_rates", "hardware_deployment_lag_years"),
        "kind": "float", "min": 0.0, "max": 5.0, "step": 0.1,
        "help": "Years between frontier hardware improvement and in-fleet installation. Shifts when cohorts realize efficiency gains; does not change the doubling time.",
    }),
    ("retire_year", {
        "label": "Vehicle service life (years)",
        "path": ("growth_rates", "retire_year"),
        "kind": "int", "min": 1, "max": 30, "step": 1,
    }),
    ("initial_clean_fraction", {
        "label": "Initial low-carbon electricity share",
        "path": ("initial_data", "f_clean"),
        "kind": "float", "min": 0.0, "max": 1.0, "step": 0.01,
    }),
    ("initial_ev_share", {
        "label": "Initial BEV share",
        "path": ("initial_data", "total_ev_share"),
        "kind": "float", "min": 0.0, "max": 1.0, "step": 0.001,
    }),
    ("total_cars", {
        "label": "Initial vehicle stock",
        "path": ("initial_data", "total_cars"),
        "kind": "int", "min": 1, "max": 500_000_000, "step": 10_000,
    }),
    ("total_intersections", {
        "label": "Convertible intersections",
        "path": ("initial_data", "total_intersections"),
        "kind": "int", "min": 1, "max": 10_000_000, "step": 100,
    }),
])

# Corrected display labels: "energy" not "power", units explicit
DISPLAY_LABELS: dict[str, str] = {
    "ATS Total Power (kWh)": "ATS total annual energy demand (kWh/yr)",
    "ECAV Power (kWh)": "ECAV annual energy demand (kWh/yr)",
    "ICECAV Power (kWh)": "ICEAV annual energy demand (kWh/yr)",
    "STI Power (kWh)": "STI annual energy demand (kWh/yr)",
    "ATS Emissions (kg CO2)": "ATS total annual CO\u2082 emissions (kg CO\u2082/yr)",
    "ECAV Emissions (kg CO2)": "ECAV annual CO\u2082 emissions (kg CO\u2082/yr)",
    "ICECAV Emissions (kg CO2)": "ICEAV annual CO\u2082 emissions (kg CO\u2082/yr)",
    "STI Emissions (kg CO2)": "STI annual CO\u2082 emissions (kg CO\u2082/yr)",
    "Total Vehicles": "Total modeled vehicles",
    "Total EV": "Total BEVs",
    "Total CAV": "Total autonomous vehicles",
    "Total STI": "Total smart-infrastructure units",
    "EV Fraction": "BEV share of modeled stock",
    "Clean Energy Fraction": "Low-carbon electricity share",
}

PROVENANCE_CLASSES = {
    "direct_simulation": "Direct simulation output from TransportModel",
    "derived": "Derived from simulation outputs (formula applied post-run)",
    "scenario_assumption": "Scenario assumption / input parameter",
    "conceptual": "Conceptual only — not quantitatively implemented",
}


# ===================================================================
# Config helpers
# ===================================================================

def load_base_config(region: str) -> dict[str, Any]:
    """Load the canonical scenario file for `region`.

    Primary path:   scenarios/{region}/scenario.json
    Legacy path:    configs/{region}.json
    """
    canonical = SCENARIOS_DIR / region / "scenario.json"
    legacy = CONFIGS_DIR / f"{region}.json"
    path = canonical if canonical.exists() else legacy
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def deep_merge(base: dict, overrides: dict) -> dict:
    merged = copy.deepcopy(base)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = copy.deepcopy(v)
    return merged


def available_policies(region: str) -> list[str]:
    cfg = load_base_config(region)
    names = list(cfg.get("policy_scenarios", {}).keys())
    if "baseline" not in names:
        names.insert(0, "baseline")
    ordered = [p for p in POLICY_ORDER if p in names]
    extras = sorted(set(names) - set(POLICY_ORDER))
    return ordered + extras or ["baseline"]


def load_runtime_config(region: str, policy: str = "baseline") -> dict[str, Any]:
    base = load_base_config(region)
    patch = copy.deepcopy(base.get("policy_scenarios", {}).get(policy, {}))
    return deep_merge(base, patch)


# ===================================================================
# Control-value ↔ config conversion
# ===================================================================

def controls_from_config(cfg: dict[str, Any], region: str, policy: str) -> dict[str, Any]:
    ini = cfg["initial_data"]
    gr = cfg["growth_rates"]
    total = max(float(ini["total_cars"]), 1.0)
    vals: dict[str, Any] = {"region": region, "policy": policy}
    for key, spec in CONTROL_SPECS.items():
        sec, name = spec["path"]
        if key == "initial_ev_share":
            vals[key] = float(ini["total_ev"]) / total
        elif sec == "initial_data":
            vals[key] = ini[name]
        else:
            # Graceful fallback for controls added after some scenario files
            # were written (e.g., F29 hardware_deployment_lag_years).
            vals[key] = gr.get(name, float(spec.get("min", 0.0))
                               if spec.get("kind") == "float" else int(spec.get("min", 0)))
    return vals


def apply_controls(base_cfg: dict[str, Any], cv: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)
    ini = cfg["initial_data"]
    gr = cfg["growth_rates"]
    for key, spec in CONTROL_SPECS.items():
        if key not in cv:
            continue
        sec, name = spec["path"]
        v = cv[key]
        if key == "initial_ev_share":
            tc = max(int(cv.get("total_cars", ini["total_cars"])), 1)
            ini["total_cars"] = tc
            ini["total_ev"] = int(round(tc * min(max(float(v), 0.0), 1.0)))
            continue
        target = ini if sec == "initial_data" else gr
        target[name] = int(round(v)) if spec["kind"] == "int" else float(v)
    ini["total_ev"] = min(ini["total_ev"], ini["total_cars"])
    ini["f_clean"] = min(max(float(ini["f_clean"]), 0.0), 1.0)
    gr["retire_year"] = max(int(round(gr["retire_year"])), 1)
    return cfg


def baseline_controls(region: str, policy: str) -> dict[str, Any]:
    """Control-value snapshot for the committed baseline configuration.

    Used to detect whether a slider has been moved off the baseline state; if
    it has, any precomputed uncertainty overlay for (region, policy) is stale
    and must not be displayed as if it matched the live deterministic line.
    """
    cfg = load_runtime_config(region, policy)
    return controls_from_config(cfg, region, policy)


def overlay_is_stale(cv: dict[str, Any]) -> bool:
    """Return True if the live slider state differs from the committed baseline.

    When True, callers should suppress or clearly mark the uncertainty overlay
    as stale; the precomputed quantile file was generated from the baseline
    configuration only.
    """
    try:
        base = baseline_controls(cv.get("region", ""), cv.get("policy", "baseline"))
    except Exception:
        return True
    return not controls_match(base, cv)


def controls_match(a: dict, b: dict, tol: float = 1e-9) -> bool:
    for key in CONTROL_SPECS:
        av, bv = a.get(key), b.get(key)
        if isinstance(av, float) or isinstance(bv, float):
            if abs(float(av or 0) - float(bv or 0)) > tol:
                return False
        elif av != bv:
            return False
    return a.get("region") == b.get("region") and a.get("policy") == b.get("policy")


# ===================================================================
# Simulation
# ===================================================================

def run_simulation(cfg: dict[str, Any], years: int = DEFAULT_HORIZON) -> pd.DataFrame:
    # Pass model_variants through so live-resim honours the scenario's declared
    # adoption / efficiency curve form. Previously this kwarg was dropped, which
    # silently forced constructor defaults regardless of scenario declaration
    # (see dossier S4-03). Current CA/OH scenarios declare the defaults, so this
    # is a latent-regression fix; behaviour is byte-identical on today's configs
    # and correct for any future scenario that overrides the variant.
    variants = cfg.get("model_variants") or []
    variant = variants[0] if isinstance(variants, list) and variants else (variants or {})
    if not isinstance(variant, dict):
        variant = {"type": str(variant), "name": str(variant)}
    model = TransportModel(
        cfg["initial_data"],
        cfg["growth_rates"],
        cfg["consumption_rates"],
        cfg["emission_factors"],
        model_variants=variant or None,
    )
    with redirect_stdout(io.StringIO()):
        model.run_simulation(years=years)
    return pd.DataFrame(model.results)


# ===================================================================
# Formatting helpers
# ===================================================================

def label(col: str) -> str:
    return DISPLAY_LABELS.get(col, col)


def _auto_scale(series: pd.Series, kind: str) -> tuple[pd.Series, str, float]:
    """Auto-scale a series to a readable unit.

    ENERGY: the backend stores annual energy values in **kWh/yr** (CSV columns
    are labelled "(kWh)" but represent per-year totals). Correct conversions:
        1 TWh = 1e9 kWh, 1 GWh = 1e6 kWh, 1 MWh = 1e3 kWh.
    EMISSIONS: stored in **kg CO2/yr**. 1 Mt = 1e9 kg, 1 kt = 1e6 kg.
    COUNT: raw integer count. 1 million = 1e6, 1 thousand = 1e3.

    NOTE: the original energy divisors here were authored as if the series
    were in Wh, labelling values 1000x too small (e.g. 5.92 TWh/yr shown as
    "5.92 GWh/yr"). The divisors below are the corrected versions.
    """
    mx = float(series.abs().max()) if not series.empty else 0.0
    if kind == "energy":
        for div, unit in [(1e9, "TWh/yr"), (1e6, "GWh/yr"), (1e3, "MWh/yr")]:
            if mx >= div:
                return series / div, unit, div
        return series, "kWh/yr", 1.0
    if kind == "emissions":
        for div, unit in [(1e9, "Mt CO\u2082/yr"), (1e6, "kt CO\u2082/yr")]:
            if mx >= div:
                return series / div, unit, div
        return series, "kg CO\u2082/yr", 1.0
    if kind == "count":
        for div, unit in [(1e6, "million"), (1e3, "thousand")]:
            if mx >= div:
                return series / div, unit, div
        return series, "", 1.0
    return series, "", 1.0


def scale(series: pd.Series, kind: str) -> tuple[pd.Series, str, float]:
    return _auto_scale(series, kind)


def fmt_energy(v: float) -> str:
    # Input is annual energy in kWh/yr. Conversions: 1 TWh = 1e9 kWh,
    # 1 GWh = 1e6 kWh, 1 MWh = 1e3 kWh. Previously these divisors were
    # 1000x too large (wrong label scale).
    for div, u in [(1e9, "TWh/yr"), (1e6, "GWh/yr"), (1e3, "MWh/yr")]:
        if abs(v) >= div:
            return f"{v/div:.2f} {u}"
    return f"{v:,.0f} kWh/yr"


def fmt_emissions(v: float) -> str:
    for div, u in [(1e9, "Mt CO\u2082/yr"), (1e6, "kt CO\u2082/yr")]:
        if abs(v) >= div:
            return f"{v/div:.2f} {u}"
    return f"{v:,.0f} kg CO\u2082/yr"


def fmt_count(v: float) -> str:
    for div, u in [(1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if abs(v) >= div:
            return f"{v/div:.2f}{u}"
    return f"{v:,.0f}"


def rgba(color: str, alpha: float) -> str:
    c = color.strip().lstrip("#")
    if len(c) == 6:
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(128,128,128,{alpha})"


# ===================================================================
# Quantile / uncertainty helpers
# ===================================================================

def quantile_path(region: str, policy: str) -> Path:
    return RESULTS_DIR / f"{region}__policy-{policy}__model-fixed_table_quantiles.csv"


def mc_runs_path(region: str, policy: str) -> Path:
    return RESULTS_DIR / f"{region}__policy-{policy}__model-fixed_table_mc_runs.csv"


def load_quantiles(region: str, policy: str) -> pd.DataFrame | None:
    p = quantile_path(region, policy)
    if not p.exists():
        return None
    df = pd.read_csv(p)
    if "Year" in df.columns:
        df = df.set_index("Year")
    return df


def mc_sample_count(region: str, policy: str) -> int | None:
    p = mc_runs_path(region, policy)
    if not p.exists():
        return None
    return int(pd.read_csv(p, usecols=["run_id"])["run_id"].nunique())


def saturation_metadata_path(region: str, policy: str) -> Path:
    return RESULTS_DIR / f"{region}__policy-{policy}__model-fixed_table_quantiles_metadata.json"


def load_saturation_metadata(region: str, policy: str) -> dict[str, Any]:
    """Load the saturation sidecar JSON for a region / policy.

    Returns an empty dict with a `missing=True` flag if the sidecar is
    absent (e.g. for a freshly-added region or an un-refreshed scenario).
    Callers should treat a missing sidecar as 'no saturation annotations'.
    """
    p = saturation_metadata_path(region, policy)
    if not p.exists():
        return {"missing": True, "start_year": None, "fields": {}}
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {"missing": True, "start_year": None, "fields": {}, "error": "failed_to_parse"}


# Paper-safety / quarantine flags. Used by dashboards to mark regions that
# must NOT be cited quantitatively in paper figures. See
# audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md.
REGION_PAPER_SAFETY: dict[str, dict[str, Any]] = {
    "california": {"paper_safe": True, "note": ""},
    "ohio": {"paper_safe": True, "note": ""},
    "us_average": {
        "paper_safe": False,
        "note": (
            "U.S. Average is quarantined from paper-facing quantitative comparison. "
            "Its consumption_rates sensing and communication cells diverge 10\u201330\u00d7 from CA/OH; "
            "see audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md."
        ),
    },
}


def region_paper_safety(region: str) -> dict[str, Any]:
    return REGION_PAPER_SAFETY.get(region, {"paper_safe": True, "note": ""})


def band_metadata(qf: pd.DataFrame | None, metric: str) -> dict[str, Any]:
    meta = {"available": False, "degenerate": True, "max_width": 0.0}
    if qf is None:
        return meta
    cols = [f"{metric}_p05", f"{metric}_p50", f"{metric}_p95"]
    if any(c not in qf.columns for c in cols):
        return meta
    w = (qf[cols[2]] - qf[cols[0]]).abs()
    meta["available"] = True
    meta["max_width"] = float(w.max())
    meta["degenerate"] = float(w.max()) == 0.0
    return meta


def interpretation_boundary(qf: pd.DataFrame | None,
                            metric: str = FM_INTERP_METRIC,
                            threshold: float = INTERP_THRESHOLD,
                            start: int = INTERP_START_YEAR) -> dict[str, Any]:
    """Delegates to footprint_model.compute_interpretation_boundary.

    Pages expect a key named `year`; the backend helper uses `boundary_year`.
    We expose both for backward compatibility.
    """
    res = fm_compute_interpretation_boundary(
        qf, metric_base=metric, threshold=threshold, start_year=start
    )
    res["year"] = res.get("boundary_year")
    return res


# ===================================================================
# Turning / peak metrics (derived, not forecast claims)
# ===================================================================

def compute_turning_metrics(df: pd.DataFrame) -> dict[str, Any]:
    em = df["ATS Emissions (kg CO2)"]
    idx = em.idxmax()
    peak_yr = int(df.loc[idx, "Year"])
    peak_val = float(em.loc[idx])
    turning = None
    for _, row in df.loc[df["Year"] >= peak_yr].iterrows():
        if float(row["ATS Emissions (kg CO2)"]) <= peak_val * 0.5:
            turning = int(row["Year"])
            break
    return {
        "peak_year": peak_yr,
        "peak_emissions": peak_val,
        "turning_year": turning,
        "cumulative_emissions_kg": float(em.sum()),
        "cumulative_energy_kwh": float(df["ATS Total Power (kWh)"].sum()),
    }


# ===================================================================
# Runtime diagnostics table
# ===================================================================

def runtime_diagnostics(cfg: dict[str, Any], region: str, policy: str) -> list[dict]:
    ini = cfg["initial_data"]
    gr = cfg["growth_rates"]
    ef = cfg["emission_factors"]
    tc = max(float(ini["total_cars"]), 1.0)
    return [
        {"Parameter": "Region", "Value": REGION_LABELS.get(region, region), "Unit": ""},
        {"Parameter": "Policy", "Value": POLICY_LABELS.get(policy, policy), "Unit": ""},
        {"Parameter": "Vehicle stock", "Value": f"{int(ini['total_cars']):,}", "Unit": "count"},
        {"Parameter": "Intersections", "Value": f"{int(ini['total_intersections']):,}", "Unit": "count"},
        {"Parameter": "Initial CAV count", "Value": f"{int(ini['total_cav']):,}", "Unit": "count"},
        {"Parameter": "Initial STI count", "Value": f"{int(ini['total_sti']):,}", "Unit": "count"},
        {"Parameter": "Initial BEV share", "Value": f"{float(ini['total_ev'])/tc:.4f}", "Unit": "fraction"},
        {"Parameter": "Initial low-carbon share", "Value": f"{float(ini['f_clean']):.4f}", "Unit": "fraction"},
        {"Parameter": "BEV-share growth", "Value": f"{float(gr['ev']):.4f}", "Unit": "fraction/yr"},
        {"Parameter": "Low-carbon share growth", "Value": f"{float(gr['clean_energy']):.4f}", "Unit": "fraction/yr"},
        {"Parameter": "CAV target fraction", "Value": f"{float(gr['cav']):.4f}", "Unit": "by 2075"},
        {"Parameter": "STI target fraction", "Value": f"{float(gr['sti']):.4f}", "Unit": "by 2075"},
        {"Parameter": "Efficiency doubling", "Value": f"{float(gr['efficiency_doubling']):.2f}", "Unit": "years"},
        {"Parameter": "Service life", "Value": str(int(gr['retire_year'])), "Unit": "years"},
        {"Parameter": "Fleet growth", "Value": f"{float(gr['total_car_increase']):.4f}", "Unit": "fraction/yr"},
        {"Parameter": "e_clean", "Value": f"{float(ef['e_clean']):.4f}", "Unit": "kg CO\u2082/kWh"},
        {"Parameter": "e_fossil", "Value": f"{float(ef['e_fossil']):.4f}", "Unit": "kg CO\u2082/kWh"},
        {"Parameter": "e_gasoline", "Value": f"{float(ef['e_gasoline']):.4f}", "Unit": "kg CO\u2082/kWh-eq"},
    ]


# ===================================================================
# Legacy global uncertainty presets (LOW / MEDIUM / HIGH)
# ===================================================================
# SUPERSEDED by the parameter-level registry in configs/ui_parameter_presets/.
# Retained for backward compatibility with archived Panel 2 / Panel 3 pages.
# The live Scenario Explorer uses parameter_default_choices() etc. instead.

UNCERTAINTY_PRESETS = ("low", "medium", "high")


def uncertainty_preset_path(preset: str) -> Path:
    return UI_PRESETS_DIR / f"uncertainty_{preset.lower()}.json"


def _substitute_region_means(spec: Any, region_means: dict[str, float], parent_key: str | None = None) -> Any:
    """Walk the preset JSON and replace the `__REGION_MEAN__` sentinel on
    `initial_data.f_clean.mean` / `initial_data.ev_share.mean` with the
    canonical region-specific means from the scenario file. The caller
    threads the parent field name (e.g. "f_clean" / "ev_share") so we can
    look up the right region mean regardless of how many distribution keys
    are present.
    """
    if isinstance(spec, dict):
        out = {}
        for k, v in spec.items():
            if (
                isinstance(v, str) and v == "__REGION_MEAN__"
                and k == "mean" and parent_key in region_means
                and region_means[parent_key] is not None
            ):
                out[k] = region_means[parent_key]
            else:
                out[k] = _substitute_region_means(v, region_means, parent_key=k)
        return out
    if isinstance(spec, list):
        return [_substitute_region_means(x, region_means, parent_key=parent_key) for x in spec]
    return spec


def load_uncertainty_preset(preset: str, region: str) -> dict[str, Any]:
    """Load a preset JSON and return a `data_uncertainty` dict ready to
    replace the block in a runtime config. Region-specific means are
    substituted from `scenarios/{region}/scenario.json`.

    Raises FileNotFoundError if the preset JSON is absent and KeyError if
    the preset is not in the registered set.
    """
    preset_key = str(preset).lower()
    if preset_key not in UNCERTAINTY_PRESETS:
        raise KeyError(
            f"Unknown uncertainty preset {preset!r}; expected one of {UNCERTAINTY_PRESETS}"
        )
    path = uncertainty_preset_path(preset_key)
    if not path.exists():
        raise FileNotFoundError(f"Missing preset file: {path}")
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)

    base = load_base_config(region)
    ini = base.get("data_uncertainty", {}).get("initial_data", {})
    region_means = {
        "f_clean":  (ini.get("f_clean", {}) or {}).get("mean"),
        "ev_share": (ini.get("ev_share", {}) or {}).get("mean"),
    }
    data_uncertainty = _substitute_region_means(
        payload.get("data_uncertainty", {}), region_means
    )
    return {
        "preset": preset_key,
        "label": payload.get("label", preset_key),
        "description": payload.get("description", ""),
        "paper_safe": bool(payload.get("paper_safe", False)),
        "data_uncertainty": data_uncertainty,
        "notes": payload.get("notes", {}),
    }


def apply_uncertainty_preset(cfg: dict[str, Any], preset: str, region: str) -> dict[str, Any]:
    """Return a copy of `cfg` with its `data_uncertainty` block replaced by
    the given preset for `region`. Deterministic fields (initial_data,
    growth_rates, consumption_rates, emission_factors centre values) are
    NEVER touched by the preset; this is enforced by the preset-design
    contract (see UNCERTAINTY_PRESET_DESIGN.md invariant 1).
    """
    preset_obj = load_uncertainty_preset(preset, region)
    new_cfg = copy.deepcopy(cfg)
    new_cfg["data_uncertainty"] = preset_obj["data_uncertainty"]
    new_cfg["_uncertainty_preset"] = {
        "name": preset_obj["preset"],
        "label": preset_obj["label"],
        "paper_safe": preset_obj["paper_safe"],
    }
    return new_cfg


# ---------------------------------------------------------------------------
# Grouped per-layer uncertainty presets (next-version panel)
# ---------------------------------------------------------------------------

L1_PRESETS = ("fixed", "low", "medium")
L2_PRESETS = ("fixed", "low", "medium", "high")
L3_PRESETS = ("fixed", "low", "medium", "high")

GROUPED_PRESET_FILE = {
    "L1": {p: UI_PRESETS_DIR / f"l1_{p}.json" for p in L1_PRESETS},
    "L2": {p: UI_PRESETS_DIR / f"l2_{p}.json" for p in L2_PRESETS},
    "L3": {p: UI_PRESETS_DIR / f"l3_{p}.json" for p in L3_PRESETS},
}


def _substitute_region_kappa(spec: Any, kappas: dict[str, float], parent_key: str | None = None) -> Any:
    """Walk the preset JSON and replace `__REGION_KAPPA__` and
    `__REGION_KAPPA_X2__` sentinels on `kappa` fields with the per-field
    region-specific Beta concentration. `kappas` maps field name
    (e.g. "f_clean" or "ev_share") to its committed kappa.
    """
    if isinstance(spec, dict):
        out = {}
        for k, v in spec.items():
            if k == "kappa" and isinstance(v, str) and parent_key in kappas:
                kv = kappas.get(parent_key)
                if v == "__REGION_KAPPA__" and kv is not None:
                    out[k] = kv
                elif v == "__REGION_KAPPA_X2__" and kv is not None:
                    out[k] = kv * 2.0
                else:
                    out[k] = v
            else:
                out[k] = _substitute_region_kappa(v, kappas, parent_key=k)
        return out
    if isinstance(spec, list):
        return [_substitute_region_kappa(x, kappas, parent_key=parent_key) for x in spec]
    return spec


def _load_grouped_preset_file(layer: str, choice: str) -> dict[str, Any]:
    layer = layer.upper()
    choice = str(choice).lower()
    registry = GROUPED_PRESET_FILE.get(layer)
    if registry is None:
        raise KeyError(f"Unknown grouped-preset layer {layer!r}")
    if choice not in registry:
        raise KeyError(
            f"Unknown grouped-preset choice {choice!r} for {layer}; expected one of {sorted(registry)}"
        )
    path = registry[choice]
    if not path.exists():
        raise FileNotFoundError(f"Missing grouped-preset file: {path}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_grouped_uncertainty_preset(
    l1_choice: str = "fixed",
    l2_choice: str = "low",
    l3_choice: str = "low",
    region: str = "california",
) -> dict[str, Any]:
    """Compose a merged `data_uncertainty` block from per-layer preset JSONs.

    Returns dict with keys:
      - `bundle`:        (l1, l2, l3) tuple
      - `labels`:        human labels per layer
      - `paper_safe`:    true iff every chosen preset is paper-safe
      - `data_uncertainty`: merged block ready to overwrite config
      - `fixed_factors`: list of factor ids that this bundle fixes
      - `notes`:         per-layer notes for panel display
    """
    base = load_base_config(region)
    ini = base.get("data_uncertainty", {}).get("initial_data", {})
    region_means = {
        "f_clean":  (ini.get("f_clean", {}) or {}).get("mean"),
        "ev_share": (ini.get("ev_share", {}) or {}).get("mean"),
    }
    region_kappas = {
        "f_clean":  (ini.get("f_clean", {}) or {}).get("kappa"),
        "ev_share": (ini.get("ev_share", {}) or {}).get("kappa"),
    }

    l1 = _load_grouped_preset_file("L1", l1_choice)
    l2 = _load_grouped_preset_file("L2", l2_choice)
    l3 = _load_grouped_preset_file("L3", l3_choice)

    merged: dict[str, Any] = {}

    def _merge_sub(section: str, src: dict[str, Any]) -> None:
        block = src.get("data_uncertainty", {}).get(section, {})
        if not isinstance(block, dict) or not block:
            return
        merged.setdefault(section, {}).update(copy.deepcopy(block))

    # L1 owns initial_data and emission_factors
    _merge_sub("initial_data", l1)
    _merge_sub("emission_factors", l1)
    # L2 owns consumption_rates; may also write growth_rates.retire_year
    _merge_sub("consumption_rates", l2)
    l2_gr = l2.get("data_uncertainty", {}).get("growth_rates", {})
    if isinstance(l2_gr, dict) and "retire_year" in l2_gr:
        merged.setdefault("growth_rates", {})["retire_year"] = copy.deepcopy(l2_gr["retire_year"])
    # L3 owns growth_rates (except retire_year which is L2's)
    l3_gr = l3.get("data_uncertainty", {}).get("growth_rates", {})
    for k, v in (l3_gr or {}).items():
        if k == "retire_year":
            continue
        merged.setdefault("growth_rates", {})[k] = copy.deepcopy(v)

    # Region-specific substitutions
    merged = _substitute_region_means(merged, region_means)
    merged = _substitute_region_kappa(merged, region_kappas)

    paper_safe = bool(l1.get("paper_safe", False)) \
        and bool(l2.get("paper_safe", False)) \
        and bool(l3.get("paper_safe", False))

    # Factor-ids that each layer fixes by omission
    fixed_factors: list[str] = []
    if l1_choice == "fixed":
        fixed_factors.extend(["F01", "F02", "F03", "F04", "F05"])
    if l2_choice == "fixed":
        fixed_factors.extend([f"F{n:02d}" for n in range(6, 23)])
    elif l2_choice == "low":
        # l2_low drops per-level axes (S2-01/S2-02)
        fixed_factors.extend(["F06", "F07", "F08", "F12", "F13", "F14", "F21"])
    if l3_choice == "fixed":
        fixed_factors.extend([f"F{n}" for n in (23, 24, 25, 26, 27, 28)])

    return {
        "bundle": (l1_choice, l2_choice, l3_choice),
        "labels": {
            "L1": l1.get("label", f"L1 {l1_choice}"),
            "L2": l2.get("label", f"L2 {l2_choice}"),
            "L3": l3.get("label", f"L3 {l3_choice}"),
        },
        "paper_safe": paper_safe,
        "data_uncertainty": merged,
        "fixed_factors": fixed_factors,
        "notes": {
            "L1": l1.get("notes", {}),
            "L2": l2.get("notes", {}),
            "L3": l3.get("notes", {}),
        },
    }


def apply_grouped_uncertainty_preset(
    cfg: dict[str, Any],
    l1_choice: str,
    l2_choice: str,
    l3_choice: str,
    region: str,
) -> dict[str, Any]:
    """Return a copy of `cfg` with its `data_uncertainty` block replaced by the
    composed (L1, L2, L3) preset bundle for `region`.
    """
    bundle = load_grouped_uncertainty_preset(l1_choice, l2_choice, l3_choice, region)
    new_cfg = copy.deepcopy(cfg)
    new_cfg["data_uncertainty"] = bundle["data_uncertainty"]
    new_cfg["_uncertainty_bundle"] = {
        "L1": l1_choice,
        "L2": l2_choice,
        "L3": l3_choice,
        "paper_safe": bundle["paper_safe"],
    }
    return new_cfg


GROUPED_DEFAULT_BUNDLE = ("fixed", "low", "low")  # decision-meaningful
GROUPED_PAPER_SAFE_BUNDLE = ("medium", "medium", "medium")
GROUPED_EXPLORATORY_BUNDLE = ("fixed", "medium", "high")


def validate_grouped_preset_bundle(l1_choice: str, l2_choice: str, l3_choice: str) -> list[str]:
    """Return a list of human-readable warnings for the bundle.

    Warnings are non-fatal; the panel surfaces them but still allows the
    bundle to be applied. Empty list means no warnings.
    """
    warnings_out: list[str] = []
    l1_choice = l1_choice.lower(); l2_choice = l2_choice.lower(); l3_choice = l3_choice.lower()
    if l3_choice == "high":
        warnings_out.append(
            "L3=high is exploratory: bands exceed 1.5x median past 2030 by construction."
        )
    if l2_choice == "high":
        warnings_out.append(
            "L2=high retains per-level x per-subsystem scale-factor compounding (S2-01/S2-02)."
        )
    if l1_choice == "medium" and l2_choice == "medium" and l3_choice == "medium":
        pass  # paper-safe bundle; no warning
    elif not (l1_choice in ("fixed", "low", "medium") and l2_choice in ("fixed", "low", "medium") and l3_choice in ("fixed", "low", "medium")):
        warnings_out.append(
            "Bundle contains an exploratory preset: not paper-safe; do not cite headline numbers."
        )
    return warnings_out


def load_contribution_experiment() -> pd.DataFrame | None:
    """Load the precomputed layer-contribution experiment CSV for panel use."""
    path = REPO_DIR / "audits" / "uncertainty_governance" / "UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv"
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def load_layer_contribution_experiment() -> pd.DataFrame | None:
    path = REPO_DIR / "audits" / "uncertainty_governance" / "LAYER_CONTRIBUTION_EXPERIMENT.csv"
    if not path.exists():
        # Fallback to the earlier all-layer CSV if the aliased file is absent
        return load_contribution_experiment()
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def load_parameter_contribution_experiment() -> pd.DataFrame | None:
    for name in ("PARAMETER_IMPORTANCE_EXPERIMENT.csv", "PARAMETER_CONTRIBUTION_EXPERIMENT.csv"):
        path = REPO_DIR / "audits" / "uncertainty_governance" / name
        if path.exists():
            try:
                return pd.read_csv(path)
            except Exception:
                continue
    return None


def load_bundle_quantiles(region: str, policy: str, bundle: str) -> pd.DataFrame | None:
    """Load MC quantile CSV produced by scripts/regenerate_default_bundle_quantiles.py.
    `bundle` is e.g. 'default' or 'paper-safe'.
    """
    path = RESULTS_DIR / f"{region}__policy-{policy}__bundle-{bundle}_quantiles.csv"
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        if "Year" in df.columns:
            df = df.set_index("Year")
        return df
    except Exception:
        return None


def bundle_mc_sample_count(region: str, policy: str, bundle: str) -> int | None:
    path = RESULTS_DIR / f"{region}__policy-{policy}__bundle-{bundle}_mc_runs.csv"
    if not path.exists():
        return None
    try:
        return int(pd.read_csv(path, usecols=["run_id"])["run_id"].nunique())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Parameter-level uncertainty registry (primary control abstraction)
# ---------------------------------------------------------------------------

UI_PARAM_PRESETS_DIR = REPO_DIR / "configs" / "ui_parameter_presets"


def load_parameter_registry() -> list[dict[str, Any]]:
    """Return a flat list of every parameter record across all group JSON files.
    Each record keeps its group_id and layer attached. The order is the order
    of appearance in the group files for deterministic panel layout.
    """
    index_path = UI_PARAM_PRESETS_DIR / "_registry_index.json"
    groups: list[str]
    if index_path.exists():
        with open(index_path, encoding="utf-8") as fh:
            groups = json.load(fh).get("groups", [])
    else:
        groups = sorted(
            p.name for p in UI_PARAM_PRESETS_DIR.glob("*.json") if not p.name.startswith("_")
        )

    records: list[dict[str, Any]] = []
    for group_file in groups:
        path = UI_PARAM_PRESETS_DIR / group_file
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as fh:
            group = json.load(fh)
        layer = group.get("layer")
        gid = group.get("group_id", group_file.rsplit(".", 1)[0])
        glabel = group.get("group_label", gid)
        ghelp = group.get("help", "")
        for p in group.get("parameters", []):
            p = dict(p)
            p.setdefault("layer", layer)
            p["group_id"] = gid
            p["group_label"] = glabel
            p["group_help"] = ghelp
            # Propagate group-level semantic_category to each parameter record
            # so the page can read it directly from the record.
            sc = group.get("semantic_category")
            if sc and "semantic_category" not in p:
                p["semantic_category"] = sc
            records.append(p)
    return records


def _resolve_level_spec(spec: Any, region_means: dict[str, float],
                       region_kappas: dict[str, float], parent_key: str | None = None) -> Any:
    """Recursively substitute region sentinels in a level spec."""
    if isinstance(spec, dict):
        out = {}
        for k, v in spec.items():
            if isinstance(v, str):
                if v == "__REGION_MEAN__" and parent_key in region_means and region_means[parent_key] is not None:
                    out[k] = region_means[parent_key]
                elif k == "kappa" and v == "__REGION_KAPPA__" and parent_key in region_kappas and region_kappas[parent_key] is not None:
                    out[k] = region_kappas[parent_key]
                elif k == "kappa" and v == "__REGION_KAPPA_X2__" and parent_key in region_kappas and region_kappas[parent_key] is not None:
                    out[k] = region_kappas[parent_key] * 2.0
                elif v == "region_mean" and parent_key in region_means and region_means[parent_key] is not None:
                    out[k] = region_means[parent_key]
                else:
                    out[k] = v
            else:
                out[k] = _resolve_level_spec(v, region_means, region_kappas, parent_key=k)
        return out
    if isinstance(spec, list):
        return [_resolve_level_spec(x, region_means, region_kappas, parent_key=parent_key) for x in spec]
    return spec


def _set_nested(target: dict, dotted_path: str, value: Any) -> None:
    keys = dotted_path.split(".")
    cur = target
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


def build_data_uncertainty_from_parameter_choices(
    choices: dict[str, str], region: str,
) -> dict[str, Any]:
    """Compose a `data_uncertainty` block from `{param_id: level}` user choices.

    - `fixed` level: the parameter is omitted from the block entirely (the central
      value in the runtime config is used for every Monte Carlo run).
    - any other level: the matching spec is written into the block at the parameter's
      config_path, with region sentinels and `_regions.<region>` overrides applied.
    """
    base = load_base_config(region)
    ini = base.get("data_uncertainty", {}).get("initial_data", {})
    region_means = {
        "f_clean":  (ini.get("f_clean", {}) or {}).get("mean"),
        "ev_share": (ini.get("ev_share", {}) or {}).get("mean"),
    }
    region_kappas = {
        "f_clean":  (ini.get("f_clean", {}) or {}).get("kappa"),
        "ev_share": (ini.get("ev_share", {}) or {}).get("kappa"),
    }
    registry = load_parameter_registry()

    merged: dict[str, Any] = {}
    for rec in registry:
        pid = rec["param_id"]
        level = choices.get(pid, rec.get("default_level", "fixed"))
        if level == "fixed":
            continue
        levels = rec.get("levels", {})
        if level not in levels:
            level = rec.get("default_level", "fixed")
            if level == "fixed" or level not in levels:
                continue
        spec = copy.deepcopy(levels[level])
        if not isinstance(spec, dict) or "dist" not in spec:
            continue
        # Apply region-specific overrides if present; keep the base spec for any key
        # not overridden. Then drop the `_regions` bookkeeping key.
        regions_overrides = spec.pop("_regions", None)
        if isinstance(regions_overrides, dict):
            override = regions_overrides.get(region, {})
            if isinstance(override, dict):
                spec.update(override)
        field = rec["config_path"].rsplit(".", 1)[-1]
        spec = _resolve_level_spec(spec, region_means, region_kappas, parent_key=field)
        _set_nested(merged, rec["config_path"], spec)

    return merged


def apply_parameter_choices(
    cfg: dict[str, Any],
    choices: dict[str, str],
    region: str,
) -> dict[str, Any]:
    new_cfg = copy.deepcopy(cfg)
    new_cfg["data_uncertainty"] = build_data_uncertainty_from_parameter_choices(choices, region)
    # Any parameter set to FIXED must also have its central value written back to the
    # deterministic sections so the run uses the canonical centre; since the scenario
    # already stores those centres, we only need to ensure we did not mutate them.
    new_cfg["_parameter_choices"] = dict(choices)
    return new_cfg


def parameter_default_choices() -> dict[str, str]:
    return {rec["param_id"]: rec.get("default_level", "fixed") for rec in load_parameter_registry()}


def parameter_paper_safe_choices() -> dict[str, str]:
    return {rec["param_id"]: rec.get("paper_safe_level", "medium") for rec in load_parameter_registry()}


def parameter_exploratory_choices() -> dict[str, str]:
    """Exploratory bundle: HIGH on trajectory knobs (F23, F24, F25, F26, F27, F29);
    FIXED on initial state and scale-factor duplicates; LOW on remaining free params."""
    out: dict[str, str] = {}
    for rec in load_parameter_registry():
        pid = rec["param_id"]
        allowed = set(rec.get("allowed_levels", []))
        if pid in {"F23", "F24", "F25", "F26", "F27", "F29"} and "high" in allowed:
            out[pid] = "high"
        elif pid in {"F01", "F02", "F06", "F07", "F08", "F12", "F13", "F14", "F21"}:
            out[pid] = "fixed"
        elif "low" in allowed:
            out[pid] = "low"
        elif "medium" in allowed:
            out[pid] = "medium"
        else:
            out[pid] = "fixed"
    return out


def validate_parameter_registry() -> list[str]:
    """Return a list of human-readable warnings about the registry. Empty list = clean."""
    warnings: list[str] = []
    recs = load_parameter_registry()
    seen_paths: dict[str, str] = {}
    for rec in recs:
        pid = rec["param_id"]
        path = rec.get("config_path")
        if not path:
            warnings.append(f"{pid}: missing config_path")
            continue
        if path in seen_paths:
            warnings.append(f"{pid} and {seen_paths[path]} share config_path {path}")
        seen_paths[path] = pid
        allowed = set(rec.get("allowed_levels", []))
        if rec.get("default_level") not in allowed:
            warnings.append(f"{pid}: default_level {rec.get('default_level')!r} not in allowed_levels {sorted(allowed)}")
        if rec.get("paper_safe_level") not in allowed:
            warnings.append(f"{pid}: paper_safe_level {rec.get('paper_safe_level')!r} not in allowed_levels {sorted(allowed)}")
        for lvl in allowed:
            if lvl == "fixed":
                continue
            spec = rec.get("levels", {}).get(lvl)
            if spec is None:
                warnings.append(f"{pid}: level {lvl!r} listed as allowed but has no spec")
    return warnings
