#!/usr/bin/env python3
"""Validation harness for the v6 single-layer weather module.

Checks:

  1. Monthly weather shares sum to 1 for California and Ohio.
  2. Aggregate annual weather shares sum to 1 under both deterministic
     and stochastic modes, for both regions.
  3. Weather off: v6 run_simulation_v6 equals v5 run_simulation exactly
     (within floating-point tolerance) across all numeric columns.
  4. Deterministic weather mode is stable: running it twice gives
     identical outputs.
  5. Stochastic weather mode is reproducible with a seed: same seed
     produces identical outputs; different seeds produce different
     outputs.
  6. Increasing adverse share raises subsystem sensing and computing
     energy relative to a clear-only reference.
  7. Communication energy is unchanged by weather when the multiplier
     table has no weather sensitivity for communication (it does not,
     by default).
  8. California and Ohio show different CO2 responses to the same
     weather shock, driven by the grid-intensity sensitivity gap.
  9. The v6 One-Time Energy page is not wired through the weather
     module. (Checked by grepping; weather must not appear in that file.)
 10. The Scenario Explorer v6 still uses base year 2024 and display
     horizon 2075.

Usage:
    python scripts/validate_v6_weather.py

Exits non-zero on the first failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
V5_DIR = REPO / "v5_streamlit_app"
V6_DIR = REPO / "v6_weather_singlelayer"

# Make v6 importable (it re-exports v5/v4 helpers too).
for p in (str(REPO), str(V6_DIR), str(V5_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import importlib.util as _ilu

def _load(name: str, path: Path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

weather_module = _load("v6_weather_module", V6_DIR / "weather_module.py")
v6_core = _load("v6_core", V6_DIR / "core.py")
v5_core = _load("v5_core", V5_DIR / "core.py")


FAIL = 0


def _ok(name: str) -> None:
    print(f"  PASS  {name}")


def _fail(name: str, msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {name}\n        {msg}")


# ---------------------------------------------------------------------------
# 1. Monthly shares sum to 1
# ---------------------------------------------------------------------------
print("[1] Monthly weather shares normalised")
for region in ("california", "ohio"):
    prior = weather_module.load_weather_prior(region)
    sums = prior["monthly_shares"].sum(axis=1)
    err = float(np.max(np.abs(sums - 1.0)))
    if err < 1e-6:
        _ok(f"{region}: max |row_sum − 1| = {err:.2e}")
    else:
        _fail(f"{region} monthly shares", f"max deviation {err}")


# ---------------------------------------------------------------------------
# 2. Aggregate annual shares sum to 1
# ---------------------------------------------------------------------------
print("[2] Annual aggregate shares sum to 1")
for region in ("california", "ohio"):
    prior = weather_module.load_weather_prior(region)
    # Deterministic
    annual, _ = weather_module.sample_annual_weather_shares(
        prior["monthly_shares"], prior["month_weights"], mode="deterministic",
    )
    if abs(annual.sum() - 1.0) < 1e-9:
        _ok(f"{region} deterministic: sum = {annual.sum():.9f}")
    else:
        _fail(f"{region} deterministic", f"sum = {annual.sum()}")
    # Stochastic
    rng = np.random.default_rng(42)
    s_ok = True
    for _ in range(50):
        a, _ = weather_module.sample_annual_weather_shares(
            prior["monthly_shares"], prior["month_weights"],
            mode="stochastic", concentration=80.0, rng=rng,
        )
        if abs(a.sum() - 1.0) > 1e-9:
            s_ok = False
            break
    if s_ok:
        _ok(f"{region} stochastic: 50 draws all sum to 1")
    else:
        _fail(f"{region} stochastic", f"sum deviated: {a.sum()}")


# ---------------------------------------------------------------------------
# 3. Weather-off equivalence with v5
# ---------------------------------------------------------------------------
print("[3] Weather off: v6 equals v5 run_simulation numerically")
for region in ("california", "ohio"):
    cfg = v5_core.load_runtime_config(region, "baseline")
    df_v5 = v5_core.run_simulation(cfg, years=10)
    df_v6_off = v6_core.run_simulation_v6(
        cfg, years=10, region=region,
        weather=weather_module.default_settings_off(),
    )
    num_cols = df_v5.select_dtypes(include="number").columns
    max_abs = 0.0
    worst = ""
    for c in num_cols:
        diff = float(np.max(np.abs(df_v5[c].values - df_v6_off[c].values)))
        if diff > max_abs:
            max_abs = diff
            worst = c
    if max_abs < 1e-9:
        _ok(f"{region}: all numeric columns identical (max diff {max_abs:.2e})")
    else:
        _fail(f"{region} weather-off", f"worst column '{worst}' diff {max_abs}")


# ---------------------------------------------------------------------------
# 4. Deterministic stability
# ---------------------------------------------------------------------------
print("[4] Deterministic weather mode is stable")
for region in ("california", "ohio"):
    cfg = v5_core.load_runtime_config(region, "baseline")
    s_det = weather_module.default_settings_on_deterministic()
    df_a = v6_core.run_simulation_v6(cfg, years=10, region=region, weather=s_det)
    df_b = v6_core.run_simulation_v6(cfg, years=10, region=region, weather=s_det)
    diff = float(np.max(np.abs(df_a["ATS Emissions (kg CO2)"].values
                               - df_b["ATS Emissions (kg CO2)"].values)))
    if diff < 1e-9:
        _ok(f"{region}: two runs identical (max diff {diff:.2e})")
    else:
        _fail(f"{region} deterministic stability", f"diff {diff}")


# ---------------------------------------------------------------------------
# 5. Stochastic reproducibility
# ---------------------------------------------------------------------------
print("[5] Stochastic mode reproducible with seed")
for region in ("california", "ohio"):
    cfg = v5_core.load_runtime_config(region, "baseline")
    s1 = weather_module.WeatherSettings(enabled=True, mode="stochastic",
                                        concentration=80.0, seed=7)
    s2 = weather_module.WeatherSettings(enabled=True, mode="stochastic",
                                        concentration=80.0, seed=7)
    s3 = weather_module.WeatherSettings(enabled=True, mode="stochastic",
                                        concentration=80.0, seed=9999)
    df_1 = v6_core.run_simulation_v6(cfg, years=10, region=region, weather=s1)
    df_2 = v6_core.run_simulation_v6(cfg, years=10, region=region, weather=s2)
    df_3 = v6_core.run_simulation_v6(cfg, years=10, region=region, weather=s3)
    diff_same = float(np.max(np.abs(df_1["ATS Emissions (kg CO2)"].values
                                    - df_2["ATS Emissions (kg CO2)"].values)))
    diff_diff = float(np.max(np.abs(df_1["ATS Emissions (kg CO2)"].values
                                    - df_3["ATS Emissions (kg CO2)"].values)))
    if diff_same < 1e-9 and diff_diff > 0:
        _ok(f"{region}: same seed identical (Δ={diff_same:.2e}), different seed differs (Δ={diff_diff:.3e})")
    else:
        _fail(f"{region} stochastic reproducibility",
              f"same-seed diff {diff_same}, diff-seed diff {diff_diff}")


# ---------------------------------------------------------------------------
# 6. Adverse share monotonicity
# ---------------------------------------------------------------------------
print("[6] Increasing adverse share increases sensing & computing energy")
mults = weather_module.load_weather_multipliers()
baseline_like = np.array([1.0, 0.0, 0.0])  # all clear
tweaked_adverse = np.array([0.0, 0.0, 1.0])  # all adverse
for bucket in ("ECAV", "ICECAV", "STI"):
    ratio_adverse_sens = weather_module.subsystem_energy_ratio(
        tweaked_adverse, baseline_like, mults[bucket][0],  # sensing
    )
    ratio_adverse_cmp = weather_module.subsystem_energy_ratio(
        tweaked_adverse, baseline_like, mults[bucket][1],  # computing
    )
    if ratio_adverse_sens > 1.0 and ratio_adverse_cmp > 1.0:
        _ok(f"{bucket}: sensing ratio {ratio_adverse_sens:.3f}, computing ratio {ratio_adverse_cmp:.3f}")
    else:
        _fail(f"{bucket} adverse monotonicity",
              f"sens {ratio_adverse_sens}, cmp {ratio_adverse_cmp}")


# ---------------------------------------------------------------------------
# 7. Communication unchanged under weather
# ---------------------------------------------------------------------------
print("[7] Communication energy unchanged by weather")
for bucket in ("ECAV", "ICECAV", "STI"):
    ratio_comm = weather_module.subsystem_energy_ratio(
        tweaked_adverse, baseline_like, mults[bucket][2],  # communication
    )
    if abs(ratio_comm - 1.0) < 1e-9:
        _ok(f"{bucket} communication ratio {ratio_comm:.3f}")
    else:
        _fail(f"{bucket} communication",
              f"ratio {ratio_comm} != 1.0 (check weather_multipliers.json)")


# ---------------------------------------------------------------------------
# 8. CA vs OH CO2 response divergence
# ---------------------------------------------------------------------------
print("[8] CA and OH CO2 responses to weather differ via grid intensity")
cfg_ca = v5_core.load_runtime_config("california", "baseline")
cfg_oh = v5_core.load_runtime_config("ohio", "baseline")
s_on = weather_module.WeatherSettings(enabled=True, mode="stochastic",
                                      concentration=30.0, seed=2026)
s_off = weather_module.default_settings_off()
df_ca_on = v6_core.run_simulation_v6(cfg_ca, years=10, region="california", weather=s_on)
df_ca_off = v6_core.run_simulation_v6(cfg_ca, years=10, region="california", weather=s_off)
df_oh_on = v6_core.run_simulation_v6(cfg_oh, years=10, region="ohio", weather=s_on)
df_oh_off = v6_core.run_simulation_v6(cfg_oh, years=10, region="ohio", weather=s_off)
ca_ratio = (df_ca_on["ATS Emissions (kg CO2)"].values /
            np.where(df_ca_off["ATS Emissions (kg CO2)"].values == 0, 1,
                     df_ca_off["ATS Emissions (kg CO2)"].values))
oh_ratio = (df_oh_on["ATS Emissions (kg CO2)"].values /
            np.where(df_oh_off["ATS Emissions (kg CO2)"].values == 0, 1,
                     df_oh_off["ATS Emissions (kg CO2)"].values))
# Expect CA and OH ratios to differ because γ_cloudy/γ_adverse differ
# per region (0.10/0.25 vs 0.06/0.15) and baselines differ.
if not np.allclose(ca_ratio, oh_ratio, atol=1e-6):
    _ok(f"CA mean ratio {np.nanmean(ca_ratio):.4f}, OH mean ratio {np.nanmean(oh_ratio):.4f}")
else:
    _fail("CA/OH CO2 divergence",
          "ratios matched to 1e-6; check grid_sensitivity values")


# ---------------------------------------------------------------------------
# 9. One-Time Energy page is not wired through weather
# ---------------------------------------------------------------------------
print("[9] One-Time Energy page has no weather wiring")
ot_src = (V6_DIR / "pages" / "01_One_Time_Energy.py").read_text(encoding="utf-8")
if ("apply_weather_to_results" in ot_src
    or "run_simulation_v6" in ot_src
    or "weather_module" in ot_src):
    _fail("One-Time page scope",
          "weather module appears in 01_One_Time_Energy.py — utility-phase only rule violated")
else:
    _ok("weather module not referenced in 01_One_Time_Energy.py")


# ---------------------------------------------------------------------------
# 10. Base year 2024 / horizon still present in Scenario Explorer v6
# ---------------------------------------------------------------------------
print("[10] Scenario Explorer v6 keeps 2024 base year and 2075 horizon")
se_src = (V6_DIR / "pages" / "00_Scenario_Explorer.py").read_text(encoding="utf-8")
base_ok = "2024" in se_src
horiz_ok = "2075" in se_src or "DISPLAY_MAX_YEAR" in se_src
if base_ok and horiz_ok:
    _ok("2024 base year and 2075 display horizon references present")
else:
    _fail("Scenario Explorer v6 horizon", f"2024={base_ok} 2075/DISPLAY_MAX_YEAR={horiz_ok}")


# ---------------------------------------------------------------------------
print()
if FAIL == 0:
    print("v6 weather module validation: ALL CHECKS PASSED")
    sys.exit(0)
else:
    print(f"v6 weather module validation: {FAIL} CHECK(S) FAILED")
    sys.exit(1)
