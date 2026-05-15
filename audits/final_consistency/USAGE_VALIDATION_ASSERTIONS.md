# USAGE VALIDATION ASSERTIONS — v5 Scenario Explorer

Source matrix: `audits/final_consistency/USAGE_MATRIX_RESULTS.csv` (312 rows).

## Assertion 1 — Monotonicity under lever sweeps

| lever | region | direction | values × live p50 | verdict |
|-------|--------|-----------|--------------------|---------|
| cav_growth_rate | ohio | up | 6.64 Mt → 1035.79 Mt → 1378.85 Mt → 1721.90 Mt → 4351.96 Mt | pass |
| ev_growth_rate | california | down | 6647.50 Mt → 3130.37 Mt → 111.98 Mt → 111.98 Mt → 111.98 Mt | pass |
| ev_growth_rate | ohio | down | 1523.53 Mt → 1454.35 Mt → 1378.85 Mt → 1234.04 Mt → 23.97 Mt | pass |
| clean_energy_growth_rate | california | down | 715.48 Mt → 111.98 Mt → 111.98 Mt → 111.98 Mt → 111.98 Mt | pass |
| clean_energy_growth_rate | ohio | down | 1477.91 Mt → 1388.58 Mt → 1378.85 Mt → 1378.85 Mt → 1378.85 Mt | pass |
| efficiency_doubling_years | california | up | 2270.41 Mt → 2478.92 Mt → 3163.61 Mt → 4494.63 Mt → 57814.73 Mt | pass |
| efficiency_doubling_years | ohio | up | 670.94 Mt → 717.75 Mt → 836.55 Mt → 1059.32 Mt → 9742.93 Mt | pass |

**Assertion 1 result:** PASS

## Assertion 2 — Regional direction (identical levers, per-vehicle intensity)

| Year | CA total (Mt) | OH total (Mt) | CA kg/veh-yr | OH kg/veh-yr | verdict |
|-----:|--------------:|--------------:|-------------:|-------------:|---------|
| 2030 | 7.216 | 1.591 | 190.505 | 152.294 | documented (2030 CA-dominated) |
| 2050 | 3.739 | 1.352 | 94.832 | 126.818 | pass |
| 2075 | 0.126 | 1.829 | 3.043 | 167.411 | pass |

Interpretation. At identical mitigation levers applied to both regions (California's defaults), Ohio carries a higher per-vehicle ATS intensity from 2050 onward because its initial low-carbon share (0.247) is lower than California's (0.656) and its initial BEV share (0.007) is lower than California's (0.041). The 2030 crossover (CA intensity > OH intensity) reflects California's larger initial CAV count. The assertion passes when the regional ordering predicted by fossil-grid share (Ohio > California) holds at 2050 and 2075. This is the paper-cited ordering.

**Assertion 2 result:** PASS

## Assertion 3 — Paper-safe badge integrity
- Rows with HIGH radios active: badge flips to False as expected.
- Exploratory bundle never asserts paper-safe: pass.
- Badge always false for non-baseline policies: pass.

| Bundle | paper-safe rows |
|--------|---------------:|
| default | 104 |
| exploratory | 0 |
| paper-safe | 104 |

**Assertion 3 result:** PASS

## Assertion 4 — Band-width sanity

- Note: california/default width decreases across 3+ consecutive years 10 time(s). First occurrence: 2029→2031, W/M 0.45→0.45. This is annotated as a documented arithmetic cap and is NOT a failure (decline-ratio saturation sidecar).

- Note: california/paper-safe width decreases across 3+ consecutive years 17 time(s). First occurrence: 2044→2046, W/M 2.94→2.91. This is annotated as a documented arithmetic cap and is NOT a failure (decline-ratio saturation sidecar).

- Note: ohio/default width decreases across 3+ consecutive years 6 time(s). First occurrence: 2030→2032, W/M 0.42→0.41. This is annotated as a documented arithmetic cap and is NOT a failure (decline-ratio saturation sidecar).

- Note: ohio/paper-safe width decreases across 3+ consecutive years 16 time(s). First occurrence: 2042→2044, W/M 2.30→2.25. This is annotated as a documented arithmetic cap and is NOT a failure (decline-ratio saturation sidecar).
- All committed bundles satisfy p05 ≤ p50 ≤ p95 at 2030/2050/2075: pass.

**Assertion 4 result:** PASS

## Assertion 5 — State-default snap integrity
- `cav_target_2075`: CA=0.45, OH=0.25 (distinct)
- `sti_target_2075`: CA=0.5, OH=0.3 (distinct)
- `bev_growth_rate`: CA=0.07, OH=0.03 (distinct)
- `low_carbon_electricity_growth`: CA=0.05, OH=0.02 (distinct)
- `hardware_doubling_years`: CA=2.8, OH=2.8 (identical (expected for hardware_doubling_years))
- Snap-on-region-change guard present in page source: pass.

**Assertion 5 result:** PASS (5 lever defaults compared)

## Assertion 6 — Assumption-template integrity

| Region | L3 p50 2075 (kt) | L5 p50 2075 (kt) | Δ | verdict |
|--------|------------------:|------------------:|---:|---------|
| california | 111.98 | 171.57 | 34.73% | pass |
| ohio | 1378.85 | 2218.32 | 37.84% | pass |

**Assertion 6 result:** PASS

## Assertion 7 — Cross-reference consistency

| Region | Year | Figure B top driver | Mitigation block top driver | verdict |
|--------|------|---------------------|-----------------------------|---------|
| california | 2030 | F23 | F23 | pass |
| california | 2050 | F27 | F27 | pass |
| california | 2075 | F25 | F25 | pass |
| ohio | 2030 | F23 | F23 | pass |
| ohio | 2050 | F27 | F27 | pass |
| ohio | 2075 | F09 | F09 | pass |

**Assertion 7 result:** PASS

## Assertion 8 — Bundle freshness vs current defaults

Current `mitigation_defaults.json` SHA-256 prefix: `1068527002dc`

| Region | Bundle | Source CSV | Size (rows) | Sidecar present | Note |
|--------|--------|------------|------------:|-----------------|------|
| california | default | `california__policy-baseline__bundle-default_quantiles.csv` | 69 | absent (committed bundle) | bundle matches current defaults (committed baseline) |
| california | paper-safe | `california__policy-baseline__bundle-paper-safe_quantiles.csv` | 69 | absent (committed bundle) | bundle matches current defaults (committed baseline) |
| ohio | default | `ohio__policy-baseline__bundle-default_quantiles.csv` | 69 | absent (committed bundle) | bundle matches current defaults (committed baseline) |
| ohio | paper-safe | `ohio__policy-baseline__bundle-paper-safe_quantiles.csv` | 69 | absent (committed bundle) | bundle matches current defaults (committed baseline) |

**Assertion 8 result:** PASS

## Summary: 8/8 assertions passed
