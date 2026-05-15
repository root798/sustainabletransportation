"""Uncertainty-contribution experiment for CLEAR-ATS.

Runs selective-layer Monte Carlo on the paper-safe regions (California, Ohio)
under the baseline policy to quantify how each uncertainty layer contributes
to the p95-p05 width and to the interpretation boundary year.

Writes:
  audits/uncertainty_governance/UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv
"""

from __future__ import annotations

import copy
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from footprint_model import (
    TransportModel,
    build_energy_model,
    compute_interpretation_boundary,
    compute_quantile_summary,
    load_config,
    sample_config,
    _deep_merge,
    _parse_model_variant,
)

OUT_CSV = REPO / "audits" / "uncertainty_governance" / "UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

REGIONS = ["california", "ohio"]
POLICY = "baseline"
METRIC = "ATS Emissions (kg CO2)"
CHECK_YEARS = [2030, 2050, 2075]
MC_RUNS = 150
SEED = 42

# Layer map: which top-level keys inside data_uncertainty belong to each layer.
# retire_year lives under growth_rates but is classified as L2 in the registry.
LAYER_SPECS = {
    "L1": {"initial_data": "all", "emission_factors": "all"},
    "L2": {"consumption_rates": "all", "growth_rates": ["retire_year"]},
    "L3": {"growth_rates": ["cav", "sti", "ev", "clean_energy", "efficiency_doubling", "total_car_increase"]},
}

SCENARIOS = [
    ("baseline_deterministic", set()),
    ("L1_only", {"L1"}),
    ("L2_only", {"L2"}),
    ("L3_only", {"L3"}),
    ("L1_L2", {"L1", "L2"}),
    ("L1_L3", {"L1", "L3"}),
    ("L2_L3", {"L2", "L3"}),
    ("all_free_L1_L2_L3", {"L1", "L2", "L3"}),
    # Top individual factors inside L2 and L3 -- isolate the single largest drivers
    ("L2_only_scale_factors_only", {"L2_scalefactors_only"}),
    ("L3_only_cav_sti_targets_only", {"L3_cavstitargets_only"}),
    ("L3_only_growth_exponents_only", {"L3_growthexponents_only"}),
]


def build_masked_data_uncertainty(full_du: dict, active_layers: set) -> dict:
    """Return a copy of `full_du` keeping only the priors that match `active_layers`."""
    keep = {}

    def include(layer_code: str) -> bool:
        return layer_code in active_layers

    # canonical layer codes
    if include("L1"):
        if "initial_data" in full_du:
            keep["initial_data"] = copy.deepcopy(full_du["initial_data"])
        if "emission_factors" in full_du:
            keep["emission_factors"] = copy.deepcopy(full_du["emission_factors"])

    if include("L2"):
        if "consumption_rates" in full_du:
            keep["consumption_rates"] = copy.deepcopy(full_du["consumption_rates"])
        gr_src = full_du.get("growth_rates", {})
        if "retire_year" in gr_src:
            keep.setdefault("growth_rates", {})["retire_year"] = copy.deepcopy(gr_src["retire_year"])

    if include("L3"):
        gr_src = full_du.get("growth_rates", {})
        l3_keys = ["cav", "sti", "ev", "clean_energy", "efficiency_doubling", "total_car_increase"]
        for k in l3_keys:
            if k in gr_src:
                keep.setdefault("growth_rates", {})[k] = copy.deepcopy(gr_src[k])

    # Narrow drill-downs for top-factor isolation.
    if "L2_scalefactors_only" in active_layers:
        cr_src = full_du.get("consumption_rates", {})
        sub = {}
        for k in ("ecav_scale_factors", "sti_scale_factors"):
            if k in cr_src:
                sub[k] = copy.deepcopy(cr_src[k])
        if sub:
            keep["consumption_rates"] = sub

    if "L3_cavstitargets_only" in active_layers:
        gr_src = full_du.get("growth_rates", {})
        sub = {}
        for k in ("cav", "sti"):
            if k in gr_src:
                sub[k] = copy.deepcopy(gr_src[k])
        if sub:
            keep["growth_rates"] = sub

    if "L3_growthexponents_only" in active_layers:
        gr_src = full_du.get("growth_rates", {})
        sub = {}
        for k in ("ev", "clean_energy", "efficiency_doubling"):
            if k in gr_src:
                sub[k] = copy.deepcopy(gr_src[k])
        if sub:
            keep["growth_rates"] = sub

    return keep


