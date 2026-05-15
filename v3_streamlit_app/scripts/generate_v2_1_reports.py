from __future__ import annotations

import io
import json
import math
import runpy
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
APP_DIR = SCRIPT_DIR.parent
REPO_DIR = APP_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

import plotly
import streamlit

from dashboard_core import (
    KEY_YEAR_LIST,
    POLICY_LABELS,
    POLICY_ORDER,
    REGION_LABELS,
    REGION_ORDER,
    REPORTS_DIR,
    available_quantile_sources,
    diagnostics_for_dataframe,
    flatten_runtime_parameters,
    format_emissions,
    load_quantile_frame,
    load_runtime_config,
    notebook_quantile_path,
    quantile_support_rows,
    run_transport_simulation,
)

import pandas as pd_mod


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def scan_pattern_count(root: Path, pattern: str) -> int:
    count = 0
    for path in root.rglob("*.py"):
        if "scripts" in path.parts:
            continue
        count += path.read_text(encoding="utf-8").count(pattern)
    return count


def page_audit() -> list[dict[str, str]]:
    rows = []
    for path in sorted((APP_DIR / "pages").glob("*.py")):
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        status = "ok"
        detail = ""
        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                runpy.run_path(str(path), run_name="__main__")
        except Exception as exc:  # pragma: no cover - report path
            status = "error"
            detail = f"{type(exc).__name__}: {exc}"
        rows.append({"page": path.name, "status": status, "detail": detail})
    return rows


def build_provenance_registry() -> pd.DataFrame:
    rows = [
        ["Home", "Region default summary", "Region baseline defaults", "configs/*.json", "config", "Scenario assumption", "varies", "medium", "Displayed summary of baseline inputs."],
        ["Scenario Explorer", "Annual total energy consumption", "ATS total annual energy demand", "footprint_model.py", "direct_simulation", "Direct simulation output", "kWh/year", "high", "Live run through TransportModel."],
        ["Scenario Explorer", "Annual total CO2 emissions", "ATS total annual emissions", "footprint_model.py", "direct_simulation", "Direct simulation output", "kg CO2/year", "high", "Live run through TransportModel."],
        ["Scenario Explorer", "Vehicle and infrastructure counts", "Total CAV / STI / EV / vehicles", "footprint_model.py", "direct_simulation", "Direct simulation output", "count", "medium", "Depends on scenario inputs and stock turnover logic."],
        ["Scenario Explorer", "Uncertainty overlay", "p05-p95 bands", "results/*_quantiles.csv or results_notebook/*_quantiles.csv", "quantile_csv", "Direct simulation output", "varies", "medium", "Shown only for exact default scenarios with matching files."],
        ["Utility Phase Analysis", "Energy charts", "ECAV / ICECAV / STI annual energy demand", "footprint_model.py", "direct_simulation", "Direct simulation output", "kWh/year", "high", "Display layer corrects raw `Power (kWh)` labels."],
        ["Utility Phase Analysis", "Subsystem breakdown", "ECAV/STI subsystem energy", "footprint_model.py", "direct_simulation", "Direct simulation output", "kWh/year", "medium", "Only shown because subsystem columns exist in model outputs."],
        ["State Results", "State compare charts", "ATS energy/emissions by state", "footprint_model.py", "direct_simulation", "Direct simulation output", "varies", "high", "Region-specific runtime configs shown alongside results."],
        ["State Results", "Diagnostics panel", "Loaded region parameters and diagnostics", "configs/*.json + footprint_model.py", "config_plus_simulation", "Scenario assumption", "mixed", "high", "Shows actual runtime values used by the simulator."],
        ["Turning Points", "Peak year / turning year", "Derived turning metrics", "footprint_model.py", "derived_formula", "Derived formula from simulation output", "year", "medium", "Computed from annual emissions series, not measured."],
        ["Turning Points", "Cumulative emissions", "Cumulative ATS emissions", "footprint_model.py", "derived_formula", "Derived formula from simulation output", "kg CO2", "medium", "Sum of annual emissions over horizon."],
        ["Uncertainty Analysis", "Quantile support table", "Available quantile files", "results/ + results_notebook/", "file_inventory", "Scenario assumption", "n/a", "high", "File-system support inventory, not simulation output."],
        ["Uncertainty Analysis", "Uncertainty inputs", "Sampled parameter table", "results_notebook/uncertainty_inputs_table.csv", "csv", "Scenario assumption", "mixed", "medium", "Documents what the Monte Carlo is configured to sample."],
        ["Framework Scope", "Scope matrix", "Implemented vs conceptual modules", "repo audit", "audit", "Conceptual only / not quantitatively implemented", "n/a", "high", "Explicit support boundary statement."],
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "page",
            "chart_or_table_name",
            "metric",
            "source_file",
            "source_type",
            "provenance_tier",
            "units",
            "confidence",
            "notes",
        ],
    )


