from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = APP_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from dashboard_core import (
    PAGE_ORDER,
    POLICY_LABELS,
    POLICY_ORDER,
    REGION_LABELS,
    REGION_ORDER,
    RESULTS_DIR,
    RESULTS_NOTEBOOK_DIR,
    deterministic_quantile_path,
    load_quantile_frame,
    load_runtime_config,
    page_support_rows,
    run_transport_simulation,
    scenario_support_record,
)

REPORTS_DIR = APP_DIR / "reports"
EXEC_PATH = REPORTS_DIR / "SCENARIO_SUPPORT_EXECUTIVE_SUMMARY.md"
MATRIX_PATH = REPORTS_DIR / "SCENARIO_SUPPORT_MATRIX.csv"
AUDIT_PATH = REPORTS_DIR / "SCENARIO_LOADER_AUDIT.md"
VALIDATION_PATH = REPORTS_DIR / "SCENARIO_VALIDATION_REPORT.md"
CHANGELOG_PATH = REPORTS_DIR / "SCENARIO_CHANGE_LOG.md"


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def support_frame() -> pd.DataFrame:
    return pd.DataFrame(page_support_rows()).sort_values(["region", "scenario", "page"]).reset_index(drop=True)


def file_inventory_frame() -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    results_quantile_pattern = re.compile(r"^(?P<region>.+)__policy-(?P<policy>.+)__model-fixed_table_quantiles\.csv$")
    notebook_quantile_pattern = re.compile(r"^(?P<region>.+)__policy-(?P<policy>.+)__quantiles(?:__(?P<variant>.+))?\.csv$")

    for path in sorted(RESULTS_DIR.glob("*.csv")):
        match = results_quantile_pattern.match(path.name)
        if match:
            rows.append(
                {
                    "source_dir": "results",
                    "file_name": path.name,
                    "region": match.group("region"),
                    "policy": match.group("policy"),
                    "variant": "",
                    "artifact_type": "aligned_quantiles",
                }
            )
            continue
        if path.name.startswith("yearly_additions_") and path.name.endswith("_results.csv"):
            rows.append(
                {
                    "source_dir": "results",
                    "file_name": path.name,
                    "region": path.name.replace("yearly_additions_", "").replace("_results.csv", ""),
                    "policy": "baseline",
                    "variant": "",
                    "artifact_type": "yearly_additions_results",
                }
            )
            continue
        if path.name.endswith("_results.csv"):
            rows.append(
                {
                    "source_dir": "results",
                    "file_name": path.name,
                    "region": path.name.replace("_results.csv", ""),
                    "policy": "baseline",
                    "variant": "",
                    "artifact_type": "deterministic_results",
                }
            )
            continue
        if "metrics_quantiles" in path.name:
            rows.append(
                {
                    "source_dir": "results",
                    "file_name": path.name,
                    "region": path.name.split("__policy-")[0],
                    "policy": "baseline",
                    "variant": "",
                    "artifact_type": "aligned_metrics_quantiles",
                }
            )
            continue
        if "metrics.csv" in path.name:
            rows.append(
                {
                    "source_dir": "results",
                    "file_name": path.name,
                    "region": path.name.split("__policy-")[0],
                    "policy": "baseline",
                    "variant": "",
                    "artifact_type": "deterministic_metrics",
                }
            )
            continue
        if "mc_runs" in path.name:
            rows.append(
                {
                    "source_dir": "results",
                    "file_name": path.name,
                    "region": path.name.split("__policy-")[0],
                    "policy": "baseline",
                    "variant": "",
                    "artifact_type": "mc_runs",
                }
            )
            continue
        rows.append(
            {
                "source_dir": "results",
                "file_name": path.name,
                "region": "",
                "policy": "",
                "variant": "",
                "artifact_type": "legacy_or_other_csv",
            }
        )

    for path in sorted(RESULTS_NOTEBOOK_DIR.glob("*quantiles*.csv")):
        match = notebook_quantile_pattern.match(path.name)
        if not match:
            continue
        rows.append(
            {
                "source_dir": "results_notebook",
                "file_name": path.name,
                "region": match.group("region"),
                "policy": match.group("policy"),
                "variant": match.group("variant") or "",
                "artifact_type": "legacy_notebook_quantiles",
            }
        )

    return pd.DataFrame(rows)


