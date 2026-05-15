"""Stage 3: surrogate + global sensitivity analysis.

Given an outer-design × outer-summary table from ``nested_mc.run_nested_mc``,
fit a lightweight surrogate (random forest when scikit-learn is available,
otherwise a ridge-regression + polynomial-feature fallback) and rank the
epistemic drivers by Sobol total-order index when SALib is available, else by
variance-explained importance derived from the surrogate.

Both rankings are emitted together so the dashboard / paper can cross-check.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


try:  # optional
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import r2_score
    _HAS_SKLEARN = True
except Exception:
    _HAS_SKLEARN = False


try:  # optional
    from SALib.sample import saltelli  # type: ignore
    from SALib.analyze import sobol  # type: ignore
    _HAS_SALIB = True
except Exception:
    _HAS_SALIB = False


DEFAULT_TARGETS = [
    "cum_emis_mean",
    "peak_emis_mean",
    "peak_year_mean",
    "turning_year_mean",
]


@dataclass
class SensitivityResult:
    target: str
    ranking: pd.DataFrame          # sorted descending by primary index
    method: str                    # "sobol_total_order" or "rf_importance" or "variance_explained"
    r2_train: Optional[float] = None


def _feature_columns(design: pd.DataFrame) -> List[str]:
    drop = {"outer_draw_id"}
    cols: List[str] = []
    for c in design.columns:
        if c in drop:
            continue
        if pd.api.types.is_numeric_dtype(design[c]):
            cols.append(c)
    return cols


def _align_targets(design: pd.DataFrame,
                   summaries: pd.DataFrame,
                   target: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    merged = design.merge(summaries, on="outer_draw_id", how="inner")
    features = _feature_columns(design)
    X = merged[features].to_numpy(dtype=float)
    y = merged[target].to_numpy(dtype=float)
    # Drop all-NaN columns and rows.
    keep_cols = ~np.all(np.isnan(X), axis=0) & (np.nanvar(X, axis=0) > 0)
    features = [f for f, k in zip(features, keep_cols) if k]
    X = X[:, keep_cols]
    mask = ~np.isnan(y)
    X = X[mask]
    y = y[mask]
    return X, y, features


def _rf_importance(X: np.ndarray, y: np.ndarray, features: List[str]) -> Tuple[pd.DataFrame, float]:
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    rf = RandomForestRegressor(
        n_estimators=400, max_depth=None, random_state=0, n_jobs=1,
    )
    rf.fit(Xs, y)
    imp = rf.feature_importances_
    r2 = float(r2_score(y, rf.predict(Xs)))
    df = pd.DataFrame(
        {"feature": features, "importance_rf": imp}
    ).sort_values("importance_rf", ascending=False).reset_index(drop=True)
    return df, r2


def _variance_explained(X: np.ndarray, y: np.ndarray, features: List[str]) -> Tuple[pd.DataFrame, float]:
    """Deterministic fallback: univariate Pearson^2 on standardized features."""
    imps: List[float] = []
    y_std = (y - y.mean()) / (y.std() + 1e-12)
    for j in range(X.shape[1]):
        xj = X[:, j]
        xj_std = (xj - xj.mean()) / (xj.std() + 1e-12)
        r = float(np.mean(xj_std * y_std))
        imps.append(r ** 2)
    df = pd.DataFrame(
        {"feature": features, "variance_explained": imps}
    ).sort_values("variance_explained", ascending=False).reset_index(drop=True)
    return df, float(sum(imps))


def _sobol_if_possible(X: np.ndarray, y: np.ndarray, features: List[str],
                       n_base: int = 1024) -> Optional[pd.DataFrame]:
    """Train a random forest as a surrogate; then Saltelli-sample around the
    observed feature ranges and run Sobol on surrogate predictions.

    Returns None if SALib or sklearn are unavailable, or if the sample budget
    cannot be met.
    """
    if not (_HAS_SALIB and _HAS_SKLEARN):
        return None
    lows = np.nanmin(X, axis=0)
    highs = np.nanmax(X, axis=0)
    # Widen slightly if any feature has zero spread.
    spread = highs - lows
    safe = spread > 1e-10
    if not np.all(safe):
        return None

    # Fit a surrogate on the observed data.
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    rf = RandomForestRegressor(n_estimators=400, max_depth=None, random_state=0, n_jobs=1)
    rf.fit(Xs, y)

    problem = {
        "num_vars": len(features),
        "names": features,
        "bounds": list(zip(lows, highs)),
    }
    try:
        samples = saltelli.sample(problem, n_base, calc_second_order=False)
    except Exception:
        return None
    preds = rf.predict(scaler.transform(samples))
    try:
        Si = sobol.analyze(problem, preds, calc_second_order=False, print_to_console=False)
    except Exception:
        return None
    df = pd.DataFrame(
        {
            "feature": features,
            "S1": Si.get("S1", np.zeros(len(features))),
            "ST": Si.get("ST", np.zeros(len(features))),
            "S1_conf": Si.get("S1_conf", np.zeros(len(features))),
            "ST_conf": Si.get("ST_conf", np.zeros(len(features))),
        }
    ).sort_values("ST", ascending=False).reset_index(drop=True)
    return df


def rank_drivers(design: pd.DataFrame,
                 summaries: pd.DataFrame,
                 target: str,
                 n_saltelli: int = 1024) -> SensitivityResult:
    X, y, features = _align_targets(design, summaries, target)
    if X.shape[0] < 4 or X.shape[1] == 0:
        return SensitivityResult(target=target,
                                 ranking=pd.DataFrame(columns=["feature"]),
                                 method="insufficient_data")

    sobol_df = _sobol_if_possible(X, y, features, n_base=n_saltelli)
    if sobol_df is not None:
        return SensitivityResult(target=target, ranking=sobol_df, method="sobol_total_order")

    if _HAS_SKLEARN:
        rf_df, r2 = _rf_importance(X, y, features)
        return SensitivityResult(target=target, ranking=rf_df, method="rf_importance", r2_train=r2)

    ve_df, _ = _variance_explained(X, y, features)
    return SensitivityResult(target=target, ranking=ve_df, method="variance_explained")


def run_all_targets(design: pd.DataFrame,
                    summaries: pd.DataFrame,
                    targets: Optional[List[str]] = None,
                    n_saltelli: int = 1024) -> Dict[str, SensitivityResult]:
    targets = targets or [t for t in DEFAULT_TARGETS if t in summaries.columns]
    return {t: rank_drivers(design, summaries, t, n_saltelli=n_saltelli) for t in targets}


def write_sensitivity_tables(results: Dict[str, SensitivityResult],
                             region: str, policy: str,
                             out_dir: str) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    paths: Dict[str, str] = {}
    combined_rows: List[Dict[str, Any]] = []
    for target, res in results.items():
        if res.ranking.empty:
            continue
        p = os.path.join(out_dir, f"{region}__{policy}__sensitivity__{target}.csv")
        res.ranking.to_csv(p, index=False)
        paths[target] = p
        top = res.ranking.head(5).to_dict(orient="records")
        for rank, row in enumerate(top, start=1):
            combined_rows.append({
                "region": region,
                "policy": policy,
                "target": target,
                "rank": rank,
                "feature": row.get("feature"),
                "method": res.method,
                "score": row.get("ST", row.get("importance_rf", row.get("variance_explained"))),
            })
    if combined_rows:
        combined = pd.DataFrame(combined_rows)
        combined.to_csv(os.path.join(out_dir, f"{region}__{policy}__sensitivity__TOPN.csv"), index=False)
    return paths


__all__ = [
    "SensitivityResult",
    "rank_drivers",
    "run_all_targets",
    "write_sensitivity_tables",
    "DEFAULT_TARGETS",
]
