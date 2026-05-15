# FIXED_VS_UNFIXED_STRATEGY.md

**Date:** 2026-04-15
**Purpose:** Formalise which Monte Carlo priors are **fixed by default** in the next-version CLEAR-ATS dashboard, which remain **adjustable by default**, and why. The guiding principle is that the paper-safe default uncertainty should not become so wide after ~2030 that the band exceeds several times the median — unless that breadth is truly unavoidable and evidence-anchored.
**Pairs with:**
- `FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.md` / `.csv` (per-factor rationale)
- `GROUPED_PRESET_DESIGN.md` (how presets encode this strategy)
- `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md` / `.csv` (empirical contribution evidence)

---

## 1. Four-class taxonomy

Every ordinary-MC factor is placed in one of four classes:

| Class | Meaning | User exposure |
|---|---|---|
| **A. Fixed by default** | Factor is held at its central value under the paper-safe default. User can opt in to sampling via a non-default preset, but the default dashboard state has no Monte Carlo variance on this factor. | Visible in the UI as a *fixed pill* with the fixed value; an "Unfix" option is available in advanced mode. |
| **B. Adjustable in normal use** | Factor is sampled in the paper-safe default. User can narrow or widen via grouped presets. The central value is preset-invariant. | Visible in the UI as a *free pill* with its current preset-selected width. |
| **C. Exploratory only** | Factor is sampled only when the user explicitly selects an exploratory preset (e.g. `l3_high`). Default dashboard leaves this factor fixed (same effect as class A in the paper-safe baseline) but flags it as available for what-if exploration. | Visible in an *exploratory* tab only; paper-safe badge explicitly says "off". |
| **D. Never exposed directly** | Factor is structural; changing it changes the scenario, not the uncertainty. Examples: model variants (adoption curve shape), 2075 ramp linearity, base-year. Also includes structural shock factors, which are NEVER folded into ordinary MC. | Not exposed on the ordinary-MC panel at all. Structural shocks have their own panel. |

---

## 2. Strategy per layer

### L1 — baseline-data and emission-factor priors

| Factor | Class | Justification |
|---|---|---|
| F01 `initial_data.f_clean` | **A (Fixed by default)** | Regional 2024 measurement. Beta(kappa=80) spread swamped within ~3–5 years by F26 compounding. Fixing improves early-horizon readability, removes double-counting with F26. |
| F02 `initial_data.ev_share` | **A (Fixed by default)** | Same pattern with F25 as the eraser. Beta(kappa=120) spread negligible after 2030. |
| F03 `emission_factors.e_clean` | **B (Adjustable)** | Operational-only vs life-cycle-inclusive is a real scenario choice. Kept free; spread narrowed under `l1_low`. |
| F04 `emission_factors.e_fossil` | **B (Adjustable)** | Physically bounded but non-trivial technological disagreement (NGCC to coal). |
| F05 `emission_factors.e_gasoline` | **B (Adjustable)** | Narrow physical uncertainty; kept free for symmetry with F03/F04. |

**Paper-safe default effect of fixing F01 and F02:** the 2030 uncertainty width on ATS Emissions in Ohio drops from ~0.15 (L1-only) to ~0.14 (F03–F05 only), i.e. roughly a 10% reduction driven almost entirely by the removal of the residual constant offset. The main effect is NOT a width reduction — it is a cleaner interpretation story for the reader.

### L2 — load-model priors

| Factor | Class | Justification |
|---|---|---|
| F06 `ecav_scale_factors.L3` | **A (Fixed by default)** | Dossier S2-01. Dual-axis duplication. Fix removes ~25–30% of ECAV-band width at 2030. |
| F07 `ecav_scale_factors.L4` | **A (Fixed by default)** | S2-01. |
| F08 `ecav_scale_factors.L5` | **A (Fixed by default)** | S2-01. |
| F09 `ecav_scale_factors.sensing` | **B (Adjustable)** | Per-subsystem axis retained. |
| F10 `ecav_scale_factors.computing` | **B (Adjustable)** | Per-subsystem axis retained. |
| F11 `ecav_scale_factors.communication` | **B (Adjustable)** | Per-subsystem axis retained. Largest single lognormal sigma. |
| F12–F14 `sti_scale_factors.{Basic,Semi,Highly}` | **A (Fixed by default)** | Dossier S2-02. Same duplication pattern on STI. |
| F15–F17 `sti_scale_factors.{sensing,computing,communication}` | **B (Adjustable)** | Per-subsystem STI axis retained. |
| F18 `cav_levels` | **B (Adjustable)** | Dirichlet mix; genuine scenario choice. |
| F19 `sti_levels` | **B (Adjustable)** | Dirichlet mix; genuine scenario choice. |
| F20 `icecav_power_factor` | **B (Adjustable)** | Alternator-overhead triangular; narrow physical range. |
| F21 `cohort_decay_factor` | **A (Fixed by default)** | Effect vanishes after 2036 cohort rotation; fixing eliminates an early-horizon only term. |
| F22 `retire_year` | **B (Adjustable)** | Evidence-anchored; controls turning year — the reader may legitimately want to vary it. |