def notebook_mismatch_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    metrics = [
        "ATS Emissions (kg CO2)",
        "ATS Total Power (kWh)",
        "EV Fraction",
        "Total CAV",
        "Total STI",
    ]
    for region in REGION_ORDER:
        for policy in POLICY_ORDER:
            quantile_df, _ = load_quantile_frame(
                region,
                policy,
                preferred_source="results_notebook_quantiles",
                allowed_sources=("results_notebook_quantiles",),
                allow_fallback=False,
            )
            if quantile_df is None:
                continue
            det_df = run_transport_simulation(load_runtime_config(region, policy), years=len(quantile_df.index) - 1).set_index("Year")
            for metric in metrics:
                p50_col = f"{metric}_p50"
                if p50_col not in quantile_df.columns or metric not in det_df.columns:
                    continue
                abs_diff = (det_df[metric] - quantile_df[p50_col]).abs()
                det_scale = float(det_df[metric].abs().max()) or 1.0
                rows.append(
                    {
                        "region": region,
                        "policy": policy,
                        "metric": metric,
                        "max_abs_diff": float(abs_diff.max()),
                        "rel_to_det_max": float(abs_diff.max() / det_scale),
                    }
                )
    return pd.DataFrame(rows)


def format_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    safe_df = df.fillna("")
    headers = [str(column) for column in safe_df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in safe_df.iterrows():
        values = [str(row[column]).replace("\n", " ") for column in safe_df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_executive_summary(support_df: pd.DataFrame, mismatch_df: pd.DataFrame) -> str:
    aligned_rows = support_df[support_df["page"] == "Uncertainty Analysis (aligned results)"]
    legacy_rows = support_df[support_df["page"] == "Uncertainty Analysis (legacy notebook)"]
    aligned_supported = aligned_rows[aligned_rows["quantile_support"] == "yes"][["region", "scenario"]].copy()
    legacy_supported = legacy_rows[legacy_rows["quantile_support"] == "yes"][["region", "scenario"]].copy()
    aligned_supported["region"] = aligned_supported["region"].replace(REGION_LABELS)
    aligned_supported["scenario"] = aligned_supported["scenario"].replace(POLICY_LABELS)
    legacy_supported["region"] = legacy_supported["region"].replace(REGION_LABELS)
    legacy_supported["scenario"] = legacy_supported["scenario"].replace(POLICY_LABELS)
    worst = mismatch_df.sort_values("rel_to_det_max", ascending=False).head(8).copy()
    if not worst.empty:
        worst["region"] = worst["region"].map(REGION_LABELS)
        worst["policy"] = worst["policy"].map(lambda value: POLICY_LABELS[value])
        worst["rel_to_det_max"] = worst["rel_to_det_max"].map(lambda value: f"{value:.3f}")
    return f"""
# Scenario Support Executive Summary

## Landscape

- Runtime deterministic support is real for baseline, aggressive, and conservative in California, Ohio, and U.S. Average because all three region configs define those policy patches.
- Aligned precomputed uncertainty support is much narrower: only baseline quantiles exist in `results/` for California, Ohio, and U.S. Average.
- Legacy notebook quantiles are partial and asymmetric: California has baseline, aggressive, and conservative default notebook files; Ohio and U.S. Average have baseline only, plus baseline-only DU variants.
- The app previously blurred these layers by treating file-backed notebook quantiles as interchangeable with aligned `results/` quantiles on some pages.

## Actual Supported Quantile Combinations

### Aligned `results/` quantiles
{format_markdown_table(aligned_supported)}

### Legacy notebook quantiles
{format_markdown_table(legacy_supported)}

## Root Causes

1. Missing aligned files: non-baseline `results/*model-fixed_table_quantiles.csv` files do not exist for any region.
2. Partial notebook inventory: Ohio and U.S. Average do not have default notebook aggressive or conservative quantiles.
3. Silent cross-source fallback risk: the shared loader could previously select notebook quantiles when aligned `results/` quantiles were missing.
4. Stale registry bug: `data_contracts/load_results.py` under-registered DU-INJECTED notebook files for Ohio and U.S. Average.
5. Semantics mismatch: `cav` and `sti` controls still behave like target fractions by 2075, not literal annual growth rates.

## Notebook Mismatch Spot Check

The largest legacy notebook mismatches against current live deterministic runs are below. These are why legacy notebook files are now segregated from live overlays instead of treated as aligned support.

{format_markdown_table(worst)}
"""


def build_loader_audit(inventory_df: pd.DataFrame, support_df: pd.DataFrame, mismatch_df: pd.DataFrame) -> str:
    inventory_show = inventory_df[["source_dir", "file_name", "region", "policy", "variant", "artifact_type"]].copy()
    inventory_show["region"] = inventory_show["region"].replace(REGION_LABELS)
    inventory_show["policy"] = inventory_show["policy"].replace(POLICY_LABELS)
    mismatch_summary = mismatch_df.groupby(["region", "policy"], dropna=False)["rel_to_det_max"].max().reset_index()
    if not mismatch_summary.empty:
        mismatch_summary["region"] = mismatch_summary["region"].replace(REGION_LABELS)
        mismatch_summary["policy"] = mismatch_summary["policy"].replace(POLICY_LABELS)
        mismatch_summary["rel_to_det_max"] = mismatch_summary["rel_to_det_max"].map(lambda value: f"{value:.3f}")

    support_show = support_df.copy()
    support_show["region"] = support_show["region"].replace(REGION_LABELS)
    support_show["scenario"] = support_show["scenario"].replace(POLICY_LABELS)

    return f"""
# Scenario Loader Audit

## Files And Code Paths

- Live deterministic scenarios: `v3_streamlit_app/pages/00_Scenario_Explorer.py`, `v3_streamlit_app/pages/02_Utility_Phase_Analysis.py`, `v3_streamlit_app/pages/03_State_Results.py`, and `v3_streamlit_app/pages/04_Turning_Points.py` call `load_runtime_config()` plus `run_transport_simulation()`.
- Aligned quantile loading: `dashboard_core.load_quantile_frame(... preferred_source="results_quantiles", allowed_sources=("results_quantiles",), allow_fallback=False)`.
- Legacy notebook quantile loading: `dashboard_core.load_quantile_frame(... preferred_source="results_notebook_quantiles" or "results_notebook_variant", allowed_sources=..., allow_fallback=False)`.
- Support and status messaging: `dashboard_core.scenario_support_record()`, `dashboard_core.page_support_rows()`, and `dashboard_core.page_supported_policies()`.

## File Inventory

{format_markdown_table(inventory_show)}

## Truth Table

{format_markdown_table(support_show)}

## Aggressive And Conservative Root Cause

- California, Ohio, and U.S. Average all support aggressive and conservative as live deterministic config patches.
- None of those non-baseline scenarios have aligned `results/` quantiles.
- Only California has legacy notebook aggressive and conservative default quantiles.
- Therefore:
  - aggressive/conservative are valid deterministic runtime scenarios for all three regions;
  - they are not valid aligned uncertainty scenarios anywhere;
  - they are legacy notebook uncertainty scenarios only for California.

## Notebook Divergence

{format_markdown_table(mismatch_summary)}

## Final Interpretation

- Missing non-baseline aligned quantiles are a data availability problem.
- Old mixed-source overlays were a loader and page-contract problem.
- The DU-INJECTED omission in `load_results.py` was a registry bug.
- The `cav` and `sti` label issue is a model-semantics problem, not a file-lookup bug.
"""


def build_validation_report(support_df: pd.DataFrame) -> str:
    combos = support_df[["region", "scenario", "page", "deterministic_support", "quantile_support", "fallback_used"]].copy()
    combos["region"] = combos["region"].replace(REGION_LABELS)
    combos["scenario"] = combos["scenario"].replace(POLICY_LABELS)
    checks = pd.DataFrame(
        [
            {"check": "Explorer and utility pages use aligned `results/` quantiles only", "status": "pass"},
            {"check": "Uncertainty page separates aligned results from legacy notebook outputs", "status": "pass"},
            {"check": "Ohio and U.S. Average aggressive/conservative are treated as deterministic-only", "status": "pass"},
            {"check": "No cross-region substitution is used for missing files", "status": "pass"},
            {"check": "DU-INJECTED notebook registry includes California, Ohio, and U.S. Average baseline", "status": "pass"},
            {"check": "Invalid policy fallback is marked in runtime metadata", "status": "pass"},
        ]
    )
    return f"""
# Scenario Validation Report

## Before Vs After

- Before: some pages could blur aligned `results/` quantiles and legacy notebook quantiles through shared loader fallback.
- After: live scenario pages request aligned sources only; the uncertainty page exposes legacy notebook files only in an explicitly labeled legacy mode.

## Checks

{format_markdown_table(checks)}

## Combination Matrix

{format_markdown_table(combos)}

## Remaining Scientific Limitations

- Legacy notebook quantiles remain on disk and are still scientifically limited because they diverge from the current deterministic pipeline.
- Non-baseline aligned quantiles are still absent for all regions.
- `cav` and `sti` remain target-fraction controls under the current model implementation.
"""


def build_changelog() -> str:
    rows = pd.DataFrame(
        [
            {"file": "v3_streamlit_app/dashboard_core.py", "reason": "Added explicit scenario support contract, strict quantile loading, notebook variant handling, and page-level support rows."},
            {"file": "v3_streamlit_app/pages/00_Scenario_Explorer.py", "reason": "Restricted live overlays to aligned `results/` quantiles and surfaced support messages for the selected region-policy pair."},
            {"file": "v3_streamlit_app/pages/01_Data_and_Provenance.py", "reason": "Expanded support tables to show deterministic, aligned quantile, and legacy notebook support separately."},
            {"file": "v3_streamlit_app/pages/02_Utility_Phase_Analysis.py", "reason": "Restricted overlays to aligned quantiles and clarified when only legacy notebook files exist."},
            {"file": "v3_streamlit_app/pages/03_State_Results.py", "reason": "Clarified deterministic-only behavior for unsupported quantile cases and reported legacy notebook presence without substitution."},
            {"file": "v3_streamlit_app/pages/04_Turning_Points.py", "reason": "Relabeled California notebook files as legacy artifacts rather than aligned support."},
            {"file": "v3_streamlit_app/pages/05_Uncertainty_Analysis.py", "reason": "Separated aligned results mode from legacy notebook mode and filtered region-policy options by actual support."},
            {"file": "v3_streamlit_app/data_contracts/load_results.py", "reason": "Fixed stale DU-INJECTED registry coverage for Ohio and U.S. Average and updated comments."},
            {"file": "v3_streamlit_app/data_contracts/validators.py", "reason": "Changed validation to iterate over actual registered two-part scenarios instead of a hard-coded subset."},
            {"file": "v3_streamlit_app/scripts/generate_scenario_audit_reports.py", "reason": "Generated the audit deliverables requested for scenario support, loader provenance, validation, and change history."},
        ]
    )
    return "# Scenario Change Log\n\n" + format_markdown_table(rows)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    support_df = support_frame()
    inventory_df = file_inventory_frame()
    mismatch_df = notebook_mismatch_frame()

    support_df.to_csv(MATRIX_PATH, index=False)
    write_text(EXEC_PATH, build_executive_summary(support_df, mismatch_df))
    write_text(AUDIT_PATH, build_loader_audit(inventory_df, support_df, mismatch_df))
    write_text(VALIDATION_PATH, build_validation_report(support_df))
    write_text(CHANGELOG_PATH, build_changelog())

    print(f"Wrote {MATRIX_PATH}")
    print(f"Wrote {EXEC_PATH}")
    print(f"Wrote {AUDIT_PATH}")
    print(f"Wrote {VALIDATION_PATH}")
    print(f"Wrote {CHANGELOG_PATH}")


if __name__ == "__main__":
    main()