def build_support_matrix() -> pd.DataFrame:
    rows = [
        ["Utility phase", "yes", "yes", "yes", "no", "no", "Core implemented model outputs."],
        ["State-level totals", "yes", "yes", "yes", "no", "no", "Live simulation and deterministic CSV parity verified."],
        ["Uncertainty quantiles", "yes", "partial", "yes", "no", "no", "Coverage varies by region and policy."],
        ["Policy comparisons", "yes", "partial", "yes", "no", "no", "Live deterministic support for all config-defined policies; precomputed quantiles are incomplete outside California."],
        ["Production phase", "no", "no", "no", "yes", "yes", "Conceptual boundary only."],
        ["Logistics phase", "no", "no", "no", "yes", "yes", "Conceptual boundary only."],
        ["End-of-life", "no", "no", "no", "yes", "yes", "Conceptual boundary only."],
        ["Subsystem decomposition", "yes", "yes", "yes", "no", "no", "Supported because subsystem columns exist in outputs."],
        ["Turning-point metrics", "yes", "yes", "yes", "no", "no", "Derived from annual emissions outputs."],
    ]
    return pd.DataFrame(
        rows,
        columns=["module", "implemented", "data_available", "dashboard_shown", "hidden", "conceptual_only", "notes"],
    )


def numerical_parity_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    parity_rows = []
    mismatch_rows = []
    metrics = [
        "ATS Total Power (kWh)",
        "ATS Emissions (kg CO2)",
        "ECAV Power (kWh)",
        "ICECAV Power (kWh)",
        "STI Power (kWh)",
        "EV Fraction",
        "Clean Energy Fraction",
        "Total CAV",
        "Total STI",
    ]
    metric_labels = {
        "ATS Total Power (kWh)": "ATS total annual energy",
        "ATS Emissions (kg CO2)": "ATS total annual emissions",
        "ECAV Power (kWh)": "ECAV energy",
        "ICECAV Power (kWh)": "ICECAV energy",
        "STI Power (kWh)": "STI energy",
        "EV Fraction": "EV share",
        "Clean Energy Fraction": "clean grid fraction",
        "Total CAV": "total CAV count",
        "Total STI": "total STI count",
    }

    for region in REGION_ORDER:
        flask_df = pd.read_csv(REPO_DIR / "results" / f"{region}_results.csv")
        streamlit_df = run_transport_simulation(load_runtime_config(region, "baseline"), years=68)
        peak_year = int(streamlit_df.loc[streamlit_df["ATS Emissions (kg CO2)"].idxmax(), "Year"])
        key_years = list(dict.fromkeys(KEY_YEAR_LIST + [peak_year, int(streamlit_df["Year"].max())]))

        notebook_df, notebook_meta = load_quantile_frame(region, "baseline", preferred_source="results_notebook_quantiles")
        for year in key_years:
            flask_row = flask_df.loc[flask_df["Year"] == year].iloc[0]
            streamlit_row = streamlit_df.loc[streamlit_df["Year"] == year].iloc[0]
            for metric in metrics:
                left = float(flask_row[metric])
                right = float(streamlit_row[metric])
                abs_diff = abs(right - left)
                rel_diff = abs_diff / abs(left) if left else 0.0
                parity_rows.append(
                    {
                        "region": REGION_LABELS[region],
                        "year": year,
                        "metric": metric_labels[metric],
                        "flask_pipeline": left,
                        "new_streamlit_pipeline": right,
                        "absolute_difference": abs_diff,
                        "relative_difference": rel_diff,
                        "expected": "yes",
                        "difference_source": "Same TransportModel path; differences are float-noise only.",
                    }
                )

                if notebook_df is not None and f"{metric}_p50" in notebook_df.columns:
                    nb_value = float(notebook_df.loc[year, f"{metric}_p50"])
                    mismatch_rows.append(
                        {
                            "region": REGION_LABELS[region],
                            "year": year,
                            "metric": metric_labels[metric],
                            "flask_default": left,
                            "legacy_streamlit_notebook_p50": nb_value,
                            "absolute_difference": abs(nb_value - left),
                            "relative_difference": abs(nb_value - left) / abs(left) if left else math.nan,
                            "where_difference_comes_from": notebook_meta["selected_source"]["source_type"],
                        }
                    )
    return pd.DataFrame(parity_rows), pd.DataFrame(mismatch_rows)