**Paper-safe default effect of L2 dual-axis fix:** removes the full S2-01/S2-02 duplication. Quantitative evidence in `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv` shows the resulting L2-only band narrows by roughly 20–30% on the 2030 horizon.

### L3 — trajectory priors

| Factor | Class | Justification |
|---|---|---|
| F23 `growth_rates.cav` | **B (Adjustable)** | 2075 target fraction is the single largest long-horizon driver; narrowed under `l3_low` and `l3_medium`. |
| F24 `growth_rates.sti` | **B (Adjustable)** | Same story on STI side. |
| F25 `growth_rates.ev` | **B (Adjustable, narrowed default)** | Compounding exponent; MEDIUM sd=0.015 is scaled to 0.0075 in `l3_low`. |
| F26 `growth_rates.clean_energy` | **B (Adjustable, narrowed default)** | Largest driver of interpretation boundary; sd=0.012 → 0.006 under `l3_low`. |
| F27 `growth_rates.efficiency_doubling` | **B (Adjustable)** | Moore-style doubling time; narrowed under `l3_low`. |
| F28 `growth_rates.total_car_increase` | **B (Adjustable)** | Demographically bounded; low contribution. |

**Default preset decision:** L3 runs under `l3_medium` as the paper-safe default when the user chooses the "paper-safe" preset bundle, but the panel's *recommended decision-meaningful default* is `l3_low`, because MEDIUM L3 priors are precisely what causes the post-2030 > 1.5×p50 width. Users asking "what does my policy choice imply?" are better served by the narrower default; users reproducing the paper use the `l3_medium` explicit preset.

### Structural shocks

All five shock factors (SHK01–SHK05) are **Class D**. Never in ordinary MC. Exposed on a separate Structural Shocks panel.

### Underconstrained

F29 (18 absolute per-level-per-subsystem power cells with no prior) is **Class C (exploratory only)** in the sense that no sampling happens; but it is disclosed on the panel as a known L2 gap that the current preset scheme cannot close.

---

## 3. Why fixing improves interpretability

For each Class-A factor we document the specific interpretability gain, not just a vague "narrower is better":

- **F01 / F02.** The 2024 baseline is fixed across runs, so the reader sees the same starting point on every trajectory. This makes it possible to interpret band widening as *trajectory divergence*, not as *starting-condition noise + trajectory divergence*. The distinction matters in the figure caption.
- **F06–F08 and F12–F14.** Dual-axis compounding is disclosed and eliminated from the default band. The reader is not shown an inflated band that encodes two representations of the same uncertainty. This meets a known referee objection on earlier drafts (S2-01/S2-02 in the dossier).
- **F21.** Cohort-decay variance only lives in the first 12 simulated years, so variance on the 2050 and 2075 band from this factor is zero by construction. Fixing removes an early-horizon wrinkle that cannot propagate.

## 4. Why unfixed factors stay visible

- **F03 / F04 / F05 (emission factors).** The high-low span of `e_clean` (0.01–0.08) encodes a real methodological choice between operational-only and life-cycle-inclusive accounting. Hiding this spread would misrepresent scope.
- **F09 / F10 / F11 (per-subsystem ECAV).** One axis of load-model uncertainty is necessary to reflect device-to-device and vendor-to-vendor variance. Removing it would leave zero L2 variance.
- **F15 / F16 / F17 (per-subsystem STI).** Same argument on the roadside side.
- **F18 / F19 (Dirichlet mixes).** Level-mix is a legitimate modelling choice; the reader should see the simplex breath.
- **F22 (retire_year).** Integer service life is a policy / regulation input.
- **F20 (icecav_power_factor), F23–F28 (trajectory).** All are scenario-interrogation knobs.

## 5. Narrowed-default decision for L3

The most important decision in this document: we set the **default dashboard L3 preset to `l3_low`** rather than `l3_medium`, and we advertise `l3_medium` explicitly as "paper-safe reproduction". The reason is decision-meaningfulness: a width-to-median ratio above 1.5 at 2030 fails the threshold that the interpretation-boundary module uses to separate "quantitative band" from "scenario-conditioned envelope". The `l3_low` preset keeps the 2030 width/median ratio below 1.0 on California and comparable on Ohio (see `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv`), so a reader making a 2030 policy decision can read a bounded quantitative band.

This is **not** a redefinition of the paper-safe number. The paper-safe MEDIUM preset is still available in one click. We are choosing the *default dashboard state*, not the paper number.

## 6. Summary table

| Layer | Class-A (fixed default) | Class-B (adjustable) | Class-C (exploratory) | Class-D (never) |
|---|---|---|---|---|
| L1 | F01, F02 | F03, F04, F05 | — | model_variants |
| L2 | F06–F08, F12–F14, F21 | F09–F11, F15–F20, F22 | F29 | base_year / target_year |
| L3 | — | F23–F28 (default preset is `l3_low`) | — | 2075 ramp linearity |
| SHOCK | — | — | — | SHK01–SHK05 |
