"""Regenerate California and Ohio baseline quantile outputs under the final
decision-meaningful default parameter-level bundle.

Outputs under results/:
  {region}__policy-baseline__bundle-default_mc_runs.csv
  {region}__policy-baseline__bundle-default_quantiles.csv
  {region}__policy-baseline__bundle-default_metrics_quantiles.csv

Also writes paper-safe reproductions when requested:
  {region}__policy-baseline__bundle-paper-safe_quantiles.csv
"""

from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

APP_DIR = REPO / "v4_streamlit_app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import footprint_model as fm
from core import (  # type: ignore
    apply_parameter_choices,
    load_base_config,
    parameter_default_choices,
    parameter_paper_safe_choices,
)

OUT_DIR = REPO / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REGIONS = ["california", "ohio"]
POLICY = "baseline"
MC_RUNS = 200
SEED = 42
HORIZON_YEARS = 68


def _run_one(cfg: dict) -> list[dict]:
    variant = fm._parse_model_variant(cfg.get("model_variants"))
    energy_model = fm.build_energy_model(variant, cfg.get("consumption_rates", {}))
    model = fm.TransportModel(
        initial_data=cfg["initial_data"],
        growth_rates=cfg["growth_rates"],
        consumption_rates=cfg["consumption_rates"],
        emission_factors=cfg["emission_factors"],
        model_variants=cfg.get("model_variants"),
        energy_model=energy_model,
    )
    model.run_simulation(years=HORIZON_YEARS)
    return model.results


def run_bundle(region: str, choices: dict[str, str], bundle_label: str) -> None:
    base = load_base_config(region)
    policy_patch = base.get("policy_scenarios", {}).get(POLICY, {})
    runtime = fm._deep_merge(base, policy_patch) if policy_patch else copy.deepcopy(base)
    cfg_template = apply_parameter_choices(runtime, choices, region)
    rng = np.random.default_rng(SEED)

    runs = []
    t0 = time.time()
    for run_id in range(MC_RUNS):
        sampled = fm.sample_config(cfg_template, rng)
        results = _run_one(sampled)
        for row in results:
            row_with_id = dict(row)
            row_with_id["run_id"] = run_id
            runs.append(row_with_id)
    elapsed = round(time.time() - t0, 1)
    print(f"  [{region}/{bundle_label}] {MC_RUNS} runs in {elapsed}s")

    mc_df = pd.DataFrame(runs)
    prefix = OUT_DIR / f"{region}__policy-{POLICY}__bundle-{bundle_label}"
    mc_df.to_csv(prefix.parent / f"{prefix.name}_mc_runs.csv", index=False)

    # per-year quantile summary
    per_run = [mc_df[mc_df["run_id"] == rid].drop(columns=["run_id"]).to_dict("records")
               for rid in range(MC_RUNS)]
    q_df = fm.compute_quantile_summary(per_run, quantiles=[0.05, 0.5, 0.95])
    q_df.to_csv(prefix.parent / f"{prefix.name}_quantiles.csv", index=False)

    metric_rows = [fm.compute_scalar_metrics(pd.DataFrame(per_run[i])) for i in range(MC_RUNS)]
    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(prefix.parent / f"{prefix.name}_metrics.csv", index=False)

    # Interpretation boundary report
    ib = fm.compute_interpretation_boundary(q_df.set_index("Year") if "Year" in q_df.columns else q_df)
    print(f"    interpretation boundary: {ib.get('boundary_year')}")


def main() -> None:
    print(f"[regeneration] MC={MC_RUNS}, seed={SEED}, horizon={HORIZON_YEARS}")
    defaults = parameter_default_choices()
    paper_safe = parameter_paper_safe_choices()
    for region in REGIONS:
        run_bundle(region, defaults, "default")
        run_bundle(region, paper_safe, "paper-safe")
    print("done")


if __name__ == "__main__":
    main()