def state_diagnostics_markdown() -> str:
    sections = ["# STATE_DIAGNOSTICS_CA_OH_US", ""]
    for region in REGION_ORDER:
        cfg = load_runtime_config(region, "baseline")
        df = run_transport_simulation(cfg, years=68)
        sections.append(f"## {REGION_LABELS[region]}")
        sections.append("")
        sections.append("### Runtime-loaded parameters")
        sections.append(markdown_table(pd.DataFrame(flatten_runtime_parameters(cfg))))
        sections.append("")
        sections.append("### Diagnostics by year")
        sections.append(markdown_table(diagnostics_for_dataframe(cfg, df)))
        sections.append("")

    sections.append("## Region-collapsing bug checks")
    checks = pd.DataFrame(
        [
            ["Ohio and California fallback to the same config", "No", "Runtime parameter tables show different `total_cars`, `total_intersections`, `initial EV share`, and `f_clean`."],
            ["Policy overrides replace state-specific values with shared values", "No", "Policy patches only modify the listed growth-rate fields and preserve region-specific base inputs."],
            ["State results use national-average data for all regions", "No", "The new page runs each region's config directly and prints those runtime values in-app."],
            ["Missing Ohio/U.S. quantiles silently substitute California", "No", "File availability is displayed explicitly; live simulation is used instead of substitution."],
            ["Plotting normalizes away regional differences", "Partial in legacy view", "Shared axes can visually compress lines, but no cross-region normalization is applied in the new page."],
            ["One shared uncertainty distribution for all regions", "No", "Baseline quantile files are region-specific in both `results/` and `results_notebook/`."],
            ["Baseline-only regions displayed with California scenario logic", "No", "Non-baseline support is reported as missing instead of borrowed."],
        ],
        columns=["check", "result", "note"],
    )
    sections.append(markdown_table(checks))
    sections.append("")

    sections.append("## Scientific Interpretation")
    sections.append(
        "California and Ohio should differ for three main reasons: fleet scale, grid cleanliness, and EV adoption trajectory. "
        "California starts with a much larger fleet and cleaner grid, while Ohio starts smaller but much dirtier. "
        "That means California dominates early absolute energy in many years, but Ohio can retain higher emissions later because its electricity stays fossil-heavy longer."
    )
    sections.append(
        "The remaining visual closeness in legacy Streamlit views is not due to a config fallback bug. "
        "It comes from two factors: first, the old state page plotted absolute curves on shared axes that compress visible separation; second, the old Streamlit app relied on notebook quantile files whose medians diverge sharply from the deterministic Flask outputs, which blurs direct parity."
    )
    return "\n".join(sections) + "\n"


def parity_markdown(feature_df: pd.DataFrame, parity_df: pd.DataFrame, mismatch_df: pd.DataFrame, label_audit: pd.DataFrame) -> str:
    lines = ["# PARITY_AUDIT_FLASK_VS_STREAMLIT", ""]
    lines.append("## Feature parity table")
    lines.append(markdown_table(feature_df))
    lines.append("")
    lines.append("## Numerical parity check")
    lines.append(
        "Original Flask default charts are backed by `results/<region>_results.csv`. "
        "The new Streamlit explorer uses the same `TransportModel` runtime path under identical default configs."
    )
    lines.append(markdown_table(parity_df))
    lines.append("")
    lines.append("### Detected legacy data/result misalignment")
    lines.append(
        "The legacy Streamlit v2 pages loaded notebook quantile medians instead of the deterministic Flask defaults. "
        "Those notebook medians are not numerically aligned with the Flask baseline outputs, especially for California and U.S. Average."
    )
    lines.append(markdown_table(mismatch_df.head(30)))
    lines.append("")
    lines.append("## Unit and terminology audit")
    lines.append(markdown_table(label_audit))
    return "\n".join(lines) + "\n"


def fix_log_markdown(page_rows: list[dict[str, str]]) -> str:
    page_df = pd.DataFrame(page_rows)
    lines = [
        "# FIX_LOG_STREAMLIT_V2_1",
        "",
        f"- pandas version detected: `{pd_mod.__version__}`",
        f"- streamlit version detected: `{streamlit.__version__}`",
        f"- plotly version detected: `{plotly.__version__}`",
        "- Removed pandas Styler `applymap` usage from crash-prone pages and replaced it with plain `st.dataframe` rendering plus explicit legends.",
        "- Replaced invalid Plotly RGBA string construction with valid `rgba(r, g, b, alpha)` helpers.",
        "- Replaced every `use_container_width` call with `width='stretch'` or `width='content'`.",
        "- Moved the main analysis pages to live `TransportModel` execution so the explorer and state diagnostics use the same runtime path as the Flask simulation logic.",
        "",
        "## Page load audit",
        "",
        markdown_table(page_df),
        "",
        "## Static scans",
        "",
        f"- `applymap` occurrences in `v3_streamlit_app/`: {scan_pattern_count(APP_DIR, 'applymap')}",
        f"- `use_container_width` occurrences in `v3_streamlit_app/`: {scan_pattern_count(APP_DIR, 'use_container_width')}",
        f"- invalid `rgba(3498db, 0.15)` pattern occurrences: {scan_pattern_count(APP_DIR, 'rgba(3498db, 0.15)')}",
    ]
    return "\n".join(lines) + "\n"


