"""Relative-uncertainty helpers.

Absolute band widths can narrow mechanically as an output approaches a bounded
state (e.g. emissions → 0). Reporting the band *ratio* alongside the absolute
band prevents that misreading.
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd


def annual_quantiles(runs: pd.DataFrame,
                     metric: str,
                     quantiles: Optional[List[float]] = None) -> pd.DataFrame:
    qs = quantiles or [0.05, 0.5, 0.95]
    if runs.empty or metric not in runs.columns:
        return pd.DataFrame()
    rows = []
    for year, sub in runs.groupby("Year"):
        vals = sub[metric].dropna()
        if vals.empty:
            continue
        rec = {"year": int(year), "n": int(len(vals))}
        for q in qs:
            rec[f"p{int(round(q*100)):02d}"] = float(vals.quantile(q))
        rec["mean"] = float(vals.mean())
        rows.append(rec)
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def relative_width(quantile_df: pd.DataFrame) -> pd.DataFrame:
    """Add columns for (p95 - p05)/|p50|, p95/p50, p05/p50."""
    if quantile_df.empty:
        return quantile_df
    out = quantile_df.copy()
    if "p50" not in out.columns:
        return out
    p50 = out["p50"].replace(0.0, np.nan)
    if "p05" in out.columns and "p95" in out.columns:
        out["abs_width"] = (out["p95"] - out["p05"]).abs()
        out["rel_width"] = out["abs_width"] / p50.abs()
        out["ratio_p95_p50"] = out["p95"] / p50
        out["ratio_p05_p50"] = out["p05"] / p50
    return out


def compare_absolute_vs_relative(runs: pd.DataFrame,
                                 metric: str) -> pd.DataFrame:
    return relative_width(annual_quantiles(runs, metric))


__all__ = ["annual_quantiles", "relative_width", "compare_absolute_vs_relative"]
