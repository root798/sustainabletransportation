# PARAMETER_LEVEL_PRESET_LOGIC_FINAL.md

**Date:** 2026-04-15
**Authoritative JSON files:** `configs/ui_parameter_presets/*.json`.
**Supersedes:** `PARAMETER_LEVEL_PRESET_TABLE.md` (earlier table). This document is the final specification.

---

## 1. Allowed level sets are not uniform

The six allowed-level sets defined in `PARAMETER_CLASSIFICATION_FINAL.md` map onto the per-parameter radios:

| Parameters | Allowed radios |
|---|---|
| F06, F07, F08, F12, F13, F14, F21 | `[fixed]` (one pill; read-only) |
| F01, F02, F05, F20, F28 | `[fixed, low]` |
| F03, F04, F09, F10, F11, F15, F16, F17, F18, F19, F22 | `[fixed, low, medium]` |
| F23, F24, F25, F26, F27 | `[fixed, low, medium, high]` |
| F29 | hidden pill only |
| SHK01–SHK05 | not on Scenario Explorer |

## 2. Numerical level specifications

Distribution specifications per level. California values are the default; Ohio overrides appear where justified (see §4).

### L1 initial state (`l1_initial_state.json`)

| Parameter | fixed | low |
|---|---|---|
| F01 `initial_data.f_clean` | region mean (CA 0.656, OH 0.247) | Beta(region mean, κ × 2) |
| F02 `initial_data.ev_share` | region mean (CA 0.041, OH 0.00668) | Beta(region mean, κ × 2) |

MEDIUM is deliberately not offered on F01, F02.

### L1 emission factors (`l1_emission_factors.json`)

| Parameter | fixed | low | medium |
|---|---|---|---|
| F03 e_clean | 0.03 | tri(0.02, 0.03, 0.05) | tri(0.01, 0.03, 0.08) |
| F04 e_fossil | 0.50 | tri(0.40, 0.50, 0.60) | tri(0.35, 0.50, 0.65) |
| F05 e_gasoline | 1.65 | tri(1.55, 1.65, 1.75) | — |

### L2 ECAV scale factors (`l2_ecav_scale_factors.json`)

| Parameter | fixed | low | medium |
|---|---|---|---|
| F06 `ecav_sf.L3` | 1.0 | — | — |
| F07 `ecav_sf.L4` | 1.0 | — | — |
| F08 `ecav_sf.L5` | 1.0 | — | — |
| F09 `ecav_sf.sensing` | 1.0 | lognormal(σ=0.20) | lognormal(σ=0.30) |
| F10 `ecav_sf.computing` | 1.0 | lognormal(σ=0.15) | lognormal(σ=0.20) |
| F11 `ecav_sf.communication` | 1.0 | lognormal(σ=0.25) | lognormal(σ=0.35) |

### L2 STI scale factors (`l2_sti_scale_factors.json`)

| Parameter | fixed | low | medium |
|---|---|---|---|
| F12 `sti_sf.Basic` | 1.0 | — | — |
| F13 `sti_sf.Semi` | 1.0 | — | — |
| F14 `sti_sf.Highly` | 1.0 | — | — |
| F15 `sti_sf.sensing` | 1.0 | lognormal(σ=0.25) | lognormal(σ=0.35) |
| F16 `sti_sf.computing` | 1.0 | lognormal(σ=0.18) | lognormal(σ=0.25) |
| F17 `sti_sf.communication` | 1.0 | lognormal(σ=0.25) | lognormal(σ=0.35) |

### L2 Dirichlet mixes (`l2_dirichlet_mixes.json`)

| Parameter | fixed | low | medium |
|---|---|---|---|
| F18 `cav_levels` | [0.5, 0.333, 0.167] | dir(α = [15.0, 9.99, 5.01]) | dir(α = [5.0, 3.33, 1.67]) |
| F19 `sti_levels` | [0.5, 0.333, 0.167] | dir(α = [15.0, 9.99, 5.01]) | dir(α = [5.0, 3.33, 1.67]) |

### L2 other load (`l2_other_load.json`)

| Parameter | fixed | low | medium |
|---|---|---|---|
| F20 `icecav_power_factor` | 1.6 | tri(1.45, 1.6, 1.8) | — |
| F21 `cohort_decay_factor` | 0.7 | — | — |
| F22 `retire_year` | 12 | tri(10, 12, 15) int | tri(8, 12, 18) int |

### L3 2075 targets (`l3_2075_targets.json`)

