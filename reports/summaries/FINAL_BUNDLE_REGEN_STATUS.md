# FINAL_BUNDLE_REGEN_STATUS.md

**Date:** 2026-04-16
**MC configuration:** 200 runs, seed 42, horizon 68 years (through 2092).
**Prior design:** final parameter-level registry with F27 lognormal, F04 region-specific, F25/F26/F28 truncated_normal (normal+clamp).
**Backend:** scale-factor bypass fix applied (footprint_model.py:411).

---

## Regenerated outputs

| File | Region | Bundle | MC runs |
|---|---|---|---:|
| `results/california__policy-baseline__bundle-default_quantiles.csv` | CA | default | 200 |
| `results/california__policy-baseline__bundle-default_mc_runs.csv` | CA | default | 200 |
| `results/california__policy-baseline__bundle-default_metrics.csv` | CA | default | 200 |
| `results/california__policy-baseline__bundle-paper-safe_quantiles.csv` | CA | paper-safe | 200 |
| `results/california__policy-baseline__bundle-paper-safe_mc_runs.csv` | CA | paper-safe | 200 |
| `results/california__policy-baseline__bundle-paper-safe_metrics.csv` | CA | paper-safe | 200 |
| `results/ohio__policy-baseline__bundle-default_quantiles.csv` | OH | default | 200 |
| `results/ohio__policy-baseline__bundle-default_mc_runs.csv` | OH | default | 200 |
| `results/ohio__policy-baseline__bundle-default_metrics.csv` | OH | default | 200 |
| `results/ohio__policy-baseline__bundle-paper-safe_quantiles.csv` | OH | paper-safe | 200 |
| `results/ohio__policy-baseline__bundle-paper-safe_mc_runs.csv` | OH | paper-safe | 200 |
| `results/ohio__policy-baseline__bundle-paper-safe_metrics.csv` | OH | paper-safe | 200 |

## Authoritative band numbers

### ATS Emissions (kg CO2) — width / median

| Region | Bundle | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---|---|---:|---:|---:|---:|
| California | **default** | **0.83** | **0.88** | 15.95 | **2064** |
| California | paper-safe | 1.64 | 2.41 | 19.15 | 2028 |
| Ohio | **default** | **0.82** | **0.80** | 0.86 | **never** |
| Ohio | paper-safe | 1.59 | 1.92 | 1.61 | 2029 |

### Peak year and turning year (from p50 trajectory)

| Region | Bundle | Peak year | Turning year |
|---|---|---:|---:|
| California | default | 2036 | 2047 |
| California | paper-safe | 2036 | 2049 |
| Ohio | default | 2082 | — |
| Ohio | paper-safe | 2076 | — |

## Consistency checks

| Check | Status |
|---|---|
| Default W/M < 1.0 at 2030 and 2050 for both regions | **PASS** (CA 0.83/0.88; OH 0.82/0.80) |
| Paper-safe W/M > 1.5 at 2030 for both regions | **PASS** (CA 1.64; OH 1.59) |
| Default IB year later than paper-safe for CA | **PASS** (2064 vs 2028) |
| Ohio default never crosses IB | **PASS** |
| Peak year consistent between bundles for CA | **PASS** (both 2036) |
| CA turning year exists; OH turning year does not | **PASS** |
| Page label "Recommended default" matches bundle-default file | **PASS** |
| Page label "Paper-safe reproduction" matches bundle-paper-safe file | **PASS** |

## What changed from previous regeneration

Previous run (120 MC, before F27 lognormal and F04 region-specific):
- CA default: W/M 2030 = 0.74 → now 0.83
- OH default: W/M 2030 = 0.76 → now 0.82
- CA paper-safe: W/M 2030 = 1.47 → now 1.64
- OH paper-safe: W/M 2030 = 1.76 → now 1.59

The modest shifts are due to (i) F27 lognormal having a different tail shape than the old triangular, (ii) F04 Ohio prior now heavier (mode 0.62 vs 0.50), and (iii) 200 vs 120 runs reducing MC noise. The default bundle remains well under W/M = 1.0 at both 2030 and 2050 for both regions.
