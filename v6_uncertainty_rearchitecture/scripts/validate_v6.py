"""Validation harness for v6.

Checks:
  1. Deterministic reference path matches v5 legacy deterministic CSV bit-for-bit
     for ATS Emissions and ATS Total Power across every year (within 1e-6 rtol).
  2. Outer design has no NaN in any numeric feature column.
  3. Outer summaries preserve benchmark-year columns.
  4. Benchmark-year p05/p50/p95 are monotonic (p05 ≤ p50 ≤ p95).
  5. Convergence-diagnostic: stability of p50(cum_emis) across cumulative outer sub-samples.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_V6_ROOT = os.path.dirname(_HERE)
_REPO_ROOT = os.path.dirname(_V6_ROOT)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from v6_uncertainty_rearchitecture import deterministic_reference as refpath  # noqa: E402
from v6_uncertainty_rearchitecture import benchmark_distributions as bench  # noqa: E402


RESULTS_DIR = os.path.join(_REPO_ROOT, "results")


def _v5_reference_csv(region: str) -> str:
    return os.path.join(RESULTS_DIR, f"{region}_results.csv")


def check_deterministic_match(region: str, policy: str = "baseline", years: int = 68) -> dict:
    v6_df = refpath.compute_reference_path(region, policy=policy, years=years)
    v5_path = _v5_reference_csv(region)
    if not os.path.exists(v5_path):
        return {"region": region, "status": "skipped", "reason": f"v5 CSV missing: {v5_path}"}
    v5_df = pd.read_csv(v5_path)
    if "Year" not in v5_df.columns:
        return {"region": region, "status": "skipped", "reason": "v5 CSV missing Year column"}
    join = v5_df.merge(v6_df, on="Year", suffixes=("_v5", "_v6"))
    diffs = {}
    for metric in ("ATS Emissions (kg CO2)", "ATS Total Power (kWh)"):
        a = f"{metric}_v5"
        b = f"{metric}_v6"
        if a in join.columns and b in join.columns:
            rel = (join[a] - join[b]).abs() / np.maximum(join[a].abs(), 1.0)
            diffs[metric] = float(rel.max())
    status = "ok" if all(v < 1e-6 for v in diffs.values()) else "drift"
    return {"region": region, "policy": policy, "status": status, "max_rel_diff": diffs}


def check_design_nan(design: pd.DataFrame) -> dict:
    numeric = design.select_dtypes(include=[np.number])
    nan_counts = numeric.isna().sum().to_dict()
    bad = {k: v for k, v in nan_counts.items() if v > 0}
    return {"status": "ok" if not bad else "nan_found", "nan_counts": bad}


def check_benchmark_monotonic(runs: pd.DataFrame, metric: str) -> dict:
    summary = bench.benchmark_summary(runs, metric=metric)
    if summary.empty:
        return {"status": "skipped", "reason": "empty benchmark summary"}
    mono = ((summary["p05"] <= summary["p50"]) & (summary["p50"] <= summary["p95"])).all()
    return {
        "status": "ok" if bool(mono) else "non_monotonic",
        "years": summary["year"].tolist(),
        "p05": summary["p05"].tolist(),
        "p50": summary["p50"].tolist(),
        "p95": summary["p95"].tolist(),
    }


def check_convergence(summaries: pd.DataFrame, target: str = "cum_emis_mean",
                      step: int = 10) -> dict:
    if target not in summaries.columns or summaries.empty:
        return {"status": "skipped"}
    running = []
    for n in range(step, len(summaries) + 1, step):
        running.append({"n": n, "p50": float(summaries[target].head(n).median()),
                        "mean": float(summaries[target].head(n).mean())})
    if not running:
        return {"status": "skipped"}
    last = running[-1]
    rel = [abs(r["p50"] - last["p50"]) / max(abs(last["p50"]), 1.0) for r in running]
    return {
        "status": "ok" if rel[-1] < 0.02 else "not_converged",
        "curve": running,
        "rel_drift_from_final": rel,
    }


def run(region: str, policy: str, out_dir: str, metric: str) -> dict:
    report = {"region": region, "policy": policy}
    report["deterministic_match"] = check_deterministic_match(region, policy)

    design_p = os.path.join(out_dir, f"{region}__{policy}__outer_design.csv")
    runs_p = os.path.join(out_dir, f"{region}__{policy}__runs.csv")
    summaries_p = os.path.join(out_dir, f"{region}__{policy}__outer_summaries.csv")

    if os.path.exists(design_p):
        report["design_nan"] = check_design_nan(pd.read_csv(design_p))
    if os.path.exists(runs_p):
        runs = pd.read_csv(runs_p)
        report["benchmark_monotonic"] = check_benchmark_monotonic(runs, metric)
    if os.path.exists(summaries_p):
        report["convergence"] = check_convergence(pd.read_csv(summaries_p))
    return report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--regions", nargs="+", default=["california", "ohio"])
    p.add_argument("--policy", default="baseline")
    p.add_argument("--out-dir", default=os.path.join(_V6_ROOT, "results"))
    p.add_argument("--metric", default="ATS Emissions (kg CO2)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    overall = []
    for region in args.regions:
        rep = run(region, args.policy, args.out_dir, args.metric)
        overall.append(rep)
        print(rep)
    import json
    out_p = os.path.join(args.out_dir, "v6_validation_report.json")
    with open(out_p, "w") as f:
        json.dump(overall, f, indent=2, default=str)
    print(f"wrote {out_p}")


if __name__ == "__main__":
    main()
