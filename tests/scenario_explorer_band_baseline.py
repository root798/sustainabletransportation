"""Build the baseline cfg the v8 Scenario Explorer would feed to
``compute_live_residual_band`` on first load with all defaults, and
return the band frame.

Replicates the page's first-load wiring without importing Streamlit so
the same construction can run in tests, in the fixture-capture script,
and in CI. As long as ``v8_streamlit_app.core`` keeps the ``apply_*``
helpers' semantics, this builder stays valid across UI refactors.

Fixture parameters (frozen for the regression test):
    region          = "california"
    policy          = "baseline"
    bundle          = "default"   (committed-band selector — does not
                                    enter compute_live_residual_band)
    block1 levers   = mitigation_defaults.json values
    block2 fixed    = controls_from_config(runtime, region, policy)
    block3 templates= ("Balanced", "Basic-heavy (default)", retire=12,
                       fleet_linear=True)
    block4 priors   = all residual params at "published",
                      all non-residual params at "fixed"
    weather mode    = Auto (no centroid override, no kappa override)
    seed            = 42
    n_samples       = 80
    metric          = "ATS Emissions (kg CO2)"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
V8_DIR = REPO_ROOT / "v8_streamlit_app"
if str(V8_DIR) not in sys.path:
    sys.path.insert(0, str(V8_DIR))

from core import (  # noqa: E402
    CAV_LEVEL_TEMPLATES,
    CONTROL_SPECS,
    STI_LEVEL_TEMPLATES,
    V5_NON_RESIDUAL_PARAMS,
    apply_assumption_templates,
    apply_controls,
    apply_v5_choices,
    attach_weather_region,
    compute_live_residual_band,
    controls_from_config,
    load_parameter_registry,
    load_runtime_config,
)

DEFAULT_FIXTURE = {
    "region": "california",
    "policy": "baseline",
    "cav_template": "Balanced",
    "sti_template": "Basic-heavy (default)",
    "retire_year": 12,
    "fleet_linear": True,
    "seed": 42,
    "n_samples": 80,
    "years": 68,
    "metric": "ATS Emissions (kg CO2)",
}

_MIT_KEY_MAP = {
    "cav_growth_rate":               "cav_target_2075",
    "sti_growth_rate":               "sti_target_2075",
    "ev_growth_rate":                "bev_growth_rate",
    "clean_energy_growth_rate":      "low_carbon_electricity_growth",
    "efficiency_doubling_years":     "hardware_doubling_years",
    "hardware_deployment_lag_years": "hardware_deployment_lag_years",
}


def _load_mitigation_defaults(region: str) -> dict[str, Any]:
    path = V8_DIR / "configs" / "mitigation_defaults.json"
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    return raw.get(region, raw.get("california", {}))


def build_default_choices() -> dict[str, str]:
    """Block 4 default radio choices: residuals = 'published', non-residuals = 'fixed'.

    Mirrors ``_v5_initial_choices`` in pages/03_Scenario_Explorer.py.
    """
    out: dict[str, str] = {}
    for rec in load_parameter_registry():
        pid = rec["param_id"]
        out[pid] = "fixed" if pid in V5_NON_RESIDUAL_PARAMS else "published"
    return out


def build_default_cfg(
    region: str = DEFAULT_FIXTURE["region"],
    policy: str = DEFAULT_FIXTURE["policy"],
    cav_template: str = DEFAULT_FIXTURE["cav_template"],
    sti_template: str = DEFAULT_FIXTURE["sti_template"],
    retire_year: int = DEFAULT_FIXTURE["retire_year"],
    fleet_linear: bool = DEFAULT_FIXTURE["fleet_linear"],
) -> dict[str, Any]:
    """Reproduce the live cfg the Scenario Explorer feeds the band on first load."""
    runtime = load_runtime_config(region, policy)
    cv = controls_from_config(runtime, region, policy)
    mit = _load_mitigation_defaults(region)

    live_cv: dict[str, Any] = {"region": region, "policy": policy}
    for key in CONTROL_SPECS:
        if key in _MIT_KEY_MAP:
            live_cv[key] = mit.get(_MIT_KEY_MAP[key], cv.get(key))
        else:
            live_cv[key] = cv.get(key)
    live_cv["retire_year"] = int(retire_year)

    cfg = apply_controls(runtime, live_cv)
    cfg = apply_assumption_templates(
        cfg,
        cav_levels=CAV_LEVEL_TEMPLATES[cav_template],
        sti_levels=STI_LEVEL_TEMPLATES[sti_template],
        retire_year=int(retire_year),
        fleet_linear=fleet_linear,
    )
    cfg = apply_v5_choices(cfg, build_default_choices(), {}, region)
    attach_weather_region(cfg, region, centroid_override=None,
                          kappa_override=None)
    return cfg


def compute_baseline_band(
    region: str = DEFAULT_FIXTURE["region"],
    policy: str = DEFAULT_FIXTURE["policy"],
    seed: int = DEFAULT_FIXTURE["seed"],
    n_samples: int = DEFAULT_FIXTURE["n_samples"],
    years: int = DEFAULT_FIXTURE["years"],
    metric: str = DEFAULT_FIXTURE["metric"],
    **cfg_kwargs,
) -> pd.DataFrame:
    cfg = build_default_cfg(region=region, policy=policy, **cfg_kwargs)
    return compute_live_residual_band(
        cfg, years=years, n_samples=n_samples, seed=seed, metric=metric,
    )


def fixture_path(region: str = DEFAULT_FIXTURE["region"],
                 policy: str = DEFAULT_FIXTURE["policy"]) -> Path:
    return (Path(__file__).resolve().parent / "fixtures"
            / f"scenario_explorer_baseline_{region}_{policy}.pkl")