| Parameter | fixed | low | medium | high |
|---|---|---|---|---|
| F23 CA | 0.45 | tri(0.35, 0.45, 0.55) | tri(0.25, 0.45, 0.70) | tri(0.15, 0.45, 0.85) |
| F23 OH | 0.30 | tri(0.20, 0.30, 0.40) | tri(0.10, 0.30, 0.55) | tri(0.05, 0.30, 0.70) |
| F24 CA | 0.50 | tri(0.40, 0.50, 0.60) | tri(0.25, 0.50, 0.75) | tri(0.15, 0.50, 0.90) |
| F24 OH | 0.30 | tri(0.20, 0.30, 0.45) | tri(0.10, 0.30, 0.55) | tri(0.05, 0.30, 0.75) |

### L3 growth exponents (`l3_growth_exponents.json`)

| Parameter | fixed | low | medium | high |
|---|---|---|---|---|
| F25 CA | 0.07 | N(0.07, 0.0075, [0.04, 0.10]) | N(0.07, 0.015, [0.02, 0.15]) | N(0.07, 0.0225, [0.02, 0.20]) |
| F25 OH | 0.055 | N(0.055, 0.010, [0.03, 0.085]) | N(0.055, 0.020, [0.015, 0.12]) | N(0.055, 0.028, [0.01, 0.16]) |
| F26 CA | 0.05 | N(0.05, 0.006, [0.03, 0.07]) | N(0.05, 0.012, [0.01, 0.10]) | N(0.05, 0.018, [0.005, 0.12]) |
| F26 OH | 0.035 | N(0.035, 0.008, [0.02, 0.055]) | N(0.035, 0.015, [0.005, 0.08]) | N(0.035, 0.022, [0.002, 0.10]) |
| F27 (all) | 2.8 | tri(2.2, 2.8, 3.6) | tri(1.5, 2.8, 5.0) | tri(1.0, 2.8, 7.0) |
| F28 CA | 0.002 | N(0.002, 0.0005, [-0.001, 0.007]) | — | — |
| F28 OH | 0.001 | N(0.001, 0.0005, [-0.002, 0.004]) | — | — |

## 3. Scientific reasonableness of levels

Rationales per level class:

- **LOW** is never more than half the MEDIUM sigma (or equivalent triangular support). LOW is always evidence-anchored, not a speculative narrowing.
- **MEDIUM** reproduces the previous paper-safe ensemble where applicable.
- **HIGH** is only defined for trajectory-policy knobs (F23–F27) because those are the only parameters where an above-MEDIUM envelope is a real scenario-exploration request. Every HIGH is tagged `paper_safe: false` and the UI flags "exploratory" beside any radio on HIGH.

## 4. Ohio-specific overrides

Applied to F23, F24, F25, F26, F28 via `_regions.ohio` keys inside each level spec (see `OHIO_PARAMETER_PRIOR_JUSTIFICATION.md` for the underlying data). Ohio scenario file centres also updated so FIXED-level runs reflect Ohio modes. F27 (global technology) is not region-differentiated.

## 5. JSON structure (parameter-centric)

Every group file follows this schema:

```json
{
  "group_id": "...",
  "layer": "L1|L2|L3",
  "group_label": "...",
  "help": "...",
  "parameters": [
    {
      "param_id": "Fxx",
      "config_path": "initial_data.f_clean",
      "label": "...",
      "physical_meaning": "...",
      "affects": ["width"],
      "allowed_levels": ["fixed", "low"],
      "default_level": "fixed",
      "paper_safe_level": "low",
      "levels": {
        "fixed": {"fixed_to": "region_mean"},
        "low":   {"dist": "beta", "mean": "__REGION_MEAN__", "kappa": "__REGION_KAPPA_X2__"}
      },
      "why_default_fixed": "...",
      "why_medium_rejected": "...",
      "duplicates": "..."
    }
  ]
}
```

Sentinels:
- `__REGION_MEAN__` — substituted from `scenarios/{region}/scenario.json:data_uncertainty.initial_data.{field}.mean`.
- `__REGION_KAPPA__` / `__REGION_KAPPA_X2__` — Beta concentration, same source.
- `"fixed_to": "region_mean"` — the FIXED level reads the central value from the scenario file directly.
- `_regions.ohio` (or `california`) — level-spec overrides applied when that region is selected.

Invariants enforced by `validate_parameter_registry()`:

1. `default_level` and `paper_safe_level` must be in `allowed_levels`.
2. For every non-`fixed` level in `allowed_levels`, a spec must exist under `levels.<level>`.
3. `config_path` must be unique across all group files.
4. No parameter may carry HIGH without Class-G membership (trajectory knob).

## 6. Why we did not adopt a single global low/medium/high

See `PARAMETER_LEVEL_CONTROL_JUSTIFICATION.md` (rebuttal support). In short: a single global selector forces the reader to accept a decision like "narrow F06–F08 and also narrow F03 in one click" — those two decisions are scientifically unrelated and should be independent.
