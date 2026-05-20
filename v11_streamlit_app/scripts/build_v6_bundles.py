"""Generate the six v6 policy-scenario MC bundles.

Outputs to ``results/`` with the v6 naming convention:
  {region}__policy-{scenario_short}__v6_quantiles.csv
  {region}__policy-{scenario_short}__v6_mc_runs.csv
  {region}__policy-{scenario_short}__v6_metrics.csv
  {region}__policy-{scenario_short}__v6_extras.csv

v5 bundles in results/ are NOT touched.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_V6_ROOT = os.path.dirname(_HERE)
_REPO_ROOT = os.path.dirname(_V6_ROOT)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
if _V6_ROOT not in sys.path:
    sys.path.insert(0, _V6_ROOT)

import v6_run  # noqa: E402
from scenario_definitions import list_scenarios  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--scenarios", nargs="+", default=None,
                   help="Subset of scenario IDs; default = all six.")
    p.add_argument("--n-runs", type=int, default=80)
    p.add_argument("--years", type=int, default=68)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=os.path.join(_REPO_ROOT, "results"))
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def short_name(scenario_id: str) -> str:
    parts = scenario_id.split("-", 1)
    return parts[1] if len(parts) > 1 else parts[0]


def main() -> None:
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    scenarios = args.scenarios or (list_scenarios("california") + list_scenarios("ohio"))

    for sid in scenarios:
        t0 = time.time()
        out = v6_run.mc_scenario_run(sid, n_runs=args.n_runs, years=args.years,
                                     seed=args.seed, verbose=args.verbose)
        region = out["region"]
        prefix = f"{region}__policy-{short_name(sid)}__v6"

        runs_p = os.path.join(args.out_dir, f"{prefix}_mc_runs.csv")
        out["runs"].to_csv(runs_p, index=False)

        quants = v6_run.quantile_summary(out["runs"])
        quants.to_csv(os.path.join(args.out_dir, f"{prefix}_quantiles.csv"), index=False)

        metrics = v6_run.metrics_per_run(out["runs"])
        metrics.to_csv(os.path.join(args.out_dir, f"{prefix}_metrics.csv"), index=False)

        out["extras"].to_csv(os.path.join(args.out_dir, f"{prefix}_extras.csv"), index=False)

        elapsed = time.time() - t0
        print(f"[v6/build_bundles] {sid} -> {prefix}_*  n_runs={args.n_runs}  "
              f"runs_rows={len(out['runs'])}  elapsed={elapsed:.1f}s")


if __name__ == "__main__":
    main()
