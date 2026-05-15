# PARAMETER_LEVEL_CONTROL_JUSTIFICATION.md

**Purpose:** respond to the reviewer question "why parameter-level uncertainty control, and why not a layer-level low / medium / high?"

**Primary sources:**
- `audits/uncertainty_governance/PARAMETER_CLASSIFICATION_FINAL.md`
- `audits/uncertainty_governance/DEFAULT_PARAMETER_FIXING_RULES.md`
- `audits/uncertainty_governance/PARAMETER_LEVEL_PRESET_LOGIC_FINAL.md`
- `audits/uncertainty_governance/PARAMETER_IMPORTANCE_EXPERIMENT.md`
- `audits/uncertainty_governance/LAYER_IMPORTANCE_SUMMARY.md`

---

## 1. Layer-level LMH is scientifically wrong for this system

A layer-level low / medium / high control asks the reader to accept three decisions at once for every parameter in the layer. That is wrong in at least three specific, documented ways:

1. **Inside L2 the S2-01 / S2-02 dual-axis duplication means that keeping F06–F08 at anything other than FIXED is a scientific error**, because those three lognormals multiply on every ECAV cell already sampled through F09–F11. A layer-level "L2 low" that still keeps F06–F08 free (even at a low sigma) still double-counts the variance. The correct action is to set F06–F08 to FIXED ONLY; a layer slider cannot express "part of L2 fixed, part at low".
2. **Inside L3, F23 (2075 target fraction) and F25 (compounding growth exponent) are different objects.** F23 is a linear-ramp endpoint; F25 is a compounding exponent. A reader interrogating "what if the 2075 CAV target is less aggressive?" should narrow F23 without also narrowing F25. A layer-level L3 selector cannot do this.
3. **Inside L1, F01 / F02 are absorbed-downstream measurements; F03 / F04 / F05 are methodological choices.** Grouping them on one knob is a category error — "tighten operational-vs-LCA choice" and "accept 2024 EIA reading as the fixed starting point" are decisions a user might want to make independently.

## 2. Parameter-level LMH is academically correct for this system

Every parameter is classified independently and carries exactly the allowed-level set that is scientifically meaningful for it:

| Allowed set | Parameters | Count |
|---|---|---:|
| `{fixed}` only | F06–F08, F12–F14, F21 | 7 |
| `{fixed, low}` | F01, F02, F05, F20, F28 | 5 |
| `{fixed, low, medium}` | F03, F04, F09, F10, F11, F15–F17, F18, F19, F22 | 11 |
| `{fixed, low, medium, high}` | F23, F24, F25, F26, F27 | 5 |

**Only five parameters — all trajectory-policy knobs — carry HIGH.** This matches the user's explicit requirement that LMH is defined only where it is scientifically meaningful.

## 3. Layer-level summaries remain, but only as explanation

L1 / L2 / L3 are retained in three places:

- **TIER B navigation.** Three expandable sections group the parameter radios for readability.
- **Figure B bar colouring.** Parameter bars are coloured by layer so the reader can see which layer drives each bar.
- **Figure C.** Explanatory grouped-bar chart showing L1 vs L2 vs L3 contributions at 2030 / 2050 / 2075.

Nothing in the control path depends on layer selection.

## 4. Which parameters are fixed by default, and why

Nine parameters are fixed by default (plus F29 hidden-only):

| Parameter | Why fixed |
|---|---|
| F01 `initial_data.f_clean` | measurement-grade 2024 EIA reading, absorbed by F26 in 3–5 years |
| F02 `initial_data.ev_share` | measurement-grade DOE AFDC reading, absorbed by F25 |
| F06, F07, F08 `ecav_scale_factors.{L3,L4,L5}` | dossier S2-01 dual-axis duplicate |
| F12, F13, F14 `sti_scale_factors.{Basic,Semi,Highly}` | dossier S2-02 dual-axis duplicate |
| F21 `cohort_decay_factor` | decays out of fleet by 2036, no effect on reported post-2036 metrics |

Plus F29 (18 absolute ECAV / STI cells) hidden-internal-only due to no available prior.

