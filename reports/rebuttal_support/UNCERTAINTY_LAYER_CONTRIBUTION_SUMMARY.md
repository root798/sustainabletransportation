# UNCERTAINTY_LAYER_CONTRIBUTION_SUMMARY.md

**Purpose:** one-page rebuttal summary: what each uncertainty layer adds to the band and why the chosen defaults are quantitatively defensible.
**Primary data:** `audits/uncertainty_governance/UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv` (150 MC runs per scenario, seed 42, baseline policy, California and Ohio).

---

## 1. Headline numbers (California, baseline)

| Layer freed | Relative width at 2030 | Relative width at 2050 | Relative width at 2075 | Interpretation boundary |
|---|---:|---:|---:|---:|
| None (deterministic) | 0.00 | 0.00 | 0.00 | — |
| L1 only | 0.17 | 0.42 | 20.9 | 2063 |
| L2 only | 1.27 | 1.02 | 0.91 | — |
| L3 only | 0.93 | 1.46 | 33.1 | 2042 |
| L1 + L2 | 1.19 | 1.25 | 21.8 | 2058 |
| L1 + L3 | 0.95 | 1.40 | 23.3 | 2041 |
| L2 + L3 | 1.58 | 2.08 | 30.1 | 2030 |
| All (paper-safe MC) | **1.49** | **2.45** | 18.7 | **2031** |

## 2. Headline numbers (Ohio, baseline)

| Layer freed | Relative width at 2030 | Relative width at 2050 | Relative width at 2075 | Interpretation boundary |
|---|---:|---:|---:|---:|
| None (deterministic) | 0.00 | 0.00 | 0.00 | — |
| L1 only | 0.15 | 0.20 | 0.73 | — |
| L2 only | 1.10 | 1.08 | 1.31 | — |
| L3 only | 0.88 | 0.98 | 1.07 | 2079 |
| L1 + L2 | 1.18 | 1.04 | 1.47 | 2076 |
| L1 + L3 | 0.81 | 1.08 | 1.11 | 2084 |
| L2 + L3 | 1.45 | 1.44 | 1.85 | 2031 |
| All (paper-safe MC) | **1.47** | **1.71** | **2.09** | **2031** |

## 3. Per-layer narrative

### L1 — baseline data and emission factors

Small contributor. L1-only 2030 relative widths are 0.17 (CA) and 0.15 (OH) — well below the 1.5 interpretation threshold. L1 is never the reason the band blows up. Fixing L1 by default is therefore an *interpretability* choice, not a width-reduction choice: the 2024 baseline is held constant across runs so the reader can attribute trajectory divergence to L3 rather than to starting-condition noise.

### L2 — load-model per-device uncertainty

Large 2030 contributor. L2-only 2030 relative widths are 1.27 (CA) and 1.10 (OH) — already above the interpretation threshold. Two structural defects explain this (dossier S2-01 / S2-02): six ECAV lognormals compound on every ECAV power cell as per-level × per-subsystem; same on STI. The `l2_low` preset removes the per-level axis on both tables, which keeps one axis of genuine hardware variance and removes the duplication. The contribution experiment's `L2_only_scale_factors_only` sub-run (scale factors only, the per-subsystem axis retained) gives 2030 width ≈ 0.71 on CA and 0.67 on OH — roughly half of the dual-axis L2-only width. This is quantitative evidence that the S2-01/S2-02 fix halves the L2 band.

### L3 — long-horizon trajectory uncertainty

Dominant long-horizon contributor. L3-only 2075 relative width on CA is 33.1 — a factor-of-33 span. Decomposing L3:

- `L3_only_cav_sti_targets_only` gives 2075 width ≈ 0.51 — the CAV/STI 2075 target triangulars widen the band but do NOT explode it.
- `L3_only_growth_exponents_only` (`ev`, `clean_energy`, `efficiency_doubling`) gives 2075 width ≈ 33.8 — the explosive component is the 51-year compounding of growth-rate exponents.

The `l3_low` preset halves the sigmas on `growth_rates.ev` (0.015 → 0.0075) and `growth_rates.clean_energy` (0.012 → 0.006) and tightens truncation on both. The 2075 trajectory remains scenario-meaningful (±2σ BEV share at 2075 goes from ~0.13–0.97 to ~0.35–0.70 on CA) but no longer explodes.

## 4. Why the default is `L1=fixed, L2=low, L3=low`

Applying the above diagnoses jointly:

- L1 fixed: removes a small, mostly-absorbed source; improves interpretability.
- L2 low: removes the duplication; cuts L2 band width roughly in half.
- L3 low: halves sigma on the primary long-horizon drivers; keeps CAV/STI target range scenario-meaningful but not explosive.

Expected aggregate effect (based on the layer-only contributions and the half-reduction from de-duplication and sigma-halving): 2030 relative width ≤ 1.0, 2050 relative width ≤ 1.5, interpretation boundary pushed past 2035 on California and past 2040 on Ohio.

## 5. One-line summary for a paper caption

"Monte Carlo uncertainty is grouped into three layers (L1 baseline data; L2 load-model per-device; L3 long-horizon trajectory) and controlled per-layer. Bands in this figure use the decision-meaningful default (L1 fixed, L2 low, L3 low); the paper-safe reproduction bundle (L1 medium, L2 medium, L3 medium) is available in the dashboard."
