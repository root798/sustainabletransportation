# QUICK_BUNDLE_MAPPING.md

**Date:** 2026-04-15
**Implementation:** `v4_streamlit_app/core.py::parameter_default_choices`, `parameter_paper_safe_choices`, `parameter_exploratory_choices`.

The Scenario Explorer exposes exactly three one-click bundles. Bundles are convenience shortcuts — they populate the per-parameter radios; the radios remain the scientific control.

---

## 1. Recommended default (decision-meaningful)

One-click action: sets every parameter to its `default_level`.

| Parameter | Level |
|---|---|
| F01 initial f_clean | `fixed` |
| F02 initial ev_share | `fixed` |
| F03 e_clean | `low` |
| F04 e_fossil | `low` |
| F05 e_gasoline | `low` |
| F06–F08 ECAV per-level | `fixed` (only option) |
| F09 ECAV sensing | `low` |
| F10 ECAV computing | `low` |
| F11 ECAV communication | `low` |
| F12–F14 STI per-level | `fixed` (only option) |
| F15 STI sensing | `low` |
| F16 STI computing | `low` |
| F17 STI communication | `low` |
| F18 cav_levels | `low` |
| F19 sti_levels | `low` |
| F20 icecav_power_factor | `low` |
| F21 cohort_decay_factor | `fixed` (only option) |
| F22 retire_year | `low` |
| F23 CAV 2075 target | `low` |
| F24 STI 2075 target | `low` |
| F25 ev growth | `low` |
| F26 clean_energy growth | `low` |
| F27 efficiency_doubling | `low` |
| F28 total_car_increase | `low` |
| F29 | hidden |
| SHK01–SHK05 | shock panel only |

Paper-safe: **yes** (no HIGH levels active).
Expected bands (regenerated under the fixed backend):

- California 2030 W/M = 0.74; 2050 = 0.77; interpretation boundary 2065.
- Ohio 2030 W/M = 0.76; 2050 = 0.75; interpretation boundary does not occur within the horizon.

## 2. Paper-safe baseline

One-click action: sets every parameter to its `paper_safe_level`. Reproduces the committed paper-safe MC ensemble (under the fixed backend).

| Parameter | Level |
|---|---|
| F01, F02 | `low` |
| F03, F04 | `medium` |
| F05 | `low` |
| F06–F08 | `fixed` |
| F09, F10, F11 | `medium` |
| F12–F14 | `fixed` |
| F15, F16, F17 | `medium` |
| F18, F19 | `medium` |
| F20 | `low` |
| F21 | `fixed` |
| F22 | `medium` |
| F23, F24, F25, F26, F27 | `medium` |
| F28 | `low` |

Paper-safe: **yes**.
Expected bands:

- California 2030 W/M = 1.47; interpretation boundary 2031.
- Ohio 2030 W/M = 1.76; interpretation boundary 2027.

## 3. Exploratory long-horizon

One-click action: sets F23, F24, F25, F26, F27 to HIGH; leaves every other parameter at its default-bundle value (fixed or low).

| Parameter | Level |
|---|---|
| F01, F02 | `fixed` |
| F03–F05 | `low` |
| F06–F08 | `fixed` |
| F09, F10, F11 | `low` |
| F12–F14 | `fixed` |
| F15, F16, F17 | `low` |
| F18, F19, F20 | `low` (F20) / `low` (F18, F19) |
| F21 | `fixed` |
| F22 | `low` |
| **F23, F24, F25, F26, F27** | **`high`** |
| F28 | `low` |

Paper-safe: **no** (explicitly exploratory). The UI badges any HIGH radio with a non-paper-safe warning.

Expected bands (approximate, extrapolated from the parameter-level contribution experiment):

- California 2030 W/M ≈ 1.0–1.2.
- California 2050 W/M ≈ 2.0+ (driven by HIGH on F25, F26, F27).
- Interpretation boundary likely pushed in by L3 HIGHs but still later than paper-safe because L1 and L2 remain at fixed / low.

## 4. Mapping rationale

- **Default = decision-meaningful.** Fixes the dossier-duplicated parameters (F06–F08, F12–F14) and the absorbed-downstream parameters (F01, F02). Everything else at LOW — narrow, evidence-anchored. No HIGH.
- **Paper-safe = reproduce old paper numbers.** MEDIUM where a MEDIUM level exists; otherwise LOW (because some parameters never had MEDIUM in the final design).
- **Exploratory = trajectory-policy what-if.** HIGH on the five trajectory knobs (F23–F27) only. L1 and L2 kept narrow so the HIGH band is attributable to the trajectory knobs the reader intentionally widened.

## 5. Not supported as quick bundles

The user's scientific control is the radios — bundles are shortcuts. Intentionally *not* provided:

- A "HIGH on everything" bundle. L1 and L2 HIGH levels do not exist in the final classification; there is nothing to set.
- A "LOW on everything including duplicates" bundle. Duplicates (F06–F08, F12–F14) do not accept LOW.
- A bundle that sets F29 or SHK01–SHK05 to anything. Those classes are outside ordinary MC.