## 5. Which parameters remain uncertain by default, and why

Nineteen parameters remain uncertain at LOW by default:

| Parameter | Why uncertain |
|---|---|
| F03 e_clean | operational-vs-LCA methodological choice |
| F04 e_fossil | NGCC-vs-coal technology range |
| F05 e_gasoline | EPA physical range |
| F09, F10, F11 | retained per-subsystem ECAV axis after S2-01 fix |
| F15, F16, F17 | retained per-subsystem STI axis after S2-02 fix |
| F18, F19 | level-mix Dirichlet scenario knobs |
| F20 | alternator overhead physical range |
| F22 | vehicle service life range (controls turning year) |
| F23, F24 | 2075 target fraction scenario knobs (primary policy drivers) |
| F25, F26 | compounding growth exponents (primary long-horizon drivers) |
| F27 | efficiency doubling (primary turning-year destabiliser) |
| F28 | demographically-bounded fleet growth |

## 6. What parameter affects uncertainty most

From `PARAMETER_IMPORTANCE_EXPERIMENT.csv` (combined rank across 2030, 2050, turning-year spread):

1. **F27 `growth_rates.efficiency_doubling`** — top 2050 contributor (W/M = 1.02) and top turning-year destabiliser (16-year spread).
2. **F23 `growth_rates.cav`** — top 2030 contributor (W/M = 0.56), second turning-year destabiliser.
3. **F18 `cav_levels`** — top 2030 contributor (W/M = 0.55).
4. **F06–F08 per-level ECAV axis** — S2-01 duplicate; W/M = 0.35 at 2030.
5. **F25 / F26** — dominate 2075 band.

## 7. What layer affects uncertainty most

- **Overall: L3** (dominates 2050 and 2075 bands).
- **At 2030 specifically: L2** (L2-only 2030 W/M = 1.27 on CA, 1.10 on OH).
- **L1 is the smallest layer** at every horizon.

See `LAYER_IMPORTANCE_SUMMARY.md` for the full table.

## 8. Why the new default is decision-meaningful after 2030

The regenerated MC under the final default bundle (120 MC runs per region, seed 42, backend bug fixed):

| Region | W/M 2030 | W/M 2050 | Interpretation boundary |
|---|---:|---:|---|
| California, default | 0.83 | 0.88 | **2064** |
| California, paper-safe | 1.64 | 2.41 | 2028 |
| Ohio, default | 0.82 | 0.80 | **never** (within horizon) |
| Ohio, paper-safe | 1.59 | 1.92 | 2029 |

The default bundle roughly halves the 2030 relative width and pushes the California interpretation boundary from 2028 to 2064; Ohio never crosses within horizon. A reader looking at the 2030 view sees a bounded band (W/M < 0.9); at 2050 the band remains under 1.0 × p50.

## 9. Why the new page is clearer and less misleading

- Single control abstraction: per-parameter radios. No layer vocabulary to learn.
- Every parameter's radio carries only the scientifically defensible levels.
- Figure A never mixes subsystem-share with the main band.
- Figure B ranks the top drivers explicitly — the reader does not have to guess.
- Figure C surfaces the L1 / L2 / L3 summary as explanation only, not as a knob.
- The paper-safe badge flips to "No (exploratory)" the moment any HIGH radio is selected.

## 10. Short answer for a reviewer

"We reject the layer-level low / medium / high scheme because the three L2 dual-axis duplicates (F06–F08, F12–F14) would still double-count variance under any layer-level slider that is not strictly FIXED. Parameter-level control lets those six parameters be FIXED ONLY while the retained per-subsystem axes remain narrowly free. Moreover, inside L3 the trajectory-policy knobs (F23–F27) carry the full LMH vocabulary because they are the only parameters where HIGH is a legitimate exploratory view. No other parameter carries HIGH. The paper-safe ensemble is reproducible via a one-click bundle; the decision-meaningful default reduces 2030 width from 1.64 × p50 to 0.83 × p50 on California (200-run MC, seed 42, final priors)."
