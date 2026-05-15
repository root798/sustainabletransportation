# V6_VALIDATION_REPORT — v6 validation and convergence

Checks every v6 output against a targeted list of invariants. If any fail, the
v6 release is not shippable. Run: `python v6_uncertainty_rearchitecture/scripts/validate_v6.py`.

Run context: 2026-04-19, demo design (40 outer × 20 inner, CA + OH, baseline,
seed 42). Results below reflect this run; re-validate when scaling up.

---

## 1. Deterministic non-regression vs v5

**Check**: v6 `compute_reference_path(region, policy, years=68)` with central
inputs must match v5 `python footprint_model.py --scenarios <region> --policy
<policy> --mc 0` bit-for-bit. Tolerance: max relative difference < 1e-6 on
every annual value of ATS Emissions and ATS Total Power.

**Result**:

| Region | Policy | Max rel. diff (ATS Emissions) | Max rel. diff (ATS Total Power) | Status |
| --- | --- | --- | --- | --- |
| California | baseline | 1.3e-16 | 1.3e-16 | **PASS** |
| Ohio | baseline | 2.1e-16 | 1.8e-16 | **PASS (after Ohio CSV regen)** |

**Discovered side issue**: on first run, Ohio validation reported 35% drift. Root cause: `results/ohio_results.csv` on disk was from before the v5.1.3 Ohio prior hardening (`scenarios/ohio/scenario.json` `cav 0.45→0.30`, `sti 0.50→0.30`, `ev 0.07→0.055`, `clean_energy 0.05→0.035`). Re-running `python footprint_model.py --scenarios ohio --policy baseline --mc 0` regenerates the CSV and v6 matches bit-exact. This is a stale-artefact finding — v6 itself is correct. It has been flagged in `memory/project_known_open_items.md` as a maintenance task and is unrelated to v6 code.

## 2. Outer design hygiene

**Check**: no NaN in any numeric column of `<region>__<policy>__outer_design.csv`.

| Region | n_outer | NaN-columns | Status |
| --- | --- | --- | --- |
| California | 40 | 0 | **PASS** |
| Ohio | 40 | 0 | **PASS** |

## 3. Benchmark-year monotonicity

**Check**: for every benchmark year (2030, 2035, 2045, 2055, 2075), the marginal
p05 ≤ p50 ≤ p95 of annual ATS emissions.

| Region | 2030 | 2035 | 2045 | 2055 | 2075 | Status |
| --- | --- | --- | --- | --- | --- | --- |
| California | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |
| Ohio | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |

Example California marginals (Mt CO₂e / year):

| Year | p05 | p50 | p95 |
| --- | --- | --- | --- |
| 2030 | 2.71 | 5.14 | 12.00 |
| 2035 | 4.34 | 8.52 | 20.78 |
| 2045 | 2.51 | 5.46 | 15.90 |
| 2055 | 0.37 | 3.53 | 8.83 |
| 2075 | 0.09 | 0.26 | 7.03 |

Example Ohio marginals (Mt CO₂e / year):

| Year | p05 | p50 | p95 |
| --- | --- | --- | --- |
| 2030 | 0.56 | 1.38 | 2.97 |
| 2035 | 0.89 | 2.35 | 5.74 |
| 2045 | 0.68 | 1.89 | 5.54 |
| 2055 | 0.78 | 1.76 | 4.07 |
| 2075 | 0.13 | 2.52 | 5.33 |

## 4. Convergence of outer cumulative-emissions p50

**Check**: cumulative drift of `cum_emis_p50` as the outer draw count is
expanded. Target: relative drift between final quarter and complete run < 2%.

### California

| n_outer | p50 cumulative (kg CO₂) | rel. drift from final |
| --- | --- | --- |
| 10 | 1.99e+11 | 7.4% |
| 20 | 2.50e+11 | 16.3% |
| 30 | 2.12e+11 | 1.6% |
| 40 (final) | 2.15e+11 | 0.0% |

Status: **PASS** (last step < 2%). 40 outer draws are the minimum for stable
ordering; 200 is recommended for publication.

### Ohio

| n_outer | p50 cumulative (kg CO₂) | rel. drift from final |
| --- | --- | --- |
| 10 | 1.41e+11 | 1.7% |
| 20 | 1.35e+11 | 2.3% |
| 30 | 1.38e+11 | 0.0% |
| 40 (final) | 1.38e+11 | 0.0% |

Status: **PASS**.

## 5. Surrogate fit quality

Random-forest surrogate R² on the training data (OOB-equivalent, limited by
demo design size):

| Region | Target | R² |
| --- | --- | --- |
| California | cum_emis_mean | 0.896 |
| California | peak_emis_mean | 0.900 |
| California | peak_year_mean | 0.960 |
| California | turning_year_mean | 0.862 |
| Ohio | cum_emis_mean | 0.902 |
| Ohio | peak_emis_mean | 0.910 |
| Ohio | peak_year_mean | 0.912 |
| Ohio | turning_year_mean | 0.964 |

All R² ≥ 0.86. Acceptable for dashboard-grade sensitivity rankings. Publication
claims should re-fit at `n_outer = 200`.

## 6. Sample-size sufficiency check

| Signal | Diagnosis at n_outer = 40 |
| --- | --- |
| Deterministic match | bit-exact — sample count irrelevant. |
| Benchmark-year monotonicity | holds at all benchmarks — sample count sufficient. |
| Cumulative convergence | ≤ 2% drift in last quarter — sample count marginally sufficient. |
| Sensitivity top-3 stability | stable across 3 re-seeds (verified manually). |
| Sensitivity long-tail ranking (ranks 4-10) | unstable; see `SENSITIVITY_RANKINGS_TABLE.md §D`. |

Recommendation: `n_outer = 40, n_inner = 20` is acceptable for a dashboard-
facing demo. Publication-grade figures require `n_outer ≥ 200, n_inner = 20`
and re-validation of this report.

## 7. What the validation explicitly does NOT cover

- Does not verify the v6 aleatoric-injected multipliers against real annual
  utilization / weather data. The `Normal(1.0, 0.02)` and `Normal(1.0, 0.015)`
  σ values are stated orders of magnitude, not calibrated estimates.
- Does not verify Sobol indices — SALib was not available in the demo
  environment. Publication runs should install `SALib>=1.4.7` and re-run
  `scripts/run_sensitivity.py --n-saltelli 2048`.
- Does not repeat the v5 8/8 assertion validation suite. The v5 harness
  (`scripts/run_assertions.py`) is still the authoritative suite for the
  legacy objects and is preserved intact.

## 8. Reproducibility

Every check in this report can be reproduced by:

```bash
# Regenerate Ohio baseline CSV if stale
python footprint_model.py --scenarios ohio --policy baseline --mc 0

# v6 nested MC + sensitivity + validation
python v6_uncertainty_rearchitecture/scripts/run_nested_mc.py \
    --regions california ohio --policy baseline \
    --n-outer 40 --n-inner 20 --years 68 --seed 42
python v6_uncertainty_rearchitecture/scripts/run_sensitivity.py \
    --regions california ohio --policy baseline
python v6_uncertainty_rearchitecture/scripts/validate_v6.py \
    --regions california ohio --policy baseline
```

Outputs appear in `v6_uncertainty_rearchitecture/results/`; summary JSON at
`v6_validation_report.json`.

## 9. Overall verdict

All five check categories (deterministic, hygiene, monotonicity, convergence,
surrogate fit) pass on the demo design. v6 is ready as a **dashboard-grade
rearchitecture demo**. Promotion to manuscript-facing requires re-running at
`n_outer = 200`, installing SALib, and re-generating this report.
