# PARAMETER_CLASSIFICATION_FINAL.md

**Date:** 2026-04-15
**Status:** final. Supersedes the earlier `PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.md` and earlier grouped-per-layer designs. This is the parameter-level classification used by the single Scenario Explorer uncertainty section.
**Machine-readable companion:** `PARAMETER_CLASSIFICATION_FINAL.csv`
**Paired docs:** `DEFAULT_PARAMETER_FIXING_RULES.md`, `PARAMETER_LEVEL_PRESET_LOGIC_FINAL.md`, `QUICK_BUNDLE_MAPPING.md`, `PARAMETER_IMPORTANCE_EXPERIMENT.md`, `LAYER_IMPORTANCE_SUMMARY.md`, `OHIO_PARAMETER_PRIOR_JUSTIFICATION.md`.

---

## 1. Decision to classify per-parameter, not per-layer

Layer-level low / medium / high was rejected because:

- Inside L2, `F06–F08` (ECAV per-level) and `F09–F11` (ECAV per-subsystem) are a *dual-axis* product on every cell. A layer-level "L2 low" cannot distinguish "drop the duplicated axis" from "narrow the retained axis".
- Inside L3, `F23` (2075 CAV target) and `F25` (EV growth exponent) drive different mechanisms (ramp endpoint vs compounding exponent). A layer-level "L3 low" cannot narrow one without the other.
- Inside L1, `F01 / F02` are measurement-grade absorbed-within-5-years parameters; `F03 / F04 / F05` are methodological choices. Grouping them onto one knob is a category error.

The final classification is per-parameter; L1 / L2 / L3 are retained only for navigation and as contribution summaries.

## 2. Classification schema

For each parameter we record:

| Column | Meaning |
|---|---|
| `param_id` | stable identifier (`F01` … `F28`, plus `F29` and `SHK01–05`). |
| `config_path` | dotted path into `scenarios/{region}/scenario.json`. |
| `layer` | L1 / L2 / L3 / SHOCK (navigational only). |
| `physical_meaning` | one-line description. |
| `current_distribution` | prior family. |
| `current_parameterization_CA_OH` | committed hyper-parameters per region. |
| `can_be_fixed` | whether the parameter can reasonably be held at its central value. |
| `must_remain_uncertain` | whether fixing it would materially mislead the reader. |
| `too_weak_to_expose` | whether the parameter is too weakly justified to put in front of a user. |
| `lmh_meaningful` | whether the full {low, medium, high} vocabulary is scientifically meaningful. |
| `allowed_levels` | the final allowed-control-set (subset of `{fixed, low, medium, high}` plus the two special tags `hidden_internal_only` and `structural_shock_only`). |
| `affects` | one or more of level / width / turning_year / interp_boundary / long_horizon / early_horizon_only. |
| `duplicates_effect_with` | other parameter IDs whose variance overlaps. |
| `default_level` | level chosen by the recommended-default bundle. |
| `paper_safe_level` | level chosen by the paper-safe-reproduction bundle. |
| `rationale` | one-line decision justification. |

## 3. Allowed-level distribution across parameters

Six distinct allowed-level sets are used. Every parameter maps to exactly one:

| Allowed-level set | Parameters | Count |
|---|---|---:|
| `{fixed}` only | F06, F07, F08, F12, F13, F14, F21 | 7 |
| `{fixed, low}` | F01, F02, F05, F20, F28 | 5 |
| `{fixed, low, medium}` | F03, F04, F09, F10, F11, F15, F16, F17, F18, F19, F22 | 11 |
| `{fixed, low, medium, high}` | F23, F24, F25, F26, F27 | 5 |
| `hidden_internal_only` | F29 | 1 |
| `structural_shock_only` | SHK01–SHK05 | 5 |

**Only 5 parameters get the full {low, medium, high} vocabulary**, and every one of them is a trajectory-scenario knob (2075 targets or compounding growth exponents). This is the user-requested discipline: LMH is defined only where scientifically meaningful.

## 4. Per-parameter rationale (summary)

Detailed rationales are in the CSV `rationale` column. Highlights:

- **F01 / F02 — fixed or low only.** Previous MEDIUM Beta widths were uninformative inflation (single EIA or AFDC measurement treated as if it had wide disagreement). Evidence supports only `low` (κ × 2) at most; the fixed default is recommended because downstream growth exponents absorb the offset in 3–5 years.
- **F03 — fixed / low / medium.** Methodological choice (operational vs life-cycle); MEDIUM retains the life-cycle-inclusive upper tail and is required for paper reproduction. HIGH rejected.
- **F04 — fixed / low / medium.** NGCC-to-coal technology span is real. HIGH rejected (no technology outside the span).
- **F05 — fixed or low only.** Tight EPA range; previous MEDIUM inflation was unjustified.
- **F06–F08 and F12–F14 — FIXED ONLY.** Dossier S2-01 / S2-02 dual-axis duplication. Any non-fixed value double-counts variance; scientific correctness requires fixed only.
- **F09–F11 and F15–F17 — fixed / low / medium.** Retained per-subsystem axis. HIGH rejected (MEDIUM already spans documented measurement disagreement).
- **F18 / F19 — fixed / low / medium.** Dirichlet level mix. HIGH rejected (below-MEDIUM alpha produces near-uniform simplex draws which are not physically meaningful).
- **F20 — fixed or low only.** Narrow physical ICECAV overhead. MEDIUM inflated the triangular beyond the alternator-overhead literature.
- **F21 — FIXED ONLY (hidden).** Cohort decays out by 2036; no effect on any post-2036 metric. Classified hidden-internal-only per the user's explicit category.
- **F22 — fixed / low / medium.** Service life; MEDIUM spans the 8–20-year literature. HIGH rejected.
- **F23 / F24 — full LMH.** 2075 target fractions are the primary trajectory-scenario knobs; reader must be able to interrogate them. HIGH exploratory.
- **F25 / F26 — full LMH.** Compounding growth exponents; same rationale. HIGH exploratory.
- **F27 — full LMH.** Moore-style efficiency doubling time; top turning-year-sensitivity driver. HIGH exploratory.
- **F28 — fixed or low only.** Demographically bounded (Census-based); MEDIUM width was unsupported.
- **F29 — hidden_internal_only.** 18 absolute ECAV/STI power cells without a direct prior. Variance routes through scale factors; a true joint prior is deferred. Disclosed but never user-tunable.
- **SHK01–SHK05 — structural_shock_only.** Invoked only from the Structural Shocks panel; never in ordinary MC.

## 5. Duplication audit

| Duplication | Parameters involved | Final resolution |
|---|---|---|
| ECAV dual-axis (S2-01) | F06–F08 duplicate F09–F11 | F06–F08 classified FIXED ONLY |
| STI dual-axis (S2-02) | F12–F14 duplicate F15–F17 | F12–F14 classified FIXED ONLY |
| 2024 BEV ↔ growth | F02 partial duplicate of F25 | F02 default FIXED |
| 2024 grid ↔ growth | F01 partial duplicate of F26 | F01 default FIXED |

## 6. Effect map

From `PARAMETER_IMPORTANCE_EXPERIMENT.csv` (California, 80 MC runs isolated):

- **Top 2030 drivers** (width / median): F23 (0.56), F27 (0.56), F18 (0.55), F10 (0.44), F22 (0.40).
- **Top 2050 drivers:** F27 (1.02), F23 (0.56), F18 (0.51), F02 (0.44), F09 (0.43).
- **Top turning-year destabilisers (years):** F27 (16), F23 (9), F18 (7), F06/F07/F08 axis (5).
- **Interpretation-boundary triggers (alone):** F02 (2062), F25 (2062).

F27 is the single largest driver at 2050 and of turning-year. F23 is the single largest at 2030.

## 7. Regional handling (Ohio ≠ California)

All L3 parameter specs support Ohio-specific overrides via the `_regions.ohio` key in each level spec. Concretely for the recommended-default bundle (LOW):

| Parameter | California LOW | Ohio LOW |
|---|---|---|
| F23 2075 CAV target | triangular(0.35, 0.45, 0.55) | triangular(0.20, 0.30, 0.40) |
| F24 2075 STI target | triangular(0.40, 0.50, 0.60) | triangular(0.20, 0.30, 0.45) |
| F25 EV growth | N(0.07, 0.0075, [0.04, 0.10]) | N(0.055, 0.010, [0.03, 0.085]) |
| F26 clean-energy growth | N(0.05, 0.006, [0.03, 0.07]) | N(0.035, 0.008, [0.02, 0.055]) |
| F28 total_car_increase | N(0.002, 0.0005, [-0.001, 0.007]) | N(0.001, 0.0005, [-0.002, 0.004]) |

The Ohio scenario file centres are also updated to Ohio modes (cav = 0.30, sti = 0.30, ev = 0.055, clean_energy = 0.035, total_car_increase = 0.001). See `OHIO_PARAMETER_PRIOR_JUSTIFICATION.md` for the evidence.

## 8. Structural shocks

SHK01–SHK05 are never folded into ordinary Monte Carlo at any level. They live on the Structural Shocks panel and are invoked as discrete labelled scenarios with their own output namespace (`results/shocks/`).

## 9. Invariants enforced by the panel

- Every parameter's `default_level` and `paper_safe_level` ∈ `allowed_levels`.
- No `_regions.<region>` override keys leak into the final `data_uncertainty` block (stripped before substitution).
- Structural shocks never appear as radio choices on the Scenario Explorer uncertainty tier.
- `F29 / F21` render as read-only badges ("hidden" / "fixed-only") with no radio.
- Dual-axis duplicates (F06–F08, F12–F14) render with a single "fixed" pill and a tooltip pointing to the S2-01 / S2-02 dossier entry.
