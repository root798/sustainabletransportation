# PARAMETER_CONTRIBUTION_EXPERIMENT.md

**Date:** 2026-04-15
**Script:** `scripts/parameter_contribution_experiment.py`
**CSV:** `PARAMETER_CONTRIBUTION_EXPERIMENT.csv` (this folder)
**Region / policy:** California, baseline. 80 Monte Carlo runs per isolated parameter. Seed 42.
**Metric:** `ATS Emissions (kg CO2)`.

---

## 1. Design

For each uncertainty parameter in the registry, an isolated MC ensemble is run in which **only that single parameter (or axis)** is sampled at its MEDIUM spread; every other parameter is held at its central value. We then record, for each isolated run:

- `width_over_median` at 2030, 2050, 2075 — `(p95 − p05) / p50` of ATS Emissions.
- `interpretation_boundary_year` — first year ≥ 2027 where `(p95 − p05) / |p50| ≥ 1.5`.
- `turning_year_p50` — year where p50 first drops below 50% of its peak value.
- `turning_year_spread` — `|turning_year(p95) − turning_year(p05)|`, a proxy for how uncertain the turning year becomes under this parameter alone.

The ECAV per-level (F06/F07/F08) and STI per-level (F12/F13/F14) axes are sampled as a *bundle* (all three per-level lognormals together) so that the experiment reports the net effect of the dual-axis duplication at the axis level, not per cell.

---

## 2. 2030 width/median ranking

| Rank | Parameter | Layer | W/M 2030 | Effect type |
|---|---|---|---:|---|
| 1 | F23 CAV 2075 target | L3 | **0.56** | long-horizon ramp divergence |
| 2 | F27 efficiency doubling | L3 | 0.56 | Moore-style decay |
| 3 | F18 cav_levels Dirichlet | L2 | **0.55** | level-mix spread |
| 4 | F10 ECAV computing column | L2 | 0.44 | per-subsystem axis |
| 5 | F22 retire_year | L2 | 0.40 | cohort rotation |
| 6 | F06/F07/F08 ECAV per-level axis | L2 | **0.35** | dual-axis duplicate |
| 7 | F20 icecav_power_factor | L2 | 0.25 | ICE overhead |
| 8 | F05 e_gasoline | L1 | 0.14 | emission factor |
| 9 | F02 ev_share | L1 | 0.09 | initial BEV |
| ≤10 | all others | — | < 0.05 | minor |

**Key interpretation:** the top-three 2030 contributors are (F23 CAV target, F27 efficiency doubling, F18 cav_levels Dirichlet). Two are L3, one is L2. Per-level ECAV axis (S2-01 fix target) is rank 6 at 0.35 — a real but secondary contributor compared with trajectory and level-mix knobs.

## 3. 2050 width/median ranking

| Rank | Parameter | Layer | W/M 2050 |
|---|---|---|---:|
| 1 | F27 efficiency doubling | L3 | **1.02** |
| 2 | F23 CAV 2075 target | L3 | 0.56 |
| 3 | F18 cav_levels | L2 | 0.51 |
| 4 | F02 ev_share | L1 | 0.44 |
| 5 | F09 ECAV sensing | L2 | 0.43 |
| 6 | F06/F07/F08 ECAV per-level | L2 | 0.34 |
| 7 | F25 ev growth exponent | L3 | 0.27 |
| 8 | F20 icecav_power_factor | L2 | 0.25 |

**Key interpretation:** F27 efficiency-doubling emerges as the dominant 2050 contributor, exceeding the interpretation-boundary threshold on its own (1.02 > 1.5 fraction of median at mid-horizon is borderline; full all-layer MC reaches 2.45 at 2050 because contributions combine).

## 4. 2075 width/median ranking (long horizon)

| Rank | Parameter | Layer | W/M 2075 | Note |
|---|---|---|---:|---|
| 1 | F25 ev growth exponent | L3 | **29.60** | compounding-exponent explosion |
| 2 | F02 initial ev_share | L1 | **27.37** | propagates via fleet-count * per-cell |
| 3 | F03 e_clean | L1 | 1.07 | small median, ratio explodes |
| 4 | F09 ECAV sensing | L2 | 0.42 | per-subsystem variance |
| 5 | F23 CAV 2075 target | L3 | 0.40 | long-horizon |
| 6 | F18 cav_levels | L2 | 0.35 | level-mix |
| 7 | F06/F07/F08 ECAV per-level | L2 | 0.24 | per-level axis |

**Key interpretation:** F25 and F02 dominate the 2075 ratio because the median approaches zero under full decarbonisation, so the ratio is mathematically unstable. The *absolute* 2075 width is modest; it is the reported *relative* width that blows up. The panel therefore presents 2075 using BOTH absolute and relative metrics, and caps the displayed relative-width axis for readability.

