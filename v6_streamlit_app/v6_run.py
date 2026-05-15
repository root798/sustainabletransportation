"""v6 simulator wrapper.

Thin layer around v5's ``footprint_model`` + the v6 policy-scenario apply.
Used by:
  * the bundle generator (``scripts/build_v6_bundles.py``)
  * the dashboard pages 04 (Distribution Overlay), 05 (Avoided vs Residual)

Every call goes through ``footprint_model.TransportModel.run_simulation`` —
no fork of the simulator.
"""
from __future__ import annotations

import contextlib
import copy
import io
import os
import sys
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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
    get_scenario,
)


def _silenced_run(cfg: Dict[str, Any], years: int) -> pd.DataFrame:
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


def deterministic_scenario_run(scenario_id: str, years: int = 68) -> pd.DataFrame:
    """Single deterministic run with a scenario's fixed_overrides applied
    and every distribution spec replaced by central value."""
    sc = get_scenario(scenario_id)
    cfg = fm.load_config(sc["region"])
    cfg = apply_scenario(cfg, scenario_id)

    # central values for every remaining dist spec
    def _strip(node: Any) -> Any:
        if isinstance(node, dict):
            if "dist" in node:
                d = node["dist"]
                if d == "triangular":
                    return node.get("mode", node.get("mean"))
                if d in ("normal", "truncated_normal"):
                    return node.get("mean")
                if d == "lognormal":
                    return node.get("mean", float(np.exp(node.get("mu", 0.0) + 0.5 * node.get("sigma", 0.0) ** 2)))
                if d == "beta":
                    return node.get("mean", 0.5)
                if d == "uniform":
                    return 0.5 * (node.get("low", 0.0) + node.get("high", 1.0))
                if d == "dirichlet":
                    a = node.get("alpha") or []
                    s = float(sum(a)) if a else 0.0
                    return [x / s for x in a] if s > 0 else a
                return node
            return {k: _strip(v) for k, v in node.items()}
        if isinstance(node, list):
            return [_strip(x) for x in node]
        return node

    for sect in ["initial_data", "growth_rates", "consumption_rates", "emission_factors"]:
        if sect in cfg:
            cfg[sect] = _strip(cfg[sect])
    return _silenced_run(cfg, years=years)


def mc_scenario_run(scenario_id: str, n_runs: int = 80, years: int = 68,
                    seed: int = 42, verbose: bool = False) -> Dict[str, Any]:
    """Monte Carlo within a scenario.

    Resamples every distribution spec that survives ``apply_scenario``
    (so only L1+L2 aleatoric + F27 hardware doubling + F31 fleet envelope
    in the data_uncertainty.growth_rates block). Also draws v6 epistemic
    extras (F29 gas price multiplier, F30 deployment lag) per run and
    stores them in the per-run record.
    """
    sc = get_scenario(scenario_id)
    region = sc["region"]
    base = fm.load_config(region)
    base = apply_scenario(base, scenario_id)
    exog = exogenous_epistemic_specs()

    ss = np.random.SeedSequence([seed, hash(scenario_id) & 0xFFFF])
    seeds = ss.spawn(n_runs)

    runs: List[pd.DataFrame] = []
    extras_rows: List[Dict[str, Any]] = []
    for i, sd in enumerate(seeds):
        rng = np.random.default_rng(sd)
        # Sample everything in data_uncertainty (which still contains L1+L2 +
        # the surviving growth_rates entries: efficiency_doubling, total_car_increase, retire_year).
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cfg = fm.sample_config(base, rng, trajectory_copula=False)

        # v6 exogenous extras
        v6 = {}
        for f, spec in exog.items():
            if f.startswith("_"):
                continue
            d = spec.get("dist")
            if d == "triangular":
                v6[f] = float(rng.triangular(spec["low"], spec["mode"], spec["high"]))
            elif d == "truncated_normal":
                lo, hi = spec.get("min", -np.inf), spec.get("max", np.inf)
                mn, sd_ = spec.get("mean", 0.0), spec.get("sd", spec.get("sigma", 1.0))
                v = float(np.clip(rng.normal(mn, sd_), lo, hi))
                v6[f] = v
        # Apply F27 / F31 to cfg
        if "F27" in v6:
            cfg["growth_rates"]["efficiency_doubling"] = v6["F27"]
        if "F31" in v6:
            cfg["growth_rates"]["total_car_increase"] = v6["F31"]
        # F29, F30 are recorded but not yet wired into the simulator's equations
        # (paper-grade rewiring is documented as an open item; for v6 demo they
        # are tracked in the per-run extras and surfaced on page 06 of the dash).

        df = _silenced_run(cfg, years=years)
        df["run_id"] = i
        runs.append(df)
        extras_rows.append({"run_id": i, "scenario_id": scenario_id, **v6})
        if verbose and (i + 1) % 20 == 0:
            print(f"[v6/mc] {scenario_id} {i+1}/{n_runs}", file=sys.stderr)

    runs_df = pd.concat(runs, ignore_index=True)
    extras_df = pd.DataFrame(extras_rows)
    return {
        "runs": runs_df,
        "extras": extras_df,
        "scenario_id": scenario_id,
        "region": region,
        "n_runs": n_runs,
        "years": years,
    }


