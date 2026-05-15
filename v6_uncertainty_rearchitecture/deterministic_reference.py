"""Stage 1: deterministic reference trajectory.

Runs ``TransportModel`` with every distribution spec stripped out (or replaced
by its mean / mode) so v6 can assert bit-identical central paths against v5.
"""
from __future__ import annotations

import contextlib
import copy
import io
import os
import sys
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# v6 is a sibling to v5; add repo root to path so ``footprint_model`` imports cleanly.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import footprint_model as fm  # noqa: E402


def _central_value(spec: Dict[str, Any]) -> Any:
    """Return a deterministic point estimate for a distribution spec.

    Conservative rule set:
      - triangular     → mode
      - normal / truncated_normal → mean
      - lognormal      → mean if given, else exp(mu + sigma^2/2)
      - beta           → mean (beta with mean given) or alpha / (alpha+beta)
      - uniform        → midpoint
      - choice         → first option
      - discrete       → value with highest probability
      - dirichlet      → alpha / sum(alpha)
    """
    dist = spec.get("dist")
    if dist == "triangular":
        return spec.get("mode", spec.get("mean"))
    if dist in ("normal", "truncated_normal"):
        return spec.get("mean")
    if dist == "lognormal":
        if "mean" in spec:
            return spec["mean"]
        mu = spec.get("mu", 0.0)
        sigma = spec.get("sigma", 0.0)
        return float(np.exp(mu + 0.5 * sigma ** 2))
    if dist == "beta":
        if "mean" in spec:
            return spec["mean"]
        a = spec.get("alpha")
        b = spec.get("beta")
        if a is not None and b is not None and (a + b) > 0:
            return a / (a + b)
        return 0.5
    if dist == "uniform":
        return 0.5 * (spec.get("low", 0.0) + spec.get("high", 1.0))
    if dist == "choice":
        opts = spec.get("options") or spec.get("values") or []
        return opts[0] if opts else None
    if dist == "discrete":
        weights = spec.get("weights") or spec.get("probabilities") or []
        values = spec.get("values") or []
        if values and weights and len(values) == len(weights):
            return values[int(np.argmax(weights))]
        return values[0] if values else None
    if dist == "dirichlet":
        alpha = spec.get("alpha") or []
        total = float(sum(alpha)) if alpha else 0.0
        if total > 0:
            return [a / total for a in alpha]
        return alpha
    # unknown → passthrough
    return spec


def _strip_distributions(obj: Any) -> Any:
    """Replace any distribution spec (dict with ``dist``) by its central value."""
    if isinstance(obj, dict):
        if "dist" in obj:
            return _central_value(obj)
        return {k: _strip_distributions(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_distributions(v) for v in obj]
    return obj


def load_runtime_config(region: str, policy: str = "baseline") -> Dict[str, Any]:
    """Load base config + deep-merged policy patch. Distribution specs intact."""
    base = fm.load_config(region)
    policy_patches = base.get("policy_scenarios", {})
    if policy and policy in policy_patches:
        base = fm._deep_merge(base, policy_patches[policy])
    return base


def compute_reference_path(
    region: str,
    policy: str = "baseline",
    years: int = 68,
    model_variant: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Deterministic Stage 1 reference trajectory.

    Produces the same DataFrame shape the v5 simulator returns, using central
    values for every distribution spec. This should match v5's deterministic
    CSV bit-for-bit under identical configuration.
    """
    cfg = load_runtime_config(region, policy)
    # Strip all distributions in sections that the simulator reads directly
    # (the data_uncertainty block itself is not consumed when sample_config is
    # bypassed).
    for key in ["initial_data", "growth_rates", "consumption_rates", "emission_factors"]:
        if key in cfg:
            cfg[key] = _strip_distributions(cfg[key])

    variant = model_variant or fm._parse_model_variant(cfg.get("model_variants", {}))
    energy_model = fm.build_energy_model(variant, cfg["consumption_rates"])
    model = fm.TransportModel(
        initial_data=cfg["initial_data"],
        growth_rates=cfg["growth_rates"],
        consumption_rates=cfg["consumption_rates"],
        emission_factors=cfg["emission_factors"],
        model_variants=variant,
        energy_model=energy_model,
    )
    with contextlib.redirect_stdout(io.StringIO()):
        model.run_simulation(years=years)
    return pd.DataFrame(model.results)


def reference_scalar_metrics(df: pd.DataFrame) -> Dict[str, float]:
    return fm.compute_scalar_metrics(df)


def run_all_regions(
    regions: List[str] = ("california", "ohio"),
    policy: str = "baseline",
    years: int = 68,
    output_dir: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for region in regions:
        df = compute_reference_path(region, policy=policy, years=years)
        out[region] = df
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            df.to_csv(os.path.join(output_dir, f"{region}__{policy}__reference.csv"), index=False)
    return out


__all__ = [
    "compute_reference_path",
    "reference_scalar_metrics",
    "run_all_regions",
    "load_runtime_config",
]
