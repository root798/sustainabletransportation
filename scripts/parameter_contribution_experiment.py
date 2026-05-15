"""Parameter-level and layer-level contribution experiment.

For each uncertainty parameter in the registry, run a selective-Monte-Carlo with
only that single parameter free (others fixed at their central values). Record
relative band width at 2030, 2050, 2075 and the interpretation-boundary year.

Outputs:
  audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv
  audits/uncertainty_governance/LAYER_CONTRIBUTION_EXPERIMENT.csv   (copy of the earlier all-layer run aggregated)
"""

from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from footprint_model import (  # noqa: E402
    TransportModel,
    compute_interpretation_boundary,
    compute_quantile_summary,
    load_config,
    sample_config,
    _deep_merge,
)

OUT_PARAM_CSV = REPO / "audits" / "uncertainty_governance" / "PARAMETER_CONTRIBUTION_EXPERIMENT.csv"
OUT_LAYER_CSV = REPO / "audits" / "uncertainty_governance" / "LAYER_CONTRIBUTION_EXPERIMENT.csv"
OUT_PARAM_CSV.parent.mkdir(parents=True, exist_ok=True)

REGIONS = ["california", "ohio"]
POLICY = "baseline"
METRIC = "ATS Emissions (kg CO2)"
CHECK_YEARS = [2030, 2050, 2075]
MC_RUNS = 80
SEED = 42


# Parameter id -> (config_path_as_tuple, optional_subkey) telling the experiment
# which slice of data_uncertainty to retain for the isolated run.
# For multi-cell entries (e.g. the three per-level ECAV lognormals), the
# experiment groups them into one "axis" so we also report the S2-01 / S2-02
# dual-axis net effect as a single line item.
PARAMS = [
    # L1
    ("F01", ["initial_data", "f_clean"]),
    ("F02", ["initial_data", "ev_share"]),
    ("F03", ["emission_factors", "e_clean"]),
    ("F04", ["emission_factors", "e_fossil"]),
    ("F05", ["emission_factors", "e_gasoline"]),
    # L2 -- per-level ECAV axis (three cells kept together to show the duplicated axis)
    ("F06_F07_F08_ecav_per_level", ["consumption_rates", "ecav_scale_factors", ("L3", "L4", "L5")]),
    ("F09", ["consumption_rates", "ecav_scale_factors", "sensing"]),
    ("F10", ["consumption_rates", "ecav_scale_factors", "computing"]),
    ("F11", ["consumption_rates", "ecav_scale_factors", "communication"]),
    ("F12_F13_F14_sti_per_level", ["consumption_rates", "sti_scale_factors", ("Basic", "Semi", "Highly")]),
    ("F15", ["consumption_rates", "sti_scale_factors", "sensing"]),
    ("F16", ["consumption_rates", "sti_scale_factors", "computing"]),
    ("F17", ["consumption_rates", "sti_scale_factors", "communication"]),
    ("F18", ["consumption_rates", "cav_levels"]),
    ("F19", ["consumption_rates", "sti_levels"]),
    ("F20", ["consumption_rates", "icecav_power_factor"]),
    ("F21", ["consumption_rates", "cohort_decay_factor"]),
    ("F22", ["growth_rates", "retire_year"]),
    # L3
    ("F23", ["growth_rates", "cav"]),
    ("F24", ["growth_rates", "sti"]),
    ("F25", ["growth_rates", "ev"]),
    ("F26", ["growth_rates", "clean_energy"]),
    ("F27", ["growth_rates", "efficiency_doubling"]),
    ("F28", ["growth_rates", "total_car_increase"]),
]

PARAM_LAYER = {
    "F01": "L1", "F02": "L1", "F03": "L1", "F04": "L1", "F05": "L1",
    "F06_F07_F08_ecav_per_level": "L2",
    "F09": "L2", "F10": "L2", "F11": "L2",
    "F12_F13_F14_sti_per_level": "L2",
    "F15": "L2", "F16": "L2", "F17": "L2",
    "F18": "L2", "F19": "L2", "F20": "L2", "F21": "L2", "F22": "L2",
    "F23": "L3", "F24": "L3", "F25": "L3", "F26": "L3", "F27": "L3", "F28": "L3",
}


def build_isolated_data_uncertainty(full_du: dict, path: list) -> dict:
    """Return a data_uncertainty block that retains only one parameter (or one tuple of keys)."""
    if not path:
        return {}
    section = path[0]
    src_section = full_du.get(section, {})
    if not isinstance(src_section, dict):
        return {}
    result = {section: {}}
    if len(path) == 2:
        key = path[1]
        if isinstance(key, tuple):
            for k in key:
                if k in src_section:
                    result[section][k] = copy.deepcopy(src_section[k])
        else:
            if key in src_section:
                result[section][key] = copy.deepcopy(src_section[key])
    elif len(path) == 3:
        sub_key = path[1]
        leaf = path[2]
        if sub_key in src_section and isinstance(src_section[sub_key], dict):
            inner = {}
            if isinstance(leaf, tuple):
                for k in leaf:
                    if k in src_section[sub_key]:
                        inner[k] = copy.deepcopy(src_section[sub_key][k])
            else:
                if leaf in src_section[sub_key]:
                    inner[leaf] = copy.deepcopy(src_section[sub_key][leaf])
            if inner:
                result[section][sub_key] = inner
    if not result[section]:
        return {}
    return result


