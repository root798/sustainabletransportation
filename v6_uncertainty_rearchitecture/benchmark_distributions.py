"""Extract benchmark-year conditional marginals from a nested-MC run table."""
from __future__ import annotations

import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from v6_uncertainty_rearchitecture import uncertainty_taxonomy as utax


METRIC_DEFAULT = "ATS Emissions (kg CO2)"


def benchmark_frame(runs: pd.DataFrame,
                    metric: str = METRIC_DEFAULT,
                    years: Optional[List[int]] = None) -> pd.DataFrame:
    """Return a (draw × year) frame: marginal values of ``metric`` at each benchmark year.

    Each row is one inner × outer draw pair; each column is one benchmark year.
    """
    ys = years or utax.benchmark_years()
    if runs.empty or metric not in runs.columns:
        return pd.DataFrame(columns=ys)
    sub = runs[runs["Year"].isin(ys)].pivot_table(
        index=["outer_draw_id", "inner_draw_id"],
        columns="Year",
        values=metric,
        aggfunc="mean",
    )
    # make columns plain ints
    sub.columns = [int(c) for c in sub.columns]
    return sub.reset_index()


def benchmark_summary(runs: pd.DataFrame,
                      metric: str = METRIC_DEFAULT,
                      years: Optional[List[int]] = None,
                      quantiles: Optional[List[float]] = None) -> pd.DataFrame:
    """Per-year quantile summary of ``metric``."""
    ys = years or utax.benchmark_years()
    qs = quantiles or [0.05, 0.25, 0.5, 0.75, 0.95]
    if runs.empty or metric not in runs.columns:
        return pd.DataFrame()
    rows = []
    for y in ys:
        sub = runs.loc[runs["Year"] == y, metric].dropna()
        if sub.empty:
            continue
        row = {"year": int(y), "n": int(len(sub))}
        for q in qs:
            row[f"p{int(round(q*100)):02d}"] = float(sub.quantile(q))
        row["mean"] = float(sub.mean())
        row["std"] = float(sub.std(ddof=1)) if len(sub) > 1 else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def write_benchmark_tables(runs: pd.DataFrame, out_dir: str,
                           region: str, policy: str,
                           metrics: Optional[List[str]] = None) -> Dict[str, str]:
    """Persist one summary CSV per metric to ``out_dir``. Return path map."""
    os.makedirs(out_dir, exist_ok=True)
    metrics = metrics or [METRIC_DEFAULT, "ATS Total Power (kWh)"]
    paths: Dict[str, str] = {}
    for m in metrics:
        df = benchmark_summary(runs, metric=m)
        if df.empty:
            continue
        safe = m.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
        p = os.path.join(out_dir, f"{region}__{policy}__benchmark__{safe}.csv")
        df.to_csv(p, index=False)
        paths[m] = p
    return paths


__all__ = ["benchmark_frame", "benchmark_summary", "write_benchmark_tables"]
