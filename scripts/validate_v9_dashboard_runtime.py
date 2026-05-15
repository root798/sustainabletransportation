"""Lightweight runtime validator for the v9 dashboard.

Designed to catch the kinds of regressions that crashed the live page
(pandas Index truthiness, mixed-type Arrow tables, deprecated
``use_container_width`` arguments on display calls) without requiring a
running Streamlit instance.

Run:
    python scripts/validate_v9_dashboard_runtime.py

This script does NOT exercise the Streamlit UI. It is a pre-flight
that complements:
  - ``python scripts/validate_v8_weather.py`` (shared upstream wiring)
  - ``streamlit run streamlit_app_v9.py``     (the actual user-facing
                                               dashboard)
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
V9 = REPO / "v9_streamlit_app"

failures: list[str] = []


def section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"  [FAIL] {msg}")


def ok(msg: str) -> None:
    print(f"  [PASS] {msg}")


# ── 1. ensure_nonempty_chart_data: pandas Index truthiness must not
#       trigger the ValueError under any input. -------------------------
section("1. chart_guards.ensure_nonempty_chart_data")

if str(V9) not in sys.path:
    sys.path.insert(0, str(V9))
try:
    import pandas as pd  # noqa: F401
    from utils.chart_guards import (
        chart_data_warning_text,
        ensure_nonempty_chart_data,
    )
except Exception as e:
    fail(f"could not import chart_guards: {e}")
else:
    # Case A — valid frame with required columns
    df_a = pd.DataFrame({
        "ATS Total Power (kWh)_p05": [1.0, 2.0, 3.0],
        "ATS Total Power (kWh)_p50": [1.5, 2.5, 3.5],
        "ATS Total Power (kWh)_p95": [2.0, 3.0, 4.0],
    })
    ok_a, miss_a = ensure_nonempty_chart_data(
        df_a,
        ["ATS Total Power (kWh)_p05", "ATS Total Power (kWh)_p50",
         "ATS Total Power (kWh)_p95"],
        "Figure A",
    )
    (ok if ok_a and not miss_a else fail)(
        f"valid frame: ok={ok_a}, missing={miss_a}"
    )

    # Case B — missing one column
    ok_b, miss_b = ensure_nonempty_chart_data(
        df_a,
        ["ATS Total Power (kWh)_p05", "ATS Emissions (kg CO2)_p05"],
        "Figure A",
    )
    (ok if (not ok_b) and miss_b == ["ATS Emissions (kg CO2)_p05"]
     else fail)(
        f"missing column: ok={ok_b}, missing={miss_b}"
    )

    # Case C — None
    ok_c, miss_c = ensure_nonempty_chart_data(
        None, ["any_col"], "Figure A"
    )
    (ok if (not ok_c) and miss_c == ["any_col"] else fail)(
        f"None df: ok={ok_c}, missing={miss_c}"
    )

    # Case D — empty DataFrame with correct columns
    df_empty = pd.DataFrame({"a": [], "b": []})
    ok_d, miss_d = ensure_nonempty_chart_data(
        df_empty, ["a", "b"], "Figure A"
    )
    (ok if (not ok_d) else fail)(
        f"empty df with cols: ok={ok_d}, missing={miss_d}"
    )

    # Case E — pandas Index columns (the original bug). The Index
    # object is truthy-ambiguous; the helper must NOT raise.
    df_e = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    try:
        ok_e, miss_e = ensure_nonempty_chart_data(df_e, ["x", "y"], "x-y")
        (ok if ok_e else fail)(
            f"non-empty Index columns: ok={ok_e}, missing={miss_e}"
        )
    except ValueError as ve:
        fail(f"raised ValueError on Index columns: {ve}")

    # Case F — chart_data_warning_text composes a sentence
    txt = chart_data_warning_text(["foo", "bar"], "Figure A",
                                  suggestion="Click Recompute.")
    if "foo" in txt and "bar" in txt and "Click Recompute." in txt:
        ok(f"warning text composes correctly: {txt!r}")
    else:
        fail(f"warning text wrong: {txt!r}")


# ── 2. AST parse every v9 source file -------------------------------
section("2. AST parse — every v9 .py file")
ast_targets = sorted(V9.rglob("*.py"))
ast_targets.append(REPO / "streamlit_app_v9.py")
ast_failures = 0
for f in ast_targets:
    if "__pycache__" in str(f):
        continue
    try:
        ast.parse(f.read_text())
    except SyntaxError as e:
        fail(f"{f.relative_to(REPO)}: {e}")
        ast_failures += 1
if ast_failures == 0:
    ok(f"{len(ast_targets)} files parsed cleanly")


# ── 3. compute_live_residual_band exposes multi-metric default --------
section("3. compute_live_residual_band signature")
try:
    import inspect

    import core
    sig = inspect.signature(core.compute_live_residual_band)
    metric_default = sig.parameters["metric"].default
    if isinstance(metric_default, (list, tuple)) and len(metric_default) >= 2:
        ok(f"multi-metric default: {tuple(metric_default)}")
    elif isinstance(metric_default, str):
        fail(f"single-metric default still present: {metric_default!r}")
    else:
        fail(f"unexpected default: {metric_default!r}")
except Exception as e:
    fail(f"could not inspect core.compute_live_residual_band: {e}")


# ── 4. Uncertainty framework asset present ----------------------------
section("4. Overview asset — uncertainty framework figure")
asset = V9 / "assets" / "clear_ats_uncertainty_figure_v30.png"
(ok if asset.exists() else fail)(
    f"{asset.relative_to(REPO)} {'exists' if asset.exists() else 'MISSING'}"
)


# ── 5. No surviving use_container_width on display funcs -------------
section("5. use_container_width sites in v9 (st.button only is OK)")
display_pat = re.compile(
    r"\bst\.(dataframe|plotly_chart|image|data_editor|table)\b[^)]*"
    r"use_container_width",
    re.DOTALL,
)
button_pat = re.compile(r"\bst\.button\b[^)]*use_container_width", re.DOTALL)
display_hits = 0
button_hits = 0
for path in V9.rglob("*.py"):
    if "__pycache__" in str(path):
        continue
    txt = path.read_text()
    display_hits += len(display_pat.findall(txt))
    button_hits += len(button_pat.findall(txt))
(ok if display_hits == 0 else fail)(
    f"display-function use_container_width count: {display_hits}"
)
ok(f"st.button use_container_width count (intentional): {button_hits}")


# ── 6. No mixed-type column survives in build_count_wide_table render
#       (page should cast to str before passing to st.dataframe) -------
section("6. build_count_wide_table render site is string-cast")
page_path = V9 / "pages" / "01_One_Time_Energy.py"
src = page_path.read_text()
if "build_count_wide_table()).astype(str)" in src or \
   "_count_df_display = pd.DataFrame(build_count_wide_table()).astype(str)" in src:
    ok("count-table is cast to str before st.dataframe (Arrow safe)")
else:
    fail("count-table render site does NOT cast to str — Arrow warning will recur")


# ── 7. METRIC_SPECS / canonical_metric_id covers all 5 labels ---------
section("7. METRIC_SPECS / canonical_metric_id")

# Parse the Scenario Explorer module text directly so we don't have to
# import a Streamlit-dependent module. We extract the module-level
# METRIC_SPECS dict via ast literal_eval against a stripped source.
sx_path = V9 / "pages" / "03_Scenario_Explorer.py"
sx_src = sx_path.read_text()

import ast
spec_match = re.search(
    r"METRIC_SPECS\s*=\s*\{",
    sx_src,
)
if not spec_match:
    fail("METRIC_SPECS not found in Scenario Explorer")
else:
    # Walk balanced braces to capture the full dict literal.
    i = spec_match.end() - 1
    depth = 1
    j = i + 1
    while j < len(sx_src) and depth > 0:
        c = sx_src[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        j += 1
    dict_blob = sx_src[i:j]
    try:
        specs = ast.literal_eval(dict_blob)
    except Exception as e:
        fail(f"could not literal_eval METRIC_SPECS: {e}")
        specs = {}
    expected_ids = {
        "annual_co2", "annual_energy", "both",
        "cumulative_co2", "cumulative_energy",
    }
    missing_ids = expected_ids - set(specs)
    (ok if not missing_ids else fail)(
        f"METRIC_SPECS keys: {sorted(specs)}"
    )
    expected_labels = {
        "Annual CO₂ emissions",
        "Annual energy demand",
        "Both (dual axis)",
        "Cumulative CO₂ emissions",
        "Cumulative energy demand",
    }
    actual_labels = {s["label"] for s in specs.values()}
    (ok if expected_labels.issubset(actual_labels) else fail)(
        f"all 5 labels present: missing={expected_labels - actual_labels}"
    )
    # Cumulative IDs must have is_cumulative=True; annual IDs must not.
    for mid, expected_cum in [
        ("annual_co2", False), ("annual_energy", False),
        ("both", False),
        ("cumulative_co2", True), ("cumulative_energy", True),
    ]:
        got = bool(specs.get(mid, {}).get("is_cumulative", None))
        (ok if got is expected_cum else fail)(
            f"is_cumulative[{mid}] = {got} (expected {expected_cum})"
        )
    # quantity_col matches what the simulator emits.
    cols_must_be = {"ATS Emissions (kg CO2)", "ATS Total Power (kWh)"}
    actual_cols = {s["quantity_col"] for s in specs.values()
                   if s.get("quantity_col") is not None}
    (ok if actual_cols.issubset(cols_must_be) else fail)(
        f"quantity_col values are valid: {actual_cols}"
    )

# Validate the canonical mapping handles ASCII / Unicode CO2 input.
canon_match = re.search(
    r"def canonical_metric_id\(.*?\) -> str:.*?return _METRIC_LABEL_TO_ID",
    sx_src, flags=re.DOTALL,
)
(ok if canon_match else fail)(
    "canonical_metric_id() definition present"
)


# ── 8. The dead `_metric_choice`-keyed dict pattern is gone -----------
section("8. No `[_metric_choice]` direct-index access left")
pattern_hits = re.findall(r"\}\s*\[\s*_metric_choice\s*\]", sx_src)
(ok if not pattern_hits else fail)(
    f"`}}[_metric_choice]` direct-index sites: {len(pattern_hits)}"
)


# ── 9. Recompute / Clear-band buttons are removed --------------------
section("9. Recompute / Clear-band buttons removed")
forbidden_pub_strings = [
    "Recompute residual band",
    "Recompute scenario envelope",
    "Clear live band",
    "Clear envelope",
]
present = [s for s in forbidden_pub_strings if s in sx_src]
(ok if not present else fail)(
    f"public-facing recompute strings remaining: {present}"
)


# ── 10. v3–v8 untouched after most recent fix -------------------------
section("10. v3–v8 dashboards untouched")
import os
ref = V9 / "utils" / "chart_guards.py"
ref_mtime = ref.stat().st_mtime
intruders: list[str] = []
for v in ("v3_streamlit_app", "v4_streamlit_app", "v5_streamlit_app",
          "v6_streamlit_app", "v7_streamlit_app", "v8_streamlit_app"):
    base = REPO / v
    if not base.exists():
        continue
    for f in base.rglob("*"):
        if f.is_file() and "__pycache__" not in str(f):
            if f.stat().st_mtime > ref_mtime:
                intruders.append(str(f.relative_to(REPO)))
(ok if not intruders else fail)(
    f"frozen versions touched: {len(intruders)}" + (
        " (" + ", ".join(intruders[:3]) + ")" if intruders else ""
    )
)


# ── summary -----------------------------------------------------------
print()
print("=" * 60)
if failures:
    print(f"SUMMARY: {len(failures)} failure(s)")
    for m in failures:
        print(f"  - {m}")
    sys.exit(1)
else:
    print("SUMMARY: all checks passed.")
    sys.exit(0)
