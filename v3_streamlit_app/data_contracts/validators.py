"""
Validation module for CLEAR-ATS v2.

Each validator returns a dict with keys:
    passed (bool), issues (list[str]), warnings (list[str])
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd

from .load_results import load_quantile_csv, load_config, list_available_scenarios


# ---------------------------------------------------------------------------
# Individual validators
# ---------------------------------------------------------------------------


def validate_quantile_csv(df: pd.DataFrame, label: str = "") -> dict:
    """Check that a quantile DataFrame has expected structure.

    Checks:
    - Index (or 'Year' column) is monotonically increasing
    - All _p05/_p50/_p95 families are present as triplets
    - No NaN values in numeric columns
    - All numeric values are non-negative
    """
    issues = []
    warnings_list = []

    if df is None:
        return {"passed": False, "issues": [f"{label}: DataFrame is None"], "warnings": []}

    # Year monotonicity
    idx = df.index
    if not idx.is_monotonic_increasing:
        issues.append(f"{label}: Year index is not monotonically increasing.")

    # Check _p50 columns exist
    p50_cols = [c for c in df.columns if c.endswith("_p50")]
    if not p50_cols:
        issues.append(f"{label}: No _p50 columns found.")

    # Check triplet completeness
    bases = set()
    for c in df.columns:
        for suf in ("_p05", "_p50", "_p95"):
            if c.endswith(suf):
                bases.add(c[: -len(suf)])
    for base in sorted(bases):
        missing = [
            suf
            for suf in ("_p05", "_p50", "_p95")
            if f"{base}{suf}" not in df.columns
        ]
        if missing:
            issues.append(f"{label}: Column family '{base}' missing suffixes: {missing}")

    # NaN check
    nan_count = df.isnull().sum().sum()
    if nan_count > 0:
        warnings_list.append(f"{label}: {nan_count} NaN values found in DataFrame.")

    # Non-negative check for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    neg_cols = [c for c in numeric_cols if (df[c] < 0).any()]
    if neg_cols:
        issues.append(f"{label}: Negative values found in columns: {neg_cols}")

    passed = len(issues) == 0
    return {"passed": passed, "issues": issues, "warnings": warnings_list}


def validate_units_consistency(df: pd.DataFrame) -> dict:
    """Check that kWh and kg CO2 columns contain positive finite values."""
    issues = []
    warnings_list = []

    if df is None:
        return {"passed": False, "issues": ["DataFrame is None"], "warnings": []}

    kwh_cols = [c for c in df.columns if "kWh" in c]
    co2_cols = [c for c in df.columns if "kg CO2" in c]

    for col in kwh_cols:
        if (df[col] < 0).any():
            issues.append(f"kWh column '{col}' has negative values.")
        if not np.isfinite(df[col]).all():
            warnings_list.append(f"kWh column '{col}' contains non-finite values.")

    for col in co2_cols:
        if (df[col] < 0).any():
            issues.append(f"CO2 column '{col}' has negative values.")
        if not np.isfinite(df[col]).all():
            warnings_list.append(f"CO2 column '{col}' contains non-finite values.")

    passed = len(issues) == 0
    return {"passed": passed, "issues": issues, "warnings": warnings_list}


def validate_scenario_names(configs: dict) -> dict:
    """Check that scenario configs have consistent key sets across regions."""
    issues = []
    warnings_list = []

    if not configs:
        return {"passed": False, "issues": ["No configs provided"], "warnings": []}

    key_sets = {region: set(cfg.keys()) for region, cfg in configs.items() if cfg is not None}
    if not key_sets:
        return {"passed": False, "issues": ["All configs are None"], "warnings": []}

    ref_region = next(iter(key_sets))
    ref_keys = key_sets[ref_region]

    for region, keys in key_sets.items():
        if keys != ref_keys:
            missing = ref_keys - keys
            extra = keys - ref_keys
            if missing:
                issues.append(f"Config for '{region}' missing keys vs '{ref_region}': {missing}")
            if extra:
                warnings_list.append(
                    f"Config for '{region}' has extra keys vs '{ref_region}': {extra}"
                )

    passed = len(issues) == 0
    return {"passed": passed, "issues": issues, "warnings": warnings_list}


# ---------------------------------------------------------------------------
# Master runner
# ---------------------------------------------------------------------------


def run_all_validations() -> dict:
    """Run all validation checks and return a consolidated report dict.

    Returns
    -------
    dict with keys:
        overall_passed (bool)
        scenario_availability (dict)
        quantile_validations (dict)
        units_validations (dict)
        config_validation (dict)
        all_issues (list[str])
        all_warnings (list[str])
    """
    report: dict[str, Any] = {
        "overall_passed": True,
        "scenario_availability": {},
        "quantile_validations": {},
        "units_validations": {},
        "config_validation": {},
        "all_issues": [],
        "all_warnings": [],
    }

    # --- Scenario availability ---
    availability = list_available_scenarios()
    report["scenario_availability"] = availability
    missing = [str(k) for k, v in availability.items() if not v]
    if missing:
        report["all_warnings"].append(f"Missing scenario files: {missing}")

    # --- Quantile CSV validation for available scenarios ---
    primary_scenarios = [key for key, exists in availability.items() if exists and len(key) == 2]

    for region, policy in primary_scenarios:
        if not availability.get((region, policy), False):
            continue
        df = load_quantile_csv(region, policy)
        label = f"{region}/{policy}"

        q_result = validate_quantile_csv(df, label)
        u_result = validate_units_consistency(df)

        report["quantile_validations"][label] = q_result
        report["units_validations"][label] = u_result

        if not q_result["passed"]:
            report["overall_passed"] = False
        report["all_issues"].extend(q_result["issues"])
        report["all_warnings"].extend(q_result["warnings"])

        if not u_result["passed"]:
            report["overall_passed"] = False
        report["all_issues"].extend(u_result["issues"])
        report["all_warnings"].extend(u_result["warnings"])

    # --- Config validation ---
    configs = {r: load_config(r) for r in ("california", "ohio", "us_average")}
    cfg_result = validate_scenario_names(configs)
    report["config_validation"] = cfg_result
    if not cfg_result["passed"]:
        report["overall_passed"] = False
    report["all_issues"].extend(cfg_result["issues"])
    report["all_warnings"].extend(cfg_result["warnings"])

    # Print summary
    status = "PASSED" if report["overall_passed"] else "FAILED"
    print(f"[CLEAR-ATS v2 Validation] Overall: {status}")
    for issue in report["all_issues"]:
        print(f"  ERROR: {issue}")
    for w in report["all_warnings"]:
        print(f"  WARN:  {w}")

    return report


if __name__ == "__main__":
    run_all_validations()
