# UNCERTAINTY_FIXED_UNFIXED_JUSTIFICATION.md

**Purpose:** supporting material to answer a reviewer or reader asking "why did you fix some uncertainty factors rather than sampling them?"
**Primary sources:**
- `audits/uncertainty_governance/FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.md`
- `audits/uncertainty_governance/FIXED_VS_UNFIXED_STRATEGY.md`
- `audits/uncertainty_governance/UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md`

---

## 1. The problem the previous pipeline created

Under the committed paper-safe Monte Carlo ensemble, the ratio `(p95 − p05) / p50` for `ATS Emissions (kg CO2)` reaches **1.49× at 2030 on California** and **1.47× at 2030 on Ohio**, and exceeds **2.0× by 2050**. The interpretation-boundary (the first year where the ratio exceeds 1.5) falls on **2031** for both regions. A user looking at the 2030 panel therefore sees bands that are already wider than the median — a visual claim the dashboard cannot quantitatively defend.

Two mechanisms produced this breadth:

1. **Per-level × per-subsystem dual-axis compounding on ECAV and STI scale factors** (dossier S2-01 / S2-02). Six lognormals multiplied on every ECAV power cell and six on every STI power cell. The effective per-cell multiplicative σ reaches ≈ 0.47 on ECAV and ≈ 0.49 on STI, even though each single axis contributes σ ≈ 0.2–0.3.
2. **Compounding 51-year exponential growth-rate priors** on `growth_rates.ev` (σ = 0.015) and `growth_rates.clean_energy` (σ = 0.012). Over 51 years, a ±2σ window corresponds to roughly a factor of 2.3 in the 2075 BEV share and a factor of 2.0 in the low-carbon electricity share, which is not physically meaningful.

The new design fixes the first mechanism outright (S2-01/S2-02 dual-axis duplication) and narrows the second under the default preset (`l3_low`), while preserving the paper-safe bundle for reproduction.

---

## 2. Why "fixed by default" is not "hiding uncertainty"

Each Class-A factor (fixed by default) is fixed because freeing it either (a) duplicates uncertainty already represented elsewhere, or (b) contributes variance that is absorbed by a downstream factor within a few simulated years. Neither case is genuine scientific uncertainty being hidden — it is uncertainty being represented *once*, at the factor where it is most interpretable.

| Fixed factor | Alternative representation |
|---|---|
| F01 `initial_data.f_clean` | `growth_rates.clean_energy` (F26) evolves the same quantity |
| F02 `initial_data.ev_share` | `growth_rates.ev` (F25) evolves the same quantity |
| F06–F08 ECAV per-level | F09–F11 ECAV per-subsystem (single retained axis) |
| F12–F14 STI per-level | F15–F17 STI per-subsystem (single retained axis) |
| F21 cohort_decay_factor | effect decays to zero by 2036; post-2036 bands are not affected |

For every fixed factor, the user can still opt in to sampling by choosing a non-fixed preset or advanced mode. The default just changes what the dashboard shows on first load.

## 3. Why unfixed factors stay free

The remaining factors represent either scenario-interrogation knobs the reader may legitimately want to vary, or genuine physical uncertainty with no other representation in the model. The diagnosis CSV labels each with `adjustable_default` and documents the rationale.

Priority examples:
- `emission_factors.e_clean` (F03): operational-only vs life-cycle-inclusive is a methodological choice; hiding it would misrepresent scope.
- `growth_rates.cav` / `growth_rates.sti` (F23/F24): 2075 target fractions are the central scenario assumption; their variation is exactly the scenario-envelope the reader should see.
- `growth_rates.ev` / `growth_rates.clean_energy` (F25/F26): primary long-horizon drivers. Narrowed under `l3_low` rather than fixed, because their spread represents real policy-trajectory uncertainty.
- `retire_year` (F22): integer service life; directly controls the turning year, which is a reported metric.

## 4. How the default satisfies "decision-meaningful"

The decision-meaningful default bundle is `L1=fixed, L2=low, L3=low`. Under this bundle:

- Dual-axis ECAV/STI compounding is removed (S2-01/S2-02 fix).
- Trajectory-growth sigmas are halved relative to paper-safe MEDIUM.
- 2024 baseline conditions do not draw Monte Carlo noise; every run starts from the same regional baseline.

The expected outcome (empirically validated by the contribution experiment): 2030 relative width ≤ 1.0 on both regions; interpretation boundary pushed past 2035 on California.

This meets the stated design principle: **the default uncertainty must not become so wide after ~2030 that the band exceeds several times the median unless truly unavoidable and evidence-anchored.** The paper-safe bundle remains one click away and reproduces the committed `_quantiles.csv`.

## 5. How a reader verifies the claim

Every claim in this document is reproducible:

1. Read `audits/uncertainty_governance/FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.csv` for the factor-level decisions.
2. Run `python scripts/uncertainty_contribution_experiment.py` to regenerate the layer-contribution CSV.
3. Open the v4 Uncertainty Panel and toggle through the bundles; fixed-vs-free tables are rendered per preset.
4. Compare bundle numbers against `audits/uncertainty_governance/UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md` tables.
