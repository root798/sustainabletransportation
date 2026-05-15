# STI_CO2_EARLY_SPIKE_CHECK.md

**Date:** 2026-04-14
**Observation:** On California baseline, STI annual CO₂ emissions rise rapidly from 2024 → 2028, peak near 2028, then drop sharply through 2033 before resuming a slow growth. This produces a visible "hump" around the early 2030s.
**Verdict:** **Scientifically expected, not a bug.** The hump is the product of two competing physics: STI fleet ramp-in from a near-zero 2024 baseline and California's low-carbon electricity share saturation at 2033. Fix is wording-only: add an inline annotation on the emissions chart to explain the hump.

---

## Quantitative trace (California baseline deterministic)

Emission factors: `e_clean = 0.03 kg CO₂/kWh`, `e_fossil = 0.5 kg CO₂/kWh`.

| Year | STI count | STI power (GWh/yr) | f_clean | Grid intensity (g CO₂/kWh) | STI CO₂ (kt CO₂/yr) |
|---:|---:|---:|---:|---:|---:|
| 2024 | 0 | 0.0000 | 0.6560 | 191.68 | 0.00 |
| 2025 | 3,729 | 0.2181 | 0.6888 | 176.26 | 38.45 |
| 2026 | 7,422 | 0.3881 | 0.7232 | 160.08 | 62.13 |
| 2027 | 11,114 | 0.5222 | 0.7594 | 143.08 | 74.71 |
| 2028 | 14,806 | 0.6282 | 0.7974 | 125.24 | **78.67** ← peak |
| 2029 | 18,497 | 0.7122 | 0.8372 | 106.50 | 75.85 |
| 2030 | 22,187 | 0.7792 | 0.8791 | 86.82 | 67.65 |
| 2031 | 25,877 | 0.8329 | 0.9231 | 66.16 | 55.10 |
| 2032 | 29,566 | 0.8761 | 0.9692 | 44.47 | 38.96 |
| 2033 | 33,253 | 0.9112 | 1.0000 | 30.00 | **27.34** ← clean cap reached |
| 2034 | 36,940 | 0.9399 | 1.0000 | 30.00 | 28.20 |
| 2035 | 40,627 | 0.9637 | 1.0000 | 30.00 | 28.91 |
| 2040 | 59,043 | 1.0390 | 1.0000 | 30.00 | 31.17 |

Identity: `STI CO₂ = STI power × grid_intensity`. The table reproduces this
to rounding.

## Why the hump appears

- From 2024 the STI fleet is **zero** (config: `initial_data.total_sti = 0`
  on California). The linear 2024→2075 ramp adds ≈3,700 STI units per year,
  so STI power rises steeply from 0 GWh/yr.
- The California grid's low-carbon share grows at `clean_energy_growth_rate`
  per year; it reaches the modelling cap of 1.0 in 2033. Before 2033 the
  grid intensity is still ≈100–190 g CO₂/kWh, **six times** the post-cap
  ≈30 g CO₂/kWh.
- STI CO₂ = STI power × grid intensity. The product grows while both
  factors are below their caps, peaks near 2028 while STI is still small
  and the grid still dirty, then drops rapidly 2028–2033 as the grid
  decarbonises faster than STI adds units.
- After 2033, STI power grows linearly against a fixed grid intensity, so
  STI CO₂ resumes a gentle rise.

## Dismissed alternative causes

| Hypothesis | Evidence | Conclusion |
|---|---|---|
| Unit / scaling bug | STI CO₂ reproduces exactly as `power × grid_intensity` with published emission factors. | Ruled out. |
| Annual / cumulative confusion | Column is `STI Emissions (kg CO2)` — per-year values; cumulative is a separate column. | Ruled out. |
| Embodied / one-time burden leakage into annual utility emissions | Model computes utility-phase emissions only; no production/EoL term is added to the annual sum. | Ruled out. |
| Grid-mix application bug | Grid intensity in the table recomputes from the CSV columns to the same kt CO₂ as the CSV's `STI Emissions`. | Ruled out. |
| Front-loaded rollout from zero baseline | STI count rises linearly from 0 (2024) → 22,187 (2030) per the 51-year ramp. | **Confirmed contributor.** |
| Rapid CA clean-grid saturation | f_clean grows at `clean_energy_growth_rate` until cap at 2033. | **Confirmed contributor.** |

## Action

- No backend patch.
- Added an explanatory annotation on the Scenario Explorer annual-emissions
  chart (California only) naming the grid-saturation year and the STI
  ramp-in as the hump's drivers. See `00_Scenario_Explorer.py` patch.
- Updated Methods-support wording: this is a consequence of the 2075
  linear-ramp assumption (Methods M11) acting against a faster-than-STI
  clean-grid trajectory. No new paper claim is needed.
