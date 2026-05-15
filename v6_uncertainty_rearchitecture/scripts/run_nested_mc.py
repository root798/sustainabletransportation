"""CLI driver for v6 nested MC.

Usage:
    python v6_uncertainty_rearchitecture/scripts/run_nested_mc.py \
        --regions california ohio \
        --policy baseline \
        --n-outer 40 --n-inner 20 --years 68 --seed 42
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

from v6_uncertainty_rearchitecture import nested_mc  # noqa: E402
from v6_uncertainty_rearchitecture import benchmark_distributions as bench  # noqa: E402
from v6_uncertainty_rearchitecture import relative_uncertainty as relu  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--regions", nargs="+", default=["california", "ohio"])
    p.add_argument("--policy", default="baseline")
    p.add_argument("--n-outer", type=int, default=None)
    p.add_argument("--n-inner", type=int, default=None)
    p.add_argument("--years", type=int, default=68)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--out-dir", default=os.path.join(_V6_ROOT, "results"))
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    for region in args.regions:
        t0 = time.time()
        result = nested_mc.run_nested_mc(
            region=region,
            policy=args.policy,
            n_outer=args.n_outer,
            n_inner=args.n_inner,
            years=args.years,
            seed_outer=args.seed,
            verbose=args.verbose,
        )
        nested_mc.save_result(result, region=region, policy=args.policy, out_dir=args.out_dir)

        # companion tables
        bench.write_benchmark_tables(result.runs, args.out_dir, region, args.policy)
        for metric in ("ATS Emissions (kg CO2)", "ATS Total Power (kWh)"):
            df_rel = relu.compare_absolute_vs_relative(result.runs, metric)
            if df_rel.empty:
                continue
            safe = metric.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
            p = os.path.join(args.out_dir, f"{region}__{args.policy}__relative__{safe}.csv")
            df_rel.to_csv(p, index=False)

        elapsed = time.time() - t0
        print(f"[v6] {region}/{args.policy}: {len(result.outer_design)} outer × "
              f"{len(result.runs) // max(len(result.outer_design),1)} inner (approx) "
              f"in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
