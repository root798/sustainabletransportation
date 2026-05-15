# PARAMETER_LEVEL_PRESET_TABLE.md

**Date:** 2026-04-15
**Purpose:** single-source numerical table for every parameter's allowed levels. This is the human-readable view of `configs/ui_parameter_presets/*.json` consumed by the v4 Uncertainty Panel.
**Authoritative JSON files:** 8 group files under `configs/ui_parameter_presets/` plus `_registry_index.json`.

**Level semantics** (from `_registry_index.json`):

- `fixed`: parameter held at deterministic central value; no Monte Carlo draw.
- `low`: narrow evidence-anchored or decision-meaningful spread.
- `medium`: paper-safe baseline spread; reproduces committed Monte Carlo ensemble.
- `high`: exploratory wider spread; not paper-safe; clearly labelled in UI.

---

## 1. L1 — baseline data and emission factors

### L1 initial state (`l1_initial_state.json`)

| Parameter | Allowed levels | Default | Paper-safe | fixed | low | medium |
|---|---|---|---|---|---|---|
| F01 `initial_data.f_clean` | fixed, low, medium | **fixed** | medium | region mean | beta(mean, κ×2) | beta(mean, κ) |
| F02 `initial_data.ev_share` | fixed, low, medium | **fixed** | medium | region mean | beta(mean, κ×2) | beta(mean, κ) |

(`region mean` and `κ` are substituted from `scenarios/{region}/scenario.json`.)

### L1 emission factors (`l1_emission_factors.json`)

| Parameter | Allowed | Default | Paper-safe | fixed | low | medium |
|---|---|---|---|---|---|---|
| F03 `e_clean`    | fixed, low, medium | **low** | medium | 0.03  | tri(0.02, 0.03, 0.05) | tri(0.01, 0.03, 0.08) |
| F04 `e_fossil`   | fixed, low, medium | **low** | medium | 0.50  | tri(0.40, 0.50, 0.60) | tri(0.35, 0.50, 0.65) |
| F05 `e_gasoline` | fixed, low, medium | **low** | medium | 1.65  | tri(1.55, 1.65, 1.75) | tri(1.45, 1.65, 1.85) |

**Why no HIGH for L1.** Widening these beyond MEDIUM is not supported by evidence; the methodological span (operational vs life-cycle) is already captured by MEDIUM.

## 2. L2 — load-model parameters

### L2 ECAV scale factors (`l2_ecav_scale_factors.json`)

| Parameter | Allowed | Default | Paper-safe | fixed | low | medium |
|---|---|---|---|---|---|---|
| F06 `ecav_sf.L3`            | fixed, medium | **fixed** | medium | 1.0 | — | lognormal(1, σ=0.15) |
| F07 `ecav_sf.L4`            | fixed, medium | **fixed** | medium | 1.0 | — | lognormal(1, σ=0.20) |
| F08 `ecav_sf.L5`            | fixed, medium | **fixed** | medium | 1.0 | — | lognormal(1, σ=0.25) |
| F09 `ecav_sf.sensing`       | fixed, low, medium | **low** | medium | 1.0 | lognormal(1, σ=0.20) | lognormal(1, σ=0.30) |
| F10 `ecav_sf.computing`     | fixed, low, medium | **low** | medium | 1.0 | lognormal(1, σ=0.15) | lognormal(1, σ=0.20) |
| F11 `ecav_sf.communication` | fixed, low, medium | **low** | medium | 1.0 | lognormal(1, σ=0.25) | lognormal(1, σ=0.35) |

**Why fixed is the only non-paper-safe option for F06–F08.** Dossier S2-01 dual-axis duplication. LOW is undefined because removing the axis entirely (=fixed) is the scientifically defensible action.

### L2 STI scale factors (`l2_sti_scale_factors.json`)

| Parameter | Allowed | Default | Paper-safe | fixed | low | medium |
|---|---|---|---|---|---|---|
| F12 `sti_sf.Basic`   | fixed, medium | **fixed** | medium | 1.0 | — | lognormal(1, σ=0.20) |
| F13 `sti_sf.Semi`    | fixed, medium | **fixed** | medium | 1.0 | — | lognormal(1, σ=0.25) |
| F14 `sti_sf.Highly`  | fixed, medium | **fixed** | medium | 1.0 | — | lognormal(1, σ=0.30) |
| F15 `sti_sf.sensing`       | fixed, low, medium | **low** | medium | 1.0 | lognormal(1, σ=0.25) | lognormal(1, σ=0.35) |
| F16 `sti_sf.computing`     | fixed, low, medium | **low** | medium | 1.0 | lognormal(1, σ=0.18) | lognormal(1, σ=0.25) |
| F17 `sti_sf.communication` | fixed, low, medium | **low** | medium | 1.0 | lognormal(1, σ=0.25) | lognormal(1, σ=0.35) |

### L2 Dirichlet mixes (`l2_dirichlet_mixes.json`)

