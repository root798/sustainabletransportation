# FINAL_PARAMETER_ALLOWED_LEVELS.md

**Date:** 2026-04-15
**Authoritative JSON source:** `configs/ui_parameter_presets/*.json`
**Supersedes:** `PARAMETER_LEVEL_PRESET_LOGIC_FINAL.md` (any conflict resolved in favour of this document and the JSONs).

---

## 1. Allowed-level distribution

| Allowed set | Parameters | Count | Rationale |
|---|---|---:|---|
| `{fixed}` only | F06, F07, F08, F12, F13, F14, F21 | 7 | Structural duplicates (S2-01, S2-02) or vanishes post-2036 |
| `{fixed, low}` | F01, F02, F05, F20, F28 | 5 | Narrow evidence; MEDIUM was uninformative inflation |
| `{fixed, low, medium}` | F03, F04, F09, F10, F11, F15, F16, F17, F18, F19, F22 | 11 | Real methodological or technology spread |
| `{fixed, low, medium, high}` | F23, F24, F25, F26, F27 | 5 | Trajectory-policy knobs; HIGH is exploratory only |
| Hidden internal | F29 | 1 | No prior; disclosed but not tunable |
| Structural shock only | SHK01–SHK05 | 5 | Never in ordinary MC |

## 2. Default level per parameter

| Parameter | Default | Paper-safe | Allowed set |
|---|---|---|---|
| F01 initial f_clean | fixed | low | {fixed, low} |
| F02 initial ev_share | fixed | low | {fixed, low} |
| F03 e_clean | low | medium | {fixed, low, medium} |
| F04 e_fossil | low | medium | {fixed, low, medium} |
| F05 e_gasoline | low | low | {fixed, low} |
| F06 ecav_sf.L3 | fixed | fixed | {fixed} |
| F07 ecav_sf.L4 | fixed | fixed | {fixed} |
| F08 ecav_sf.L5 | fixed | fixed | {fixed} |
| F09 ecav_sf.sensing | low | medium | {fixed, low, medium} |
| F10 ecav_sf.computing | low | medium | {fixed, low, medium} |
| F11 ecav_sf.communication | low | medium | {fixed, low, medium} |
| F12 sti_sf.Basic | fixed | fixed | {fixed} |
| F13 sti_sf.Semi | fixed | fixed | {fixed} |
| F14 sti_sf.Highly | fixed | fixed | {fixed} |
| F15 sti_sf.sensing | low | medium | {fixed, low, medium} |
| F16 sti_sf.computing | low | medium | {fixed, low, medium} |
| F17 sti_sf.communication | low | medium | {fixed, low, medium} |
| F18 cav_levels | low | medium | {fixed, low, medium} |
| F19 sti_levels | low | medium | {fixed, low, medium} |
| F20 icecav_power_factor | low | low | {fixed, low} |
| F21 cohort_decay | fixed | fixed | {fixed} |
| F22 retire_year | low | medium | {fixed, low, medium} |
| F23 cav target 2075 | low | medium | {fixed, low, medium, high} |
| F24 sti target 2075 | low | medium | {fixed, low, medium, high} |
| F25 ev growth | low | medium | {fixed, low, medium, high} |
| F26 clean_energy growth | low | medium | {fixed, low, medium, high} |
| F27 efficiency doubling | low | medium | {fixed, low, medium, high} |
| F28 total_car_increase | low | low | {fixed, low} |

## 3. Why most parameters do NOT get full LMH

- **7 fixed-only:** offering non-fixed values would re-introduce the S2-01/S2-02 dual-axis duplication or sample a parameter whose effect cannot appear in any reported post-2036 metric.
- **5 fixed/low:** previous MEDIUM was simply LOW-with-doubled-tails; no evidence supported the wider tails. Offering MEDIUM or HIGH would overstate knowledge.
- **11 fixed/low/medium:** a real methodological or measurement spread exists between LOW and MEDIUM. HIGH beyond MEDIUM is rejected because no measurement or scenario evidence supports it for these parameters.
- **5 full LMH:** the five trajectory-policy knobs (2075 targets + growth exponents + efficiency doubling) are the only parameters where HIGH represents a genuine exploratory what-if view rather than unsupported inflation.

## 4. Ohio-specific overrides

F23, F24, F25, F26, F28 carry Ohio-specific centre and support values at every level via `_regions.ohio` keys in the JSON specs. See `OHIO_PARAMETER_PRIOR_JUSTIFICATION.md`.

## 5. Regenerated band evidence

Under the default bundle (9 fixed, 19 at LOW):
- California 2030 W/M = 0.74; interpretation boundary 2065.
- Ohio 2030 W/M = 0.76; interpretation boundary never within horizon.

Under the paper-safe bundle (7 fixed, 5 at LOW, 16 at MEDIUM):
- California 2030 W/M = 1.47; interpretation boundary 2031.
- Ohio 2030 W/M = 1.76; interpretation boundary 2027.