def run_single(config: dict, years: int = 68) -> list[dict]:
    # IMPORTANT: do NOT pass a pre-built energy_model; TransportModel builds one
    # from the post-scale-factor consumption rates. Passing a pre-built model
    # bypasses the L2 scale-factor application for sensing/computing/communication.
    model = TransportModel(
        initial_data=config["initial_data"],
        growth_rates=config["growth_rates"],
        consumption_rates=config["consumption_rates"],
        emission_factors=config["emission_factors"],
        model_variants=config.get("model_variants"),
    )
    model.run_simulation(years=years)
    return model.results


def run_ensemble(base_config: dict, active_layers: set, mc_runs: int, seed: int) -> pd.DataFrame | None:
    if not active_layers:
        rows = run_single(copy.deepcopy(base_config))
        return compute_quantile_summary([rows], quantiles=[0.05, 0.5, 0.95])
    cfg_template = copy.deepcopy(base_config)
    full_du = cfg_template.get("data_uncertainty", {})
    cfg_template["data_uncertainty"] = build_masked_data_uncertainty(full_du, active_layers)
    rng = np.random.default_rng(seed)
    runs = []
    for _ in range(mc_runs):
        sampled = sample_config(cfg_template, rng)
        runs.append(run_single(sampled))
    if not runs:
        return None
    return compute_quantile_summary(runs, quantiles=[0.05, 0.5, 0.95])


def width_metrics(q_df: pd.DataFrame, metric: str, year: int) -> dict:
    # Accepts either 'Year' column or index
    if "Year" in q_df.columns:
        row = q_df.loc[q_df["Year"] == year]
    else:
        row = q_df.loc[q_df.index == year]
    if row.empty:
        return {"p05": np.nan, "p50": np.nan, "p95": np.nan, "width": np.nan, "width_over_median": np.nan}
    p05 = float(row[f"{metric}_p05"].iloc[0])
    p50 = float(row[f"{metric}_p50"].iloc[0])
    p95 = float(row[f"{metric}_p95"].iloc[0])
    width = p95 - p05
    wom = width / abs(p50) if p50 else np.nan
    return {"p05": p05, "p50": p50, "p95": p95, "width": width, "width_over_median": wom}


def deterministic_row(base_config: dict, years: int, metric: str) -> dict:
    rows = run_single(copy.deepcopy(base_config), years=years)
    df = pd.DataFrame(rows)
    out = {}
    for y in CHECK_YEARS:
        r = df.loc[df["Year"] == y, metric]
        out[y] = float(r.iloc[0]) if not r.empty else np.nan
    return out


def main() -> None:
    rows = []
    for region in REGIONS:
        print(f"[region] {region}", flush=True)
        base_cfg = load_config(region)
        policy_patch = base_cfg.get("policy_scenarios", {}).get(POLICY, {})
        region_cfg = _deep_merge(base_cfg, policy_patch) if policy_patch else copy.deepcopy(base_cfg)
        det = deterministic_row(region_cfg, years=68, metric=METRIC)
        for scenario_name, active_layers in SCENARIOS:
            t0 = time.time()
            mc_runs = 0 if not active_layers else MC_RUNS
            if mc_runs == 0:
                # Deterministic -- width is 0, just record median trajectory as p50.
                for year in CHECK_YEARS:
                    val = det.get(year, np.nan)
                    rows.append({
                        "region": region,
                        "scenario": scenario_name,
                        "mc_runs": 0,
                        "active_layers": ";".join(sorted(active_layers)) or "none",
                        "year": year,
                        "metric": METRIC,
                        "p05": val, "p50": val, "p95": val,
                        "width": 0.0,
                        "width_over_median": 0.0,
                        "interpretation_boundary_year": None,
                        "elapsed_sec": round(time.time() - t0, 2),
                    })
                continue
            q = run_ensemble(region_cfg, active_layers, mc_runs=mc_runs, seed=SEED)
            if q is None:
                continue
            ib = compute_interpretation_boundary(q.set_index("Year") if "Year" in q.columns else q)
            for year in CHECK_YEARS:
                m = width_metrics(q, METRIC, year)
                rows.append({
                    "region": region,
                    "scenario": scenario_name,
                    "mc_runs": mc_runs,
                    "active_layers": ";".join(sorted(active_layers)),
                    "year": year,
                    "metric": METRIC,
                    **m,
                    "interpretation_boundary_year": ib.get("boundary_year"),
                    "elapsed_sec": round(time.time() - t0, 2),
                })
            print(f"  [{scenario_name}] IB={ib.get('boundary_year')} width/median 2030={rows[-3]['width_over_median']:.2f} 2050={rows[-2]['width_over_median']:.2f} 2075={rows[-1]['width_over_median']:.2f}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
