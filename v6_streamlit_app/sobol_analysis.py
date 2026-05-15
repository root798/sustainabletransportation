"""v6 Sobol harness.

Wraps the v5 footprint_model simulator with Saltelli sampling to produce
total-order (S_T), first-order (S_1), and second-order (S_ij) Sobol indices
for a chosen target quantity under a chosen policy scenario.

Falls back to a random-forest feature-importance ranking if SALib is not
installed; the dashboard label says so honestly.
"""
from __future__ import annotations

import contextlib
import copy
import io
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import footprint_model as fm  # noqa: E402
from scenario_definitions import (  # noqa: E402
    apply_scenario,
    exogenous_epistemic_specs,
    metadata_for,
)

try:
    from SALib.sample import saltelli  # type: ignore
    from SALib.analyze import sobol  # type: ignore
    _HAS_SALIB = True
except Exception:  # pragma: no cover
    _HAS_SALIB = False

try:
    from sklearn.ensemble import RandomForestRegressor
    _HAS_SKLEARN = True
except Exception:  # pragma: no cover
    _HAS_SKLEARN = False


# ---------------------------------------------------------------------------
# Sample-space construction
# ---------------------------------------------------------------------------
def _flatten_aleatoric_specs(base_cfg: Dict[str, Any],
                             excludes: List[str]) -> Dict[str, Dict[str, Any]]:
    """Return {dotted_path: dist_spec} for every L1+L2 aleatoric prior in
    ``data_uncertainty``. Skips paths in ``excludes`` (the policy-fixed F23-F26).

    Compound-distribution containers (Dirichlet, ecav_scale_factors) are
    descended into; their leaf scalars are exposed separately.
    """
    flat: Dict[str, Dict[str, Any]] = {}
    du = base_cfg.get("data_uncertainty", {})

    def _walk(node: Any, prefix: str) -> None:
        if isinstance(node, dict):
            if "dist" in node:
                if prefix not in excludes and not any(prefix.startswith(p + ".") for p in excludes):
                    flat[prefix] = copy.deepcopy(node)
                return
            for k, v in node.items():
                key = f"{prefix}.{k}" if prefix else k
                _walk(v, key)

    _walk(du, "")
    return flat