def quantile_summary(runs_df: pd.DataFrame,
                     metrics: Optional[List[str]] = None,
                     quantiles: List[float] = (0.05, 0.5, 0.95)) -> pd.DataFrame:
    metrics = metrics or [
        "ATS Total Power (kWh)", "ATS Emissions (kg CO2)",
        "EV Fraction", "Clean Energy Fraction",
        "ECAV Sensing Power (kWh)", "ECAV Computing Power (kWh)",
        "ECAV Communication Power (kWh)",
        "STI Sensing Power (kWh)", "STI Computing Power (kWh)",
        "STI Communication Power (kWh)",
        "ECAV Sensing Emissions (kg CO2)", "ECAV Computing Emissions (kg CO2)",
        "ECAV Communication Emissions (kg CO2)",
        "STI Sensing Emissions (kg CO2)", "STI Computing Emissions (kg CO2)",
        "STI Communication Emissions (kg CO2)",
    ]
    out = {"Year": []}
    for m in metrics:
        for q in quantiles:
            out[f"{m}_p{int(round(q*100)):02d}"] = []
    years = sorted(runs_df["Year"].unique())
    for y in years:
        out["Year"].append(int(y))
        for m in metrics:
            if m not in runs_df.columns:
                for q in quantiles:
                    out[f"{m}_p{int(round(q*100)):02d}"].append(np.nan)
                continue
            vals = runs_df.loc[runs_df["Year"] == y, m].dropna().to_numpy()
            for q in quantiles:
                out[f"{m}_p{int(round(q*100)):02d}"].append(
                    float(np.quantile(vals, q)) if len(vals) else np.nan
                )
    return pd.DataFrame(out)


def metrics_per_run(runs_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, float]] = []
    for rid, sub in runs_df.groupby("run_id"):
        m = fm.compute_scalar_metrics(sub.reset_index(drop=True))
        m["run_id"] = int(rid)
        # 2050 / 2075 annual emissions
        for y in [2030, 2035, 2045, 2050, 2055, 2075]:
            row = sub.loc[sub["Year"] == y]
            if not row.empty:
                m[f"annual_emis_{y}"] = float(row["ATS Emissions (kg CO2)"].iloc[0])
        m["cumulative_emissions_2050"] = float(sub.loc[sub["Year"] <= 2050,
                                                        "ATS Emissions (kg CO2)"].sum())
        rows.append(m)
    return pd.DataFrame(rows)


__all__ = [
    "deterministic_scenario_run",
    "mc_scenario_run",
    "quantile_summary",
    "metrics_per_run",
]