| Parameter | Allowed | Default | Paper-safe | fixed | low | medium |
|---|---|---|---|---|---|---|
| F18 `cav_levels` | fixed, low, medium | **low** | medium | [0.5, 0.333, 0.167] | dir([15, 9.99, 5.01]) | dir([5, 3.33, 1.67]) |
| F19 `sti_levels` | fixed, low, medium | **low** | medium | [0.5, 0.333, 0.167] | dir([15, 9.99, 5.01]) | dir([5, 3.33, 1.67]) |

### L2 other load (`l2_other_load.json`)

| Parameter | Allowed | Default | Paper-safe | fixed | low | medium |
|---|---|---|---|---|---|---|
| F20 `icecav_power_factor` | fixed, low, medium | **low** | medium | 1.6 | tri(1.45, 1.6, 1.8) | tri(1.3, 1.6, 2.0) |
| F21 `cohort_decay_factor` | fixed, medium | **fixed** | medium | 0.7 | — | tri(0.5, 0.7, 0.9) |
| F22 `retire_year` | fixed, low, medium | **low** | medium | 12 | tri(10, 12, 15) int | tri(8, 12, 18) int |

## 3. L3 — trajectory parameters

### L3 2075 targets (`l3_2075_targets.json`)

| Parameter | Allowed | Default | Paper-safe | fixed | low | medium | high |
|---|---|---|---|---|---|---|---|
| F23 `growth_rates.cav` | fixed, low, medium, high | **low** | medium | 0.45 (CA/OH) | tri(0.35, 0.45, 0.55) | tri(0.25, 0.45, 0.70) | tri(0.15, 0.45, 0.85) |
| F24 `growth_rates.sti` | fixed, low, medium, high | **low** | medium | 0.50 | tri(0.40, 0.50, 0.60) | tri(0.25, 0.50, 0.75) | tri(0.15, 0.50, 0.90) |

### L3 growth exponents (`l3_growth_exponents.json`)

| Parameter | Allowed | Default | Paper-safe | fixed | low | medium | high |
|---|---|---|---|---|---|---|---|
| F25 `growth_rates.ev` | fixed, low, medium, high | **low** | medium | 0.07 | N(0.07, σ=0.0075, [0.04, 0.10]) | N(0.07, σ=0.015, [0.02, 0.15]) | N(0.07, σ=0.0225, [0.02, 0.20]) |
| F26 `growth_rates.clean_energy` | fixed, low, medium, high | **low** | medium | 0.05 | N(0.05, σ=0.006, [0.03, 0.07]) | N(0.05, σ=0.012, [0.01, 0.10]) | N(0.05, σ=0.018, [0.005, 0.12]) |
| F27 `growth_rates.efficiency_doubling` | fixed, low, medium, high | **low** | medium | 2.8 | tri(2.2, 2.8, 3.6) | tri(1.5, 2.8, 5.0) | tri(1.0, 2.8, 7.0) |
| F28 `growth_rates.total_car_increase` | fixed, low, medium | **low** | medium | 0.002 | N(0.002, σ=0.0005, [-0.001, 0.007]) | N(0.002, σ=0.001, [-0.005, 0.010]) | — |

## 4. Quick-access bundles

The panel offers three one-click bundles. Each applies per-parameter levels according to:

- **Decision-meaningful default** = each parameter's `default_level` column.
- **Paper-safe reproduction** = each parameter's `paper_safe_level` column (usually MEDIUM; FIXED for F06–F08, F12–F14, F21 would make paper-safe differ from current paper — not intended; paper-safe applies MEDIUM to those too).
- **Exploratory long-horizon** = `fixed` on L1 initial state (F01, F02), `low` on emission factors (F03–F05), `low` on L2 scale-factor per-subsystem and Dirichlets (F09–F11, F15–F17, F18, F19, F20, F22), FIXED on F21 and the per-level axes (F06–F08, F12–F14), and **HIGH on F23, F24, F25, F26, F27**; F28 LOW.

## 5. Scientifically-meaningful-only level assignment

The table deliberately avoids forcing every parameter to have all four levels. Rationale summary:

- Duplicate / irrelevant-after-2036 parameters (F06–F08, F12–F14, F21) have only `{fixed, medium}` — LOW and HIGH are undefined because narrowing them has no decision meaning and widening them is scientifically wrong.
- Evidence-anchored parameters (L1 emission factors, L2 per-subsystem, Dirichlet mixes, icecav, retire_year) have `{fixed, low, medium}` — HIGH is undefined because widening is unsupported.
- Trajectory-policy parameters (F23, F24, F25, F26, F27) have all four levels because HIGH represents exploratory long-horizon what-if scenarios.
- F28 has `{fixed, low, medium}` — demographically bounded; HIGH not justified.

## 6. Region handling

Region-specific means and Beta κ values are substituted from `scenarios/{region}/scenario.json` at load time using the `__REGION_MEAN__`, `__REGION_KAPPA__`, and `__REGION_KAPPA_X2__` sentinels. For US Average, the scenario file's centres for F23, F24, F27, F28 differ from CA/OH; the FIXED level always reads the scenario file directly, and the low/medium/high specs above apply to CA/OH. The panel banner flags the US Average case when selected.
