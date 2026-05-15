"""CLEAR-ATS v5 Scenario Explorer — 312-case usage validation harness.

Sweeps the full matrix described in
audits/final_consistency/USAGE_VALIDATION_ASSERTIONS.md:

  regions × (25 single-lever sweeps + 27 template combinations) × 3 bundles
  = 2 × (25 + 27) × 3 = 312 runs.

For every case, the harness captures:
  - committed-bundle p05, p50, p95 at 2030, 2050, 2075 (what Figure A shades)
  - live deterministic p50 at the same years (what Figure A's red line shows)
  - interpretation-boundary year
  - paper-safe badge state
  - top parameter driver at 2030 / 2050 / 2075
  - any console warnings raised during the run

Output: audits/final_consistency/USAGE_MATRIX_RESULTS.csv
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
V5 = REPO / "v5_streamlit_app"
sys.path.insert(0, str(V5))

from core import (  # noqa: E402
    CAV_LEVEL_TEMPLATES,
    CONTROL_SPECS,
    RETIRE_YEAR_OPTIONS,
    STI_LEVEL_TEMPLATES,
    apply_assumption_templates,
    apply_controls,
    band_metadata,
    controls_from_config,
    interpretation_boundary,
    load_bundle_quantiles,
    load_parameter_contribution_experiment,
    load_runtime_config,
    parameter_default_choices,
    parameter_exploratory_choices,
    parameter_paper_safe_choices,
    run_simulation,
)

OUT_CSV = REPO / "audits" / "final_consistency" / "USAGE_MATRIX_RESULTS.csv"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

METRIC = "ATS Emissions (kg CO2)"
REGIONS = ["california", "ohio"]
BUNDLES = {
    "default":      {"label": "Recommended default",
                     "radio_choices": parameter_default_choices},
    "paper-safe":   {"label": "Paper-safe baseline",
                     "radio_choices": parameter_paper_safe_choices},
    "exploratory":  {"label": "Exploratory",
                     "radio_choices": parameter_exploratory_choices},
}
# Committed quantile files only exist for default and paper-safe. Exploratory
# uses the committed paper-safe band as the closest available reference (the
# Monte-Carlo bundle for exploratory would diverge, but assertion 8 tests
# alignment only on the committed bundles).
BUNDLE_COMMITTED_MAP = {
    "default":     "default",
    "paper-safe":  "paper-safe",
    "exploratory": "paper-safe",
}

YEARS_REPORTED = [2030, 2050, 2075]

LEVER_KEYS = [
    "cav_growth_rate", "sti_growth_rate", "ev_growth_rate",
    "clean_energy_growth_rate", "efficiency_doubling_years",
]


def lever_sweep_positions(region: str) -> list[tuple[str, str, float]]:
    """Yield (lever_key, position_label, value) for the 25 single-lever sweeps.

    Positions: state default, -25%, +25%, slider minimum, slider maximum.
    """
    cfg = load_runtime_config(region, "baseline")
    cv = controls_from_config(cfg, region, "baseline")
    out = []
    for lk in LEVER_KEYS:
        spec = CONTROL_SPECS[lk]
        d = float(cv[lk])
        lo = float(spec["min"])
        hi = float(spec["max"])
        # Clamp ±25% into slider bounds
        minus = max(lo, d * 0.75)
        plus = min(hi, d * 1.25)
        out.append((lk, "state_default",  d))
        out.append((lk, "minus_25pct",    minus))
        out.append((lk, "plus_25pct",     plus))
        out.append((lk, "slider_min",     lo))
        out.append((lk, "slider_max",     hi))
    return out


def template_combinations() -> list[tuple[str, str, int]]:
    cavs = list(CAV_LEVEL_TEMPLATES.keys())[:3]  # 3 templates per axis
    stis = list(STI_LEVEL_TEMPLATES.keys())
    retires = RETIRE_YEAR_OPTIONS
    combos = []
    for c in cavs:
        for s in stis:
            for r in retires:
                combos.append((c, s, r))
    # Task spec: 3 × 3 × 3 = 27 combinations
    assert len(combos) == 27, f"expected 27 template combos, got {len(combos)}"
    return combos


def paper_safe_badge(region: str, policy: str, bundle_name: str,
                     radio_counts: dict[str, int]) -> bool:
    if region == "us_average":
        return False
    if policy != "baseline":
        return False
    if bundle_name == "exploratory":
        return False
    # Paper-safe iff no "high" radios
    return radio_counts.get("high", 0) == 0


def count_radio_levels(choices: dict[str, str]) -> dict[str, int]:
    levels = {"fixed": 0, "low": 0, "medium": 0, "high": 0}
    for v in choices.values():
        if v in levels:
            levels[v] += 1
    return levels


def read_bundle_band(region: str, bundle_committed: str) -> pd.DataFrame | None:
    return load_bundle_quantiles(region, "baseline", bundle_committed)


def read_top_drivers(pcx: pd.DataFrame, region: str) -> dict[int, str]:
    out: dict[int, str] = {}
    if pcx is None or pcx.empty:
        return out
    rg = pcx[pcx["region"] == region]
    if rg.empty:
        rg = pcx[pcx["region"] == "california"]
    for y in YEARS_REPORTED:
        sub = rg[rg["year"] == y]
        if sub.empty:
            out[y] = ""
        else:
            out[y] = str(sub.nlargest(1, "width_over_median").iloc[0]["param_id"])
    return out


def extract_live_p50(cfg: dict, region: str, lever_overrides: dict,
                    cav_lvl: list[float], sti_lvl: list[float],
                    retire_yr: int) -> dict[int, float]:
    cv = controls_from_config(cfg, region, "baseline")
    cv.update(lever_overrides)
    live_cfg = apply_controls(cfg, cv)
    live_cfg = apply_assumption_templates(
        live_cfg,
        cav_levels=cav_lvl,
        sti_levels=sti_lvl,
        retire_year=int(retire_yr),
        fleet_linear=True,
    )
    df = run_simulation(live_cfg, years=68)
    df = df.set_index("Year")
    out = {}
    for y in YEARS_REPORTED:
        out[y] = float(df.loc[y, METRIC]) if y in df.index else float("nan")
    return out


def extract_band_values(band: pd.DataFrame | None) -> dict[str, float]:
    out: dict[str, float] = {}
    if band is None or band.empty:
        for y in YEARS_REPORTED:
            for q in ("p05", "p50", "p95"):
                out[f"bundle_{q}_{y}"] = float("nan")
        out["bundle_interp_boundary"] = float("nan")
        out["bundle_degenerate"] = True
        return out
    for y in YEARS_REPORTED:
        if y in band.index:
            for q in ("p05", "p50", "p95"):
                col = f"{METRIC}_{q}"
                out[f"bundle_{q}_{y}"] = float(band.loc[y, col]) if col in band.columns else float("nan")
        else:
            for q in ("p05", "p50", "p95"):
                out[f"bundle_{q}_{y}"] = float("nan")
    ib = interpretation_boundary(band, metric=METRIC)
    by = ib.get("boundary_year")
    out["bundle_interp_boundary"] = float(by) if by is not None else float("nan")
    meta = band_metadata(band, METRIC)
    out["bundle_degenerate"] = bool(meta.get("degenerate", False))
    return out


def main() -> None:
    warnings.filterwarnings("error", category=RuntimeWarning)
    pcx = load_parameter_contribution_experiment()
    rows: list[dict] = []
    idx = 0
    total_expected = 2 * (25 + 27) * 3
    start = time.time()

    for region in REGIONS:
        cfg = load_runtime_config(region, "baseline")
        cv_default = controls_from_config(cfg, region, "baseline")
        sweeps = lever_sweep_positions(region)
        combos = template_combinations()
        top_by_year = read_top_drivers(pcx, region)

        for bundle_name, bundle_cfg in BUNDLES.items():
            committed = BUNDLE_COMMITTED_MAP[bundle_name]
            band = read_bundle_band(region, committed)
            band_vals = extract_band_values(band)
            radio_choices = bundle_cfg["radio_choices"]()
            radio_counts = count_radio_levels(radio_choices)
            badge = paper_safe_badge(region, "baseline", bundle_name, radio_counts)

            # 25 single-lever sweeps per region, templates at defaults
            for (lever_key, pos_label, pos_val) in sweeps:
                overrides = {lever_key: pos_val}
                warn_list: list[str] = []
                try:
                    live = extract_live_p50(
                        cfg, region, overrides,
                        CAV_LEVEL_TEMPLATES["L3-heavy (default)"],
                        STI_LEVEL_TEMPLATES["Basic-heavy (default)"],
                        12,
                    )
                except Exception as exc:
                    warn_list.append(f"live_sim_error: {exc!r}")
                    live = {y: float("nan") for y in YEARS_REPORTED}

                row = {
                    "case_id": idx,
                    "mode": "lever_sweep",
                    "region": region,
                    "policy": "baseline",
                    "bundle": bundle_name,
                    "committed_bundle": committed,
                    "lever": lever_key,
                    "lever_position": pos_label,
                    "lever_value": pos_val,
                    "cav_template": "L3-heavy (default)",
                    "sti_template": "Basic-heavy (default)",
                    "retire_year": 12,
                    "paper_safe_badge": badge,
                    "radio_fixed": radio_counts["fixed"],
                    "radio_low": radio_counts["low"],
                    "radio_medium": radio_counts["medium"],
                    "radio_high": radio_counts["high"],
                    "top_driver_2030": top_by_year.get(2030, ""),
                    "top_driver_2050": top_by_year.get(2050, ""),
                    "top_driver_2075": top_by_year.get(2075, ""),
                    "live_p50_2030": live[2030],
                    "live_p50_2050": live[2050],
                    "live_p50_2075": live[2075],
                    "warnings": "|".join(warn_list),
                }
                row.update(band_vals)
                rows.append(row)
                idx += 1

            # 27 template combinations per region, levers at state defaults
            for (cav_tmpl, sti_tmpl, retire_yr) in combos:
                warn_list = []
                try:
                    live = extract_live_p50(
                        cfg, region, {},
                        CAV_LEVEL_TEMPLATES[cav_tmpl],
                        STI_LEVEL_TEMPLATES[sti_tmpl],
                        retire_yr,
                    )
                except Exception as exc:
                    warn_list.append(f"live_sim_error: {exc!r}")
                    live = {y: float("nan") for y in YEARS_REPORTED}
                row = {
                    "case_id": idx,
                    "mode": "template_sweep",
                    "region": region,
                    "policy": "baseline",
                    "bundle": bundle_name,
                    "committed_bundle": committed,
                    "lever": "",
                    "lever_position": "state_default_all",
                    "lever_value": float("nan"),
                    "cav_template": cav_tmpl,
                    "sti_template": sti_tmpl,
                    "retire_year": retire_yr,
                    "paper_safe_badge": badge,
                    "radio_fixed": radio_counts["fixed"],
                    "radio_low": radio_counts["low"],
                    "radio_medium": radio_counts["medium"],
                    "radio_high": radio_counts["high"],
                    "top_driver_2030": top_by_year.get(2030, ""),
                    "top_driver_2050": top_by_year.get(2050, ""),
                    "top_driver_2075": top_by_year.get(2075, ""),
                    "live_p50_2030": live[2030],
                    "live_p50_2050": live[2050],
                    "live_p50_2075": live[2075],
                    "warnings": "|".join(warn_list),
                }
                row.update(band_vals)
                rows.append(row)
                idx += 1

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} with {len(df)} rows "
          f"(expected {total_expected}) in {time.time()-start:.1f}s")


if __name__ == "__main__":
    main()
