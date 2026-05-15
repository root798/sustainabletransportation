"""Stage 2: nested Monte Carlo propagation.

Outer loop: freeze a pathway world by sampling every parameter flagged
``epistemic_outer`` in ``config/uncertainty_layers.json``.

Inner loop: at each outer draw, run ``n_inner`` aleatoric realizations:
  - resample the distribution specs flagged ``aleatoric_inner``
  - apply injected per-year multipliers for load and grid realization.

Emits three data products (as DataFrames, also persisted to CSV):

1. ``outer_design.csv`` — one row per outer draw; columns are the sampled
   epistemic parameters. Used as the feature table for sensitivity analysis.

2. ``runs.csv`` — long-format: (outer_draw_id, inner_draw_id, Year,
   <metric columns>). Large.

3. ``outer_summaries.csv`` — per-outer-draw scalar summaries (cumulative,
   peak year, turning year, benchmark-year annual values). Used by the
   surrogate as Y for Sobol.
"""
from __future__ import annotations

import contextlib
import copy
import io
import os
import sys
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import footprint_model as fm  # noqa: E402
from v6_uncertainty_rearchitecture import uncertainty_taxonomy as utax  # noqa: E402


DEFAULT_METRICS = [
    "ATS Total Power (kWh)",
    "ATS Emissions (kg CO2)",
    "EV Fraction",
    "Clean Energy Fraction",
]


@dataclass
class NestedResult:
    outer_design: pd.DataFrame
    runs: pd.DataFrame
    outer_summaries: pd.DataFrame


def _collect_epistemic_values(outer_cfg: Dict[str, Any]) -> Dict[str, float]:
    """Flatten outer-sampled leaf values into a design-matrix row.

    Reads from the already-sampled ``outer_cfg`` (post ``sample_config`` on the
    outer-only distribution block).
    """
    row: Dict[str, float] = {}
    for path in utax.epistemic_paths():
        if path.startswith("__v6_"):
            continue
        parts = path.split(".")
        cursor: Any = outer_cfg
        ok = True
        for part in parts:
            if isinstance(cursor, dict) and part in cursor:
                cursor = cursor[part]
            else:
                ok = False
                break
        if not ok:
            continue
        # Flatten small list-valued parameters (Dirichlet means) into indexed columns.
        if isinstance(cursor, (list, tuple, np.ndarray)):
            arr = np.asarray(cursor, dtype=float).ravel()
            for i, v in enumerate(arr):
                row[f"{path}[{i}]"] = float(v)
        elif isinstance(cursor, (int, float, np.floating, np.integer)):
            row[path] = float(cursor)
        # dicts of scale factors — flatten once more:
        elif isinstance(cursor, dict):
            for subkey, subval in cursor.items():
                if isinstance(subval, (int, float, np.floating, np.integer)):
                    row[f"{path}.{subkey}"] = float(subval)
    return row


def _build_outer_config(base_config: Dict[str, Any], outer_data_uncertainty: Dict[str, Any],
                        rng: np.random.Generator) -> Dict[str, Any]:
    """Sample only the outer partition of data_uncertainty. Returns a frozen
    pathway-world config (still with inner distribution specs intact in
    ``data_uncertainty`` so the inner loop can sample them).
    """
    cfg = copy.deepcopy(base_config)
    # Temporarily replace data_uncertainty with the outer-only sub-block for sampling.
    saved_du = cfg.get("data_uncertainty", {})
    cfg["data_uncertainty"] = outer_data_uncertainty
    sampled = fm.sample_config(cfg, rng, trajectory_copula=False)
    # Put the *original* data_uncertainty back so the inner loop still sees
    # inner specs.
    sampled["data_uncertainty"] = saved_du
    return sampled


def _build_inner_config(outer_cfg: Dict[str, Any], inner_data_uncertainty: Dict[str, Any],
                        rng: np.random.Generator) -> Dict[str, Any]:
    """At a frozen outer world, sample inner-partition distribution specs."""
    cfg = copy.deepcopy(outer_cfg)
    saved_du = cfg.get("data_uncertainty", {})
    cfg["data_uncertainty"] = inner_data_uncertainty
    sampled = fm.sample_config(cfg, rng, trajectory_copula=False)
    sampled["data_uncertainty"] = saved_du
    return sampled


def _apply_aleatoric_realizations(df: pd.DataFrame,
                                  rng: np.random.Generator,
                                  load_sigma: float,
                                  grid_sigma: float) -> pd.DataFrame:
    """Multiply annual energy and emissions by per-year realizations.

    Implemented post-simulation as a correlated-with-itself-across-time
    realization: one Normal(1, load_sigma) per year on the load, and one
    Normal(1, grid_sigma) additional on emissions.
    """
    out = df.copy()
    n = len(out)
    load_mult = rng.normal(loc=1.0, scale=load_sigma, size=n)
    grid_mult = rng.normal(loc=1.0, scale=grid_sigma, size=n)
    # Guard against negative realizations (long-tail of Normal tail is unphysical here).
    load_mult = np.clip(load_mult, 0.5, 1.5)
    grid_mult = np.clip(grid_mult, 0.5, 1.5)

    for col in ["ATS Total Power (kWh)"]:
        if col in out.columns:
            out[col] = out[col].to_numpy() * load_mult
    for col in ["ATS Emissions (kg CO2)"]:
        if col in out.columns:
            out[col] = out[col].to_numpy() * load_mult * grid_mult
    return out


def _run_single(cfg: Dict[str, Any], years: int) -> pd.DataFrame:
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


