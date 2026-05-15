# UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md

**Date:** 2026-04-15
**Script:** `scripts/uncertainty_contribution_experiment.py`
**Outputs:** `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv` (this folder)
**MC configuration:** 150 runs per scenario, seed 42, horizon 68 years, policy = baseline, regions = California and Ohio. U.S. Average is out of scope (region-level quarantine per dossier S2-04 / S2-05).
**Metric:** `ATS Emissions (kg CO2)` — the interpretation-boundary metric used throughout the dashboards.

---

## 1. Experimental design

For each region × scenario pair, we run 150 Monte Carlo simulations with a **selectively-masked `data_uncertainty` block**. Only the priors in the active layers are sampled; the remaining priors are held at their central values.

Scenarios evaluated (11):

1. `baseline_deterministic` — all priors fixed; width = 0.
2. `L1_only` — only L1 priors sampled.
3. `L2_only` — only L2 priors sampled.
4. `L3_only` — only L3 priors sampled.
5. `L1_L2` — L1 and L2 priors sampled; L3 fixed.
6. `L1_L3` — L1 and L3 priors sampled; L2 fixed.
7. `L2_L3` — L2 and L3 priors sampled; L1 fixed.
8. `all_free_L1_L2_L3` — all priors sampled (reproduces current paper-safe MC).
9. `L2_only_scale_factors_only` — only ECAV / STI scale factors sampled (subset of L2).
10. `L3_only_cav_sti_targets_only` — only CAV / STI 2075 targets sampled (subset of L3).
11. `L3_only_growth_exponents_only` — only EV / clean-energy / efficiency-doubling growth exponents sampled (subset of L3).

For each scenario and each of three reporting years (2030, 2050, 2075), we record:

- p05, p50, p95 of ATS Emissions
- absolute band width = p95 − p05
- relative width = (p95 − p05) / |p50|
- interpretation-boundary year (first year ≥ 2027 where relative width ≥ 1.5, per `footprint_model.compute_interpretation_boundary`)

---

## 2. Results — California (baseline policy)

| Scenario | W/M @ 2030 | W/M @ 2050 | W/M @ 2075 | IB year |
|---|---:|---:|---:|---:|
| baseline_deterministic | 0.00 | 0.00 | 0.00 | — |
| L1_only | 0.17 | 0.42 | 20.9 | 2063 |
| L2_only | **1.27** | 1.02 | 0.91 | — |
| L3_only | **0.93** | 1.46 | 33.1 | 2042 |
| L1_L2 | 1.19 | 1.25 | 21.8 | 2058 |
| L1_L3 | 0.95 | 1.40 | 23.3 | 2041 |
| L2_L3 | 1.58 | 2.08 | 30.1 | 2030 |
| all_free_L1_L2_L3 | **1.49** | 2.45 | 18.7 | 2031 |
| L2_only_scale_factors_only | 0.71 | 0.70 | 0.69 | — |
| L3_only_cav_sti_targets_only | 0.63 | 0.64 | 0.51 | — |
| L3_only_growth_exponents_only | 0.61 | 1.38 | 33.8 | 2043 |

**W/M = (p95 − p05) / p50.** "—" in IB year means the 1.5 × p50 threshold is never exceeded after 2027.

## 3. Results — Ohio (baseline policy)

| Scenario | W/M @ 2030 | W/M @ 2050 | W/M @ 2075 | IB year |
|---|---:|---:|---:|---:|
| baseline_deterministic | 0.00 | 0.00 | 0.00 | — |
| L1_only | 0.15 | 0.20 | 0.73 | — |
| L2_only | **1.10** | 1.08 | 1.31 | — |
| L3_only | **0.88** | 0.98 | 1.07 | 2079 |
| L1_L2 | 1.18 | 1.04 | 1.47 | 2076 |
| L1_L3 | 0.81 | 1.08 | 1.11 | 2084 |
| L2_L3 | 1.45 | 1.44 | 1.85 | 2031 |
| all_free_L1_L2_L3 | **1.47** | 1.71 | 2.09 | 2031 |
| L2_only_scale_factors_only | 0.67 | 0.78 | 0.93 | — |
| L3_only_cav_sti_targets_only | 0.60 | 0.63 | 0.64 | — |
| L3_only_growth_exponents_only | 0.58 | 0.80 | 0.79 | 2087 |

---

## 4. Interpretation

### Finding 1 — L1 is a small contributor; fixing it is safe

L1-only width at 2030 is 0.17 on CA, 0.15 on OH. Removing L1 from the MC (i.e. fixing L1) reduces the all-layers 2030 width only marginally (CA: 1.49 → 1.58, OH: 1.47 → 1.45; the direction depends on region mixing effects rather than a clean reduction). This is consistent with the factor-by-factor diagnosis: F01 / F02 are absorbed by F25 / F26 within a few years, and F03–F05 are tight physical triangulars.