def run_single(config: dict, years: int = 68) -> list[dict]:
    model = TransportModel(
        initial_data=config["initial_data"],
        growth_rates=config["growth_rates"],
        consumption_rates=config["consumption_rates"],
        emission_factors=config["emission_factors"],
        model_variants=config.get("model_variants"),
    )
    model.run_simulation(years=years)
    return model.results


def run_ensemble(region_cfg: dict, path: list, mc_runs: int, seed: int) -> pd.DataFrame | None:
    cfg_template = copy.deepcopy(region_cfg)
    full_du = cfg_template.get("data_uncertainty", {})
    cfg_template["data_uncertainty"] = build_isolated_data_uncertainty(full_du, path)
    if not cfg_template["data_uncertainty"]:
        return None
    rng = np.random.default_rng(seed)
    runs = []
    for _ in range(mc_runs):
        sampled = sample_config(cfg_template, rng)
        runs.append(run_single(sampled))
    return compute_quantile_summary(runs, quantiles=[0.05, 0.5, 0.95])


def width_at(q_df: pd.DataFrame, metric: str, year: int) -> dict:
    if "Year" in q_df.columns:
        row = q_df.loc[q_df["Year"] == year]
    else:
        row = q_df.loc[q_df.index == year]
    if row.empty:
        return {"p05": float("nan"), "p50": float("nan"), "p95": float("nan"), "width_over_median": float("nan")}
    p05 = float(row[f"{metric}_p05"].iloc[0])
    p50 = float(row[f"{metric}_p50"].iloc[0])
    p95 = float(row[f"{metric}_p95"].iloc[0])
    wom = (p95 - p05) / abs(p50) if p50 else float("nan")
    return {"p05": p05, "p50": p50, "p95": p95, "width_over_median": wom}


def turning_year_uncertainty(q_df: pd.DataFrame, metric: str) -> tuple[float | None, float | None]:
    """Very rough proxy: the year where p50 first drops below 50% of its peak, and the spread
    between p95 and p05 turning years (using the same 50%-of-peak rule)."""
    import numpy as np
    if "Year" not in q_df.columns:
        q_df = q_df.reset_index()
    p50 = q_df[f"{metric}_p50"].to_numpy()
    yrs = q_df["Year"].to_numpy()
    if p50.size == 0:
        return None, None
    peak_idx = int(np.argmax(p50))
    peak = p50[peak_idx]

    def first_year_below_half(series: np.ndarray) -> float | None:
        for i in range(peak_idx, len(series)):
            if series[i] <= 0.5 * peak:
                return float(yrs[i])
        return None

    ty_p50 = first_year_below_half(p50)
    ty_p05 = first_year_below_half(q_df[f"{metric}_p05"].to_numpy())
    ty_p95 = first_year_below_half(q_df[f"{metric}_p95"].to_numpy())
    spread = None
    if ty_p05 is not None and ty_p95 is not None:
        spread = abs(ty_p95 - ty_p05)
    return ty_p50, spread


def main() -> None:
    all_rows = []
    for region in REGIONS:
        print(f"\n=== {region} ===")
        region_cfg = load_config(region)
        policy_patch = region_cfg.get("policy_scenarios", {}).get(POLICY, {})
        cfg = _deep_merge(region_cfg, policy_patch) if policy_patch else copy.deepcopy(region_cfg)

        for param_id, path in PARAMS:
            t0 = time.time()
            q = run_ensemble(cfg, path, mc_runs=MC_RUNS, seed=SEED)
            if q is None:
                print(f"  [skip] {param_id}: no matching entry in data_uncertainty.")
                continue
            ib = compute_interpretation_boundary(q.set_index("Year") if "Year" in q.columns else q)
            ty_p50, ty_spread = turning_year_uncertainty(q, METRIC)
            elapsed = round(time.time() - t0, 1)
            for year in CHECK_YEARS:
                m = width_at(q, METRIC, year)
                all_rows.append({
                    "region": region,
                    "param_id": param_id,
                    "layer": PARAM_LAYER.get(param_id, "?"),
                    "year": year,
                    "metric": METRIC,
                    **m,
                    "interpretation_boundary_year": ib.get("boundary_year"),
                    "turning_year_p50": ty_p50,
                    "turning_year_spread": ty_spread,
                    "mc_runs": MC_RUNS,
                    "elapsed_sec": elapsed,
                })
            print(f"  [{param_id}] W/M 2030={all_rows[-3]['width_over_median']:.2f} 2050={all_rows[-2]['width_over_median']:.2f} 2075={all_rows[-1]['width_over_median']:.2f} IB={ib.get('boundary_year')} TY_spread={ty_spread}")

    pd.DataFrame(all_rows).to_csv(OUT_PARAM_CSV, index=False)
    print(f"\nwrote {OUT_PARAM_CSV} ({len(all_rows)} rows)")

    # Reuse the earlier UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv as the layer-contribution basis;
    # copy it with the cleaner filename LAYER_CONTRIBUTION_EXPERIMENT.csv so the next-version
    # panel reads from the aliased file.
    src = REPO / "audits" / "uncertainty_governance" / "UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv"
    if src.exists():
        import shutil
        shutil.copy(src, OUT_LAYER_CSV)
        print(f"aliased {src.name} -> {OUT_LAYER_CSV.name}")


if __name__ == "__main__":
    main()