def run_nested_mc(
    region: str,
    policy: str = "baseline",
    n_outer: Optional[int] = None,
    n_inner: Optional[int] = None,
    years: int = 68,
    seed_outer: Optional[int] = None,
    seed_inner: Optional[int] = None,
    metrics: Optional[List[str]] = None,
    verbose: bool = False,
) -> NestedResult:
    """Run the full outer × inner nested MC for one (region, policy)."""
    defaults = utax.defaults()
    n_outer = int(n_outer or defaults.get("n_outer", 40))
    n_inner = int(n_inner or defaults.get("n_inner", 20))
    seed_outer = int(seed_outer if seed_outer is not None else defaults.get("seed_outer", 42))
    seed_inner = int(seed_inner if seed_inner is not None else defaults.get("seed_inner", 2025))
    load_sigma = float(defaults.get("annual_load_sigma", 0.02))
    grid_sigma = float(defaults.get("annual_grid_sigma", 0.015))
    metrics_requested = list(metrics or DEFAULT_METRICS)

    base = fm.load_config(region)
    policy_patches = base.get("policy_scenarios", {})
    if policy and policy in policy_patches:
        base = fm._deep_merge(base, policy_patches[policy])

    du = base.get("data_uncertainty", {})
    outer_du, inner_du = utax.partition_data_uncertainty(du)
    unknowns = utax.unknown_path_report(du)
    if unknowns and verbose:
        print(f"[v6/nested_mc] unknown paths routed to outer: {unknowns}", file=sys.stderr)

    ss = np.random.SeedSequence([seed_outer, hash(region) & 0xFFFF, hash(policy) & 0xFFFF])
    outer_seeds = ss.spawn(n_outer)

    outer_design_rows: List[Dict[str, Any]] = []
    run_frames: List[pd.DataFrame] = []
    outer_summaries: List[Dict[str, Any]] = []

    benchmark_ys = utax.benchmark_years()

    for o, outer_ss in enumerate(outer_seeds):
        rng_outer = np.random.default_rng(outer_ss)
        outer_cfg = _build_outer_config(base, outer_du, rng_outer)
        outer_row = _collect_epistemic_values(outer_cfg)
        outer_row["outer_draw_id"] = o
        outer_design_rows.append(outer_row)

        inner_ss = np.random.SeedSequence([seed_inner, o])
        inner_seeds = inner_ss.spawn(n_inner)

        # per-outer accumulators for scalar summaries
        cum_emis = np.zeros(n_inner, dtype=float)
        peak_yr = np.zeros(n_inner, dtype=float)
        peak_em = np.zeros(n_inner, dtype=float)
        turn_yr = np.zeros(n_inner, dtype=float)
        bench_annual: Dict[int, List[float]] = {y: [] for y in benchmark_ys}

        for i, inner_s in enumerate(inner_seeds):
            rng_inner = np.random.default_rng(inner_s)
            inner_cfg = _build_inner_config(outer_cfg, inner_du, rng_inner)
            df = _run_single(inner_cfg, years=years)
            df = _apply_aleatoric_realizations(df, rng_inner, load_sigma, grid_sigma)

            # persist a slim version (only requested metrics + Year)
            cols_in = [c for c in metrics_requested if c in df.columns]
            slim = df[["Year"] + cols_in].copy()
            slim["outer_draw_id"] = o
            slim["inner_draw_id"] = i
            run_frames.append(slim)

            m = fm.compute_scalar_metrics(df)
            cum_emis[i] = m.get("cumulative_emissions", 0.0)
            peak_yr[i] = m.get("peak_year", np.nan)
            peak_em[i] = m.get("peak_emissions", 0.0)
            turn_yr[i] = m.get("turning_year", np.nan)

            for y in benchmark_ys:
                if "Year" in df.columns and (df["Year"] == y).any():
                    row = df[df["Year"] == y].iloc[0]
                    bench_annual[y].append(float(row.get("ATS Emissions (kg CO2)", np.nan)))

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            summary = {
                "outer_draw_id": o,
                "region": region,
                "policy": policy,
                "cum_emis_mean": float(np.nanmean(cum_emis)),
                "cum_emis_p50": float(np.nanmedian(cum_emis)),
                "cum_emis_p05": float(np.nanquantile(cum_emis, 0.05)),
                "cum_emis_p95": float(np.nanquantile(cum_emis, 0.95)),
                "peak_year_mean": float(np.nanmean(peak_yr)),
                "peak_emis_mean": float(np.nanmean(peak_em)),
                "turning_year_mean": float(np.nanmean(turn_yr)),
            }
        for y in benchmark_ys:
            vals = np.asarray(bench_annual[y], dtype=float)
            if len(vals):
                summary[f"annual_emis_{y}_p50"] = float(np.nanmedian(vals))
                summary[f"annual_emis_{y}_mean"] = float(np.nanmean(vals))
        outer_summaries.append(summary)

        if verbose and (o + 1) % 10 == 0:
            print(f"[v6/nested_mc] {region}/{policy} outer {o+1}/{n_outer}", file=sys.stderr)

    outer_design_df = pd.DataFrame(outer_design_rows)
    runs_df = pd.concat(run_frames, ignore_index=True) if run_frames else pd.DataFrame()
    summaries_df = pd.DataFrame(outer_summaries)

    return NestedResult(outer_design=outer_design_df, runs=runs_df, outer_summaries=summaries_df)


def save_result(result: NestedResult, region: str, policy: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    prefix = f"{region}__{policy}"
    result.outer_design.to_csv(os.path.join(out_dir, f"{prefix}__outer_design.csv"), index=False)
    result.outer_summaries.to_csv(os.path.join(out_dir, f"{prefix}__outer_summaries.csv"), index=False)
    result.runs.to_csv(os.path.join(out_dir, f"{prefix}__runs.csv"), index=False)


__all__ = ["run_nested_mc", "save_result", "NestedResult", "DEFAULT_METRICS"]