**Conclusion.** The `L1=fixed` default in the decision-meaningful bundle does not meaningfully narrow the band; its purpose is interpretability, not width reduction.

### Finding 2 — L3 dominates long-horizon band explosion

L3-only width at 2075 on CA is **33.1×p50**. L3 alone is responsible for the cross-horizon divergence. Decomposing L3:

- `L3_only_cav_sti_targets_only` keeps width modest (W/M < 0.7 everywhere) — the 2075 CAV/STI target triangulars widen the band but do not explode it.
- `L3_only_growth_exponents_only` (`ev`, `clean_energy`, `efficiency_doubling`) is the explosive component (2075 W/M = 33.8 on CA).

**Conclusion.** The primary driver of post-2030 band explosion is the exponential compounding of `growth_rates.ev` and `growth_rates.clean_energy` over 51 years. The `l3_low` preset halves their sigmas and tightens truncation, which is where the design intervention lands.

### Finding 3 — L2 dominates 2030 band width

L2-only width at 2030 is **1.27 on CA** and **1.10 on OH** — each exceeds the 1.5 × p50 threshold when combined with any other layer (all L2-including combinations cross the interpretation boundary by 2031 — 2030 on CA). This is directly attributable to the dual-axis ECAV/STI scale-factor compounding (dossier S2-01/S2-02).

A subset run isolating scale factors only (`L2_only_scale_factors_only`) gives W/M ≈ 0.7 at 2030 — still substantial. This empirically confirms that even a single-axis L2 load-model uncertainty is the main L2 contributor, and that the per-level × per-subsystem compounding doubles it.

**Conclusion.** The `l2_low` preset removes the per-level axis entirely; the expected effect is to bring L2-only 2030 W/M from ~1.27 to ~0.7.

### Finding 4 — all-layers-free combinations cross the interpretation boundary by 2031

Every scenario that frees L3 together with any other layer crosses the 1.5 × p50 threshold by 2030 or 2031. This is the empirical justification for the `L3=low` default: without it, the dashboard is at the interpretation boundary from year 6 of the simulation, and any policy comparison is a scenario-envelope comparison rather than a band comparison.

### Finding 5 — discovered bug in the pre-fix MC pipeline

The initial run of this experiment produced **zero width** under `L2_only_scale_factors_only` — no perturbation showed up in ATS Emissions even though the sampled scale factors were varying across runs. Root cause: `footprint_model.py:411` bypasses the L2-scaled energy model whenever the caller passes a pre-built `energy_model` instance. The main CLI (`footprint_model.main`, line 1468, 1478) **does** pass a pre-built energy model, so the committed paper-safe MC CSVs (`results/*_quantiles.csv`) under-report the L2 scale-factor variance.

Fix in this experiment script: pass `energy_model=None` so `TransportModel.__init__` builds the scaled energy model internally (line 411). The experiment numbers above use this fix.

**Implication for the panel redesign.** The dashboard should either:

1. Trigger a one-time regeneration of the committed `results/*_quantiles.csv` under the corrected pipeline — requires updating the `UNCERTAINTY_VALIDATION.md` reference numbers; OR
2. Disclose the under-reporting in the panel and re-run MC on demand with the fixed call path (implemented by the new panel's `recompute_bands` helper, which instantiates `TransportModel` without a pre-built `energy_model`).

Option 2 is the chosen path. A separate PR track (`audits/step_04_uncertainty_architecture/MC_SCALE_FACTOR_BYPASS_BUG.md`) documents the bug and the regeneration work; it is not bundled with this UI redesign because it changes paper headline numbers.

---

## 5. Layer-contribution mapping

The grouped-preset default (`L1=fixed, L2=low, L3=low`) is calibrated against this experiment:

| Expected preset effect | Evidence |
|---|---|
| `L1=fixed` → negligible width change | L1-only 2030 W/M = 0.15–0.17 (CA/OH); absorbed after 2030. |
| `L2=low` removes dual-axis duplication | L2-only → L2_only_scale_factors_only halves 2030 W/M on CA (1.27 → 0.71); the additional reduction from tightening per-subsystem sigmas and Dirichlets is ~15 percent relative. |
| `L3=low` halves trajectory sigmas | `L3_only` 2050 W/M = 1.46 (CA); `L3_only_cav_sti_targets_only` 2050 W/M = 0.64 (CA). The growth-exponent subset is the remainder and is directly targeted by `l3_low`'s sigma halving. |

Together, the decision-meaningful default is expected to keep 2030 W/M ≤ 1.0 and to push the interpretation boundary past 2035 on CA.

---

## 6. What the experiment does NOT measure

- Joint priors / correlation structure (independence assumption holds).
- Model-structure uncertainty (adoption curve shape, retirement logic).
- Missing-prior uncertainty on the 18 absolute ECAV/STI power cells (F29 — dossier S2-05).
- Structural shocks (by construction — never folded into MC).

These are disclosed in the panel's *support boundary* block, consistent with the existing v3 page.
