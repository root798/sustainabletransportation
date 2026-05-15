"""Stage 3 driver — Sobol + fallback sensitivity on the v6 nested-MC outputs.

Reads ``<out-dir>/<region>__<policy>__outer_design.csv`` and
``outer_summaries.csv``, computes per-target rankings, writes
``<region>__<policy>__sensitivity__<target>.csv`` plus a combined
``<region>__<policy>__sensitivity__TOPN.csv``.
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_V6_ROOT = os.path.dirname(_HERE)
_REPO_ROOT = os.path.dirname(_V6_ROOT)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from v6_uncertainty_rearchitecture import surrogate  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--regions", nargs="+", default=["california", "ohio"])
    p.add_argument("--policy", default="baseline")
    p.add_argument("--out-dir", default=os.path.join(_V6_ROOT, "results"))
    p.add_argument("--n-saltelli", type=int, default=1024)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    for region in args.regions:
        design_path = os.path.join(args.out_dir, f"{region}__{args.policy}__outer_design.csv")
        summary_path = os.path.join(args.out_dir, f"{region}__{args.policy}__outer_summaries.csv")
        if not (os.path.exists(design_path) and os.path.exists(summary_path)):
            print(f"[v6/sensitivity] skipping {region}: missing outer design / summaries", file=sys.stderr)
            continue
        design = pd.read_csv(design_path)
        summaries = pd.read_csv(summary_path)
        results = surrogate.run_all_targets(design, summaries, n_saltelli=args.n_saltelli)
        surrogate.write_sensitivity_tables(results, region, args.policy, args.out_dir)
        for target, res in results.items():
            n = len(res.ranking)
            print(f"[v6/sensitivity] {region}/{args.policy}/{target}: method={res.method}, "
                  f"features={n}, r2={res.r2_train}")


if __name__ == "__main__":
    main()