def _spec_to_bounds(spec: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """Approximate (low, high) bounds for a distribution spec, used by Saltelli."""
    dist = spec.get("dist")
    if dist == "triangular":
        return float(spec["low"]), float(spec["high"])
    if dist in ("normal", "truncated_normal"):
        mn = spec.get("min")
        mx = spec.get("max")
        mean = float(spec.get("mean", 0.0))
        sd = float(spec.get("sd", spec.get("sigma", 1.0)))
        if mn is None:
            mn = mean - 3 * sd
        if mx is None:
            mx = mean + 3 * sd
        return float(mn), float(mx)
    if dist == "lognormal":
        mean = float(spec.get("mean", 1.0))
        sigma = float(spec.get("sigma", 0.2))
        # ~ +/- 2.5 sigma in log space, multiplicative
        return float(mean * np.exp(-2.5 * sigma)), float(mean * np.exp(2.5 * sigma))
    if dist == "beta":
        mean = float(spec.get("mean", 0.5))
        kappa = float(spec.get("kappa", 80))
        # 95% credible interval approx via beta ppf
        a = mean * kappa
        b = (1 - mean) * kappa
        try:
            from scipy.stats import beta as beta_dist  # type: ignore
            return float(beta_dist.ppf(0.025, a, b)), float(beta_dist.ppf(0.975, a, b))
        except Exception:
            return float(max(0.0, mean - 0.05)), float(min(1.0, mean + 0.05))
    if dist == "uniform":
        return float(spec.get("low", 0.0)), float(spec.get("high", 1.0))
    if dist == "dirichlet":
        # Vector-valued; not exposed as a scalar to the Saltelli design.
        # Held at its central value during the Sobol pass.
        return None
    return None


# ---------------------------------------------------------------------------
# v6 epistemic sampling helpers
# ---------------------------------------------------------------------------
def _sample_v6_epistemic(rng: np.random.Generator) -> Dict[str, float]:
    """Sample F27, F29, F30, F31. Returns dict keyed by F-number."""
    out: Dict[str, float] = {}
    specs = exogenous_epistemic_specs()
    for f, spec in specs.items():
        if f.startswith("_"):
            continue
        d = spec.get("dist")
        if d == "triangular":
            out[f] = float(rng.triangular(spec["low"], spec["mode"], spec["high"]))
        elif d == "truncated_normal":
            lo = spec.get("min", -np.inf)
            hi = spec.get("max", np.inf)
            mean = spec.get("mean", 0.0)
            sd = spec.get("sd", spec.get("sigma", 1.0))
            for _ in range(50):
                v = rng.normal(mean, sd)
                if lo <= v <= hi:
                    out[f] = float(v)
                    break
            else:
                out[f] = float(np.clip(rng.normal(mean, sd), lo, hi))
    return out


# ---------------------------------------------------------------------------
# Simulator wrapper
# ---------------------------------------------------------------------------
def _silence(callable_: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*a, **kw):
        with contextlib.redirect_stdout(io.StringIO()):
            return callable_(*a, **kw)
    return wrapper


def _run_one(cfg: Dict[str, Any], years: int) -> pd.DataFrame:
    variant = fm._parse_model_variant(cfg.get("model_variants", {}))
    energy_model = fm.build_energy_model(variant, cfg["consumption_rates"])
    model = fm.TransportModel(
        initial_data=cfg["initial_data"],
        growth_rates=cfg["growth_rates"],
        consumption_rates=cfg["consumption_rates"],
        emission_factors=cfg["emission_factors"],
        model_variants=variant,
        energy_model=energy_model,
    )
    with contextlib.redirect_stdout(io.StringIO()):
        model.run_simulation(years=years)
    return pd.DataFrame(model.results)


def _target_value(df: pd.DataFrame, target: str) -> float:
    if target == "annual_emissions_2050":
        s = df.loc[df["Year"] == 2050, "ATS Emissions (kg CO2)"]
        return float(s.iloc[0]) if not s.empty else float("nan")
    if target == "cumulative_emissions_2050":
        s = df.loc[df["Year"] <= 2050, "ATS Emissions (kg CO2)"]
        return float(s.sum())
    if target == "peak_emissions":
        return float(df["ATS Emissions (kg CO2)"].max())
    if target == "turning_year":
        return float(fm.compute_scalar_metrics(df).get("turning_year", float("nan")))
    if target == "annual_emissions_2075":
        s = df.loc[df["Year"] == 2075, "ATS Emissions (kg CO2)"]
        return float(s.iloc[0]) if not s.empty else float("nan")
    if target == "cumulative_emissions_2075":
        return float(df["ATS Emissions (kg CO2)"].sum())
    return float("nan")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
TARGETS = [
    "annual_emissions_2050",
    "cumulative_emissions_2050",
    "annual_emissions_2075",
    "cumulative_emissions_2075",
    "peak_emissions",
    "turning_year",
]


@dataclass
class SobolResult:
    method: str                # "sobol" or "rf_importance"
    feature_names: List[str]
    feature_classes: List[str]  # "aleatoric" / "epistemic"
    feature_layers: List[str]   # "L1" / "L2" / "L3"
    S1: Optional[np.ndarray] = None
    ST: Optional[np.ndarray] = None
    S2: Optional[np.ndarray] = None  # square (n,n); only filled if calc_second_order
    rf_importance: Optional[np.ndarray] = None
    n_samples: int = 0
    elapsed_sec: float = 0.0


def _build_problem(base_cfg: Dict[str, Any],
                   excludes: List[str]) -> Tuple[List[str], List[Tuple[float, float]],
                                                  List[str], List[str], List[Optional[Dict[str, Any]]]]:
    """Construct (names, bounds, classes, layers, specs) for Saltelli sampling."""
    aleatoric_flat = _flatten_aleatoric_specs(base_cfg, excludes)
    names: List[str] = []
    bounds: List[Tuple[float, float]] = []
    classes: List[str] = []
    layers: List[str] = []
    specs: List[Optional[Dict[str, Any]]] = []
    # aleatoric L1+L2
    for path, spec in aleatoric_flat.items():
        b = _spec_to_bounds(spec)
        if b is None:
            continue
        names.append(path)
        bounds.append(b)
        classes.append("aleatoric")
        # crude layer guess: emission_factors -> L1; everything else -> L2
        layers.append("L1" if path.startswith("emission_factors.") or path.startswith("initial_data.") else "L2")
        specs.append(copy.deepcopy(spec))

    # exogenous epistemic — F27, F29, F30, F31
    exog = exogenous_epistemic_specs()
    for f, spec in exog.items():
        if f.startswith("_"):
            continue
        b = _spec_to_bounds(spec)
        if b is None:
            continue
        names.append(f)            # named by F-number for these
        bounds.append(b)
        classes.append("epistemic")
        layers.append("L3")
        specs.append(copy.deepcopy(spec))
    return names, bounds, classes, layers, specs


def _apply_named_value_to_cfg(cfg: Dict[str, Any], path_or_f: str, value: float,
                              spec: Optional[Dict[str, Any]] = None) -> None:
    """Write a sampled value into a config copy.

    Handles dotted aleatoric paths (rewriting their distribution spec to a
    point mass) and v6 F-numbered exogenous epistemic parameters (F27 -> efficiency_doubling;
    F29 -> recorded under cfg.__v6__; F30 -> recorded; F31 -> total_car_increase).
    """
    if path_or_f.startswith("F"):
        # exogenous epistemic
        if path_or_f == "F27":
            cfg.setdefault("growth_rates", {})["efficiency_doubling"] = float(value)
        elif path_or_f == "F31":
            cfg.setdefault("growth_rates", {})["total_car_increase"] = float(value)
        else:
            cfg.setdefault("__v6__", {})[path_or_f] = float(value)
        return

    keys = path_or_f.split(".")
    cursor: Any = cfg
    for k in keys[:-1]:
        if k not in cursor or not isinstance(cursor[k], dict):
            cursor[k] = {}
        cursor = cursor[k]
    # leaf is a scalar OR currently a dist spec — overwrite as scalar.
    # The simulator's resolve_distributions step will then leave the scalar
    # alone because it is not a dict-with-'dist'.
    cursor[keys[-1]] = float(value)
    # Also strip the matching dist spec under data_uncertainty if present, so
    # sample_config does NOT later re-randomize the scalar we just wrote.
    du = cfg.get("data_uncertainty", {})
    cursor2: Any = du
    ok = True
    for k in keys[:-1]:
        if isinstance(cursor2, dict) and k in cursor2:
            cursor2 = cursor2[k]
        else:
            ok = False
            break
    if ok and isinstance(cursor2, dict) and keys[-1] in cursor2:
        del cursor2[keys[-1]]


def run_sobol(region: str, scenario_id: str, target: str,
              n_base: int = 128, years: int = 68,
              seed: int = 42,
              calc_second_order: bool = True,
              verbose: bool = False) -> SobolResult:
    """Run a (Saltelli + Sobol) decomposition for a target under a scenario.

    Falls back to a random-forest importance ranking when SALib is missing.
    """
    base_cfg = fm.load_config(region)
    base_cfg = apply_scenario(base_cfg, scenario_id)

    excludes = ["growth_rates.cav", "growth_rates.sti",
                "growth_rates.ev", "growth_rates.clean_energy"]
    names, bounds, classes, layers, specs = _build_problem(base_cfg, excludes)
    if not names:
        raise RuntimeError("No samplable parameters found.")

    if _HAS_SALIB:
        problem = {"num_vars": len(names), "names": names, "bounds": bounds}
        t0 = time.time()
        samples = saltelli.sample(problem, n_base, calc_second_order=calc_second_order)
        Y = np.zeros(samples.shape[0], dtype=float)
        for i, row in enumerate(samples):
            cfg = copy.deepcopy(base_cfg)
            for name, val, spec in zip(names, row, specs):
                _apply_named_value_to_cfg(cfg, name, float(val), spec)
            df = _run_one(cfg, years=years)
            Y[i] = _target_value(df, target)
            if verbose and (i + 1) % 200 == 0:
                print(f"[v6/sobol] {i+1}/{len(samples)}", file=sys.stderr)
        Si = sobol.analyze(problem, Y, calc_second_order=calc_second_order, print_to_console=False)
        elapsed = time.time() - t0
        result = SobolResult(
            method="sobol",
            feature_names=names,
            feature_classes=classes,
            feature_layers=layers,
            S1=np.asarray(Si.get("S1", np.zeros(len(names)))),
            ST=np.asarray(Si.get("ST", np.zeros(len(names)))),
            S2=np.asarray(Si.get("S2")) if calc_second_order and "S2" in Si else None,
            n_samples=int(samples.shape[0]),
            elapsed_sec=elapsed,
        )
        return result

    # Fallback: random-forest importance on a Latin-hypercube-style design
    if not _HAS_SKLEARN:
        raise RuntimeError("Neither SALib nor scikit-learn is available.")

    rng = np.random.default_rng(seed)
    n = max(n_base * 8, 256)
    X = np.zeros((n, len(names)), dtype=float)
    for j, (lo, hi) in enumerate(bounds):
        X[:, j] = rng.uniform(lo, hi, size=n)
    Y = np.zeros(n, dtype=float)
    t0 = time.time()
    for i in range(n):
        cfg = copy.deepcopy(base_cfg)
        for j, name in enumerate(names):
            _apply_named_value_to_cfg(cfg, name, float(X[i, j]), specs[j])
        df = _run_one(cfg, years=years)
        Y[i] = _target_value(df, target)
        if verbose and (i + 1) % 100 == 0:
            print(f"[v6/sobol-fallback] {i+1}/{n}", file=sys.stderr)
    rf = RandomForestRegressor(n_estimators=400, random_state=seed, n_jobs=1)
    rf.fit(X, Y)
    elapsed = time.time() - t0
    return SobolResult(
        method="rf_importance",
        feature_names=names,
        feature_classes=classes,
        feature_layers=layers,
        rf_importance=rf.feature_importances_,
        n_samples=int(n),
        elapsed_sec=elapsed,
    )


def ranking_dataframe(result: SobolResult) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for i, name in enumerate(result.feature_names):
        meta = metadata_for(name) if name.startswith("F") else {}
        rows.append({
            "feature": name,
            "short_label": meta.get("short_label", name),
            "class": result.feature_classes[i],
            "layer": result.feature_layers[i],
            "S1":   float(result.S1[i]) if result.S1 is not None else None,
            "ST":   float(result.ST[i]) if result.ST is not None else None,
            "rf":   float(result.rf_importance[i]) if result.rf_importance is not None else None,
        })
    return pd.DataFrame(rows)


__all__ = [
    "TARGETS",
    "SobolResult",
    "run_sobol",
    "ranking_dataframe",
    "_HAS_SALIB",
    "_HAS_SKLEARN",
]