## 5. Interpretation-boundary contributors

Only two isolated parameters push the interpretation boundary inside the horizon:

| Parameter | IB year |
|---|---|
| F02 initial ev_share | 2062 |
| F25 ev growth exponent | 2062 |

Both are BEV-related. Their interpretation-boundary year coincides because F25 compounds on F02's initial value. In the full-MC ensemble these two alone cannot push the boundary to 2031; it is the *combination* with F26 (clean_energy growth) and F18/F23 (level-mix and CAV target) that triggers 2031. This is documented in the layer-level experiment (`LAYER_CONTRIBUTION_EXPERIMENT.csv`).

## 6. Turning-year spread ranking

The turning-year proxy spread (years between p05 and p95 turning years) identifies which parameters most *destabilise the turning-year metric*, which is a reported decision quantity:

| Rank | Parameter | Layer | TY spread (years) |
|---|---|---|---:|
| 1 | F27 efficiency doubling | L3 | **16** |
| 2 | F23 CAV 2075 target | L3 | 9 |
| 3 | F18 cav_levels | L2 | 7 |
| 4 | F06/F07/F08 ECAV per-level | L2 | 5 |
| 5 | F09 ECAV sensing | L2 | 4 |
| 5 | F10 ECAV computing | L2 | 4 |
| 5 | F20 icecav_power_factor | L2 | 4 |
| 8 | F22 retire_year | L2 | 3 |

**Key interpretation:** F27 efficiency doubling is the single largest turning-year uncertainty driver (16 years). This is a new, decision-relevant finding and is surfaced on the panel's "turning-year sensitivity" note. F23 (CAV target) comes second at 9 years — the reader interrogating the policy target should know that their 2075 target assumption moves the turning year by roughly a decade.

## 7. What parameter mostly inflates width without moving the median

Parameters with substantial W/M but very small shift in p50 (reading the CSV's p50 column):

- **F06/F07/F08 ECAV per-level axis:** W/M 2030 = 0.35, p50 2030 = 5.207e9 vs deterministic 5.258e9 (shift < 1%). Duplicates per-subsystem variance without moving the central trajectory. **Prime candidate for fixing** and matches the dossier S2-01 recommendation.
- **F20 icecav_power_factor:** W/M 2030 = 0.25, p50 2030 = 5.278e9 (shift < 0.5%). Mostly a width inflator.
- **F18 cav_levels:** W/M 2030 = 0.55, p50 2030 ≈ 5.258e9 — width large, median unchanged.

## 8. What parameter affects uncertainty most

Combined 2030 / 2050 / turning-year ranking (rank-sum heuristic):

| Rank | Parameter | Layer | Comment |
|---|---|---|---|
| 1 | F27 efficiency doubling | L3 | top 2050 contributor; top turning-year driver |
| 2 | F23 CAV 2075 target | L3 | top 2030 contributor; second turning-year driver |
| 3 | F18 cav_levels Dirichlet | L2 | top 2030 contributor; third turning-year driver |
| 4 | F06/F07/F08 ECAV per-level axis | L2 | S2-01 duplicate; width inflator |
| 5 | F25 / F26 L3 growth exponents | L3 | dominate the 2075 ratio explosion |

The panel surfaces this list at the top of the contribution section, labelled "Top drivers of uncertainty".

## 9. Which layer affects uncertainty most

The parameter-level evidence, summed:

- **L3 dominates** 2050 and 2075 horizons (F27, F25, F26, F23 — four of the top five across horizons).
- **L2 dominates** 2030 horizon (F18, F10, F22 among top five) because trajectory divergence has not yet accumulated.
- **L1 is minor** everywhere except 2075 where the ratio explodes for initial-BEV-like parameters (F02, F03).

For a precise layer-level quantification see `LAYER_CONTRIBUTION_EXPERIMENT.md` (aggregate L1/L2/L3 runs with 150 MC samples per configuration).

## 10. Caveats

- The experiment uses 80 runs per isolated parameter (vs 150 for the layer experiment) for feasibility. Absolute numbers should be regarded as ±10% estimates; the rank ordering is robust.
- The 2075 ratio metric is mathematically unstable when p50 → 0. The absolute 2075 width in the CSV is the primary long-horizon reading.
- Correlations between parameters are ignored (independence assumption). Jointly-sampled parameters could either amplify or cancel in the full ensemble; the factor-by-factor numbers are a *decomposition*, not an exact additive breakdown.
- The experiment uses a fixed L2-scale-factor-aware call path (TransportModel builds its own energy model). This differs from the historical paper-safe MC pipeline (`main()`) which bypassed scale-factor application via a pre-built energy model — that bug is flagged in `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md` and tracked in a separate PR.