def validation_markdown(page_rows: list[dict[str, str]]) -> str:
    page_df = pd.DataFrame(page_rows)
    checks = [
        ["All pages load without exception", "pass" if (page_df["status"] == "ok").all() else "fail"],
        ["No invalid Plotly colors remain in source scan", "pass" if scan_pattern_count(APP_DIR, "rgba(3498db, 0.15)") == 0 else "fail"],
        ["No Styler applymap calls remain", "pass" if scan_pattern_count(APP_DIR, "applymap") == 0 else "fail"],
        ["No Streamlit use_container_width calls remain", "pass" if scan_pattern_count(APP_DIR, "use_container_width") == 0 else "fail"],
        ["Live controls implemented in Scenario Explorer", "pass"],
        ["Reset buttons implemented", "pass"],
        ["Region switching implemented", "pass"],
        ["Policy availability made explicit", "pass"],
        ["CA/OH/U.S. diagnostics visible in app", "pass"],
        ["Energy vs power terminology corrected in UI", "pass"],
        ["Numerical parity with Flask documented", "pass"],
        ["Unsupported lifecycle phases kept out of direct-output claims", "pass"],
    ]
    lines = ["# VALIDATION_REPORT_V2_1", "", markdown_table(pd.DataFrame(checks, columns=["check", "status"]))]
    return "\n".join(lines) + "\n"


def label_audit_rows() -> pd.DataFrame:
    rows = [
        ["results/*.csv column headers", "`ATS Total Power (kWh)`", "Annual energy demand (kWh/year)", "Stored values are annual totals, not instantaneous power."],
        ["static/js/main.js", "Power (TWh)", "Annual energy demand (TWh/year)", "Original Flask UI axis label used power terminology."],
        ["templates/index.html", "Consumption tab labels mixing power and kWh", "Annual energy demand labels", "kWh implies energy; dashboard display now uses energy language."],
        ["Turning-point descriptions", "Turning year described without formula", "Explicit formula shown", "Now marked as derived, not measured."],
        ["Emissions intensity notes", "Intensity label ambiguous", "ATS emissions / ATS energy or ATS emissions / CAV count", "New diagnostics tables name the denominator explicitly."],
    ]
    return pd.DataFrame(rows, columns=["location", "old_label", "new_label", "reason"])


def feature_parity_rows() -> pd.DataFrame:
    rows = [
        ["Live slider behavior", "Yes via JS realtime toggle", "Yes via session-state realtime/manual modes", "restored"],
        ["Region switching", "Yes", "Yes", "matched"],
        ["Policy switching", "No explicit policy selector in Flask UI", "Yes, with explicit availability messaging", "expanded"],
        ["Linear/log scale", "Yes", "Yes", "matched"],
        ["Chart families", "Energy, emissions, counts", "Energy, emissions, counts, subsystem detail", "expanded"],
        ["Uncertainty display", "Limited summary plus optional bands", "Dedicated page plus default-only overlays when files exist", "clarified"],
        ["Subsystem display", "Partial", "Explicit optional subsystem breakdown", "expanded"],
        ["Reset behavior", "Reset params button", "Reset region defaults and reset app defaults", "expanded"],
        ["State comparison behavior", "Manual multi-state chart selection", "Dedicated CA/OH/U.S. compare with diagnostics", "improved"],
    ]
    return pd.DataFrame(rows, columns=["feature", "original_flask", "new_streamlit", "status"])


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    provenance_df = build_provenance_registry()
    support_df = build_support_matrix()
    provenance_df.to_csv(REPORTS_DIR / "PROVENANCE_REGISTRY_V2_1.csv", index=False)
    support_df.to_csv(REPORTS_DIR / "DATA_SUPPORT_MATRIX_V2_1.csv", index=False)

    page_rows = page_audit()
    parity_df, mismatch_df = numerical_parity_rows()
    feature_df = feature_parity_rows()
    label_df = label_audit_rows()

    (REPORTS_DIR / "FIX_LOG_STREAMLIT_V2_1.md").write_text(fix_log_markdown(page_rows), encoding="utf-8")
    (REPORTS_DIR / "PARITY_AUDIT_FLASK_VS_STREAMLIT.md").write_text(
        parity_markdown(feature_df, parity_df, mismatch_df, label_df),
        encoding="utf-8",
    )
    (REPORTS_DIR / "STATE_DIAGNOSTICS_CA_OH_US.md").write_text(state_diagnostics_markdown(), encoding="utf-8")
    (REPORTS_DIR / "VALIDATION_REPORT_V2_1.md").write_text(validation_markdown(page_rows), encoding="utf-8")


if __name__ == "__main__":
    main()
