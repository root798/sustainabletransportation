# PARAMETER_LEVEL_UNCERTAINTY_JUSTIFICATION.md

**Purpose:** support material for a reviewer or reader question: "why did you move to parameter-level uncertainty control instead of keeping the layer-level low/medium/high scheme?"

**Primary sources:**
- `audits/uncertainty_governance/PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.md`
- `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.md`
- `audits/uncertainty_governance/DEFAULT_FIXED_PARAMETER_JUSTIFICATION.md`

---

## 1. What layer-level control could not express

Layer-level presets lump physically unlike parameters onto one knob. Concretely, under a single "L2 low / medium / high" selector the reader could not:

1. **Tighten F06–F08 (per-level scale factors) while keeping F09–F11 (per-subsystem) at evidence-anchored MEDIUM** — yet this is the principled response to dossier S2-01: remove the duplicated axis, keep the retained axis. The layer-level scheme has to either widen all six together or narrow all six together.
2. **Fix F21 (cohort decay) — whose variance is invisible after 2036 — without also fixing F18 and F19 (Dirichlet mixes), which are substantial 2030 contributors.** The previous L2-low preset did exactly this coarse grouping.
3. **Narrow F25 (EV growth exponent) independently of F23 (CAV 2075 target).** These are physically different scenario knobs: F25 is a compounding exponent, F23 is a linear-ramp endpoint. A reader interrogating "what if the 2075 CAV target is less aggressive?" should be able to do so without simultaneously rewriting the BEV growth trajectory.

Each of these is a concrete scientific request that layer-level presets could not cleanly answer.

## 2. What parameter-level control does express

Every ordinary-MC parameter gets its own radio with a scientifically-chosen allowed set of levels:

- **`{fixed, medium}`** for duplicates (F06–F08, F12–F14) and irrelevant-after-2036 (F21). LOW is undefined because narrowing is meaningless; HIGH is undefined because widening is unsupported.
- **`{fixed, low, medium}`** for evidence-anchored parameters (L1 emission factors, L2 per-subsystem, Dirichlets, icecav, retire_year, F28). HIGH not offered — widening beyond MEDIUM is not defensible.
- **`{fixed, low, medium, high}`** for trajectory-policy knobs (F23, F24, F25, F26, F27). HIGH explicitly marked exploratory.

## 3. Quantitative evidence for the change

From the parameter-level contribution experiment (see `PARAMETER_CONTRIBUTION_EXPERIMENT.csv`):

- **F27 (efficiency doubling time) has the largest turning-year spread** at 16 years. Under layer-level L3 low/medium/high, this parameter's 16-year turning-year sensitivity was hidden inside the L3 bundle. Parameter-level control surfaces it as a specific driver the reader should see.
- **F18 (cav_levels Dirichlet) contributes 0.55 × p50 to the 2030 band** — larger than F06–F08 per-level ECAV axis (0.35). The old L2-low preset bundled both, so the reader could not narrow F18 independently.
- **F02 (initial BEV share) is absorbed by F25** within 3–5 years, but the old L1-low preset bundled it with F03 (e_clean) — a genuine methodological choice that should remain visible.

## 4. The parameter-level default is decision-meaningful

Applying `default_level` per parameter gives:

- 9 parameters fixed (F01, F02, F06, F07, F08, F12, F13, F14, F21).
- 19 parameters free at LOW (F03, F04, F05, F09–F11, F15–F20, F22–F28).
- No parameter at MEDIUM or HIGH under the default.
- Paper-safe-reproduction (MEDIUM everywhere) is one click away.

This default fixes the evidence-absorbed and the dossier-duplicated parameters, and narrows the remaining free parameters to LOW. Expected outcome: 2030 band width well under 1.0 × p50 on California, interpretation boundary pushed past 2035. Paper-safe bundle remains available for reproduction.

## 5. What parameter drives uncertainty most

Combined ranking from the parameter-level experiment (rank-sum across 2030 W/M, 2050 W/M, and turning-year spread):

1. **F27** `efficiency_doubling` — top 2050, top turning-year driver.
2. **F23** `growth_rates.cav` — top 2030, second turning-year.
3. **F18** `cav_levels` — top 2030, third turning-year.
4. **F06/F07/F08** `ecav_scale_factors.{L3,L4,L5}` — S2-01 duplicate; fixed by default.
5. **F25 / F26** `growth_rates.ev` / `clean_energy` — long-horizon drivers.

Parameter-level control lets the reader narrow exactly these, not their layer cohort.

## 6. What layer drives uncertainty most

From the layer-level experiment (`LAYER_CONTRIBUTION_EXPERIMENT.csv`):

- **L2 dominates 2030** (W/M ~1.10–1.27).
- **L3 dominates 2050 and 2075** (W/M 1.46 at 2050 on California).
- **L1 is the smallest contributor everywhere.**

This is retained as a **summary** (Figure C), not as a control.

## 7. Why the new uncertainty page is easier to interpret

Three reasons:

1. **Single control abstraction.** Every parameter has one radio. No more learning three different preset vocabularies per layer.
2. **Fixed-vs-free visibility is direct.** The reader reads the radio state; they don't have to mentally unpack what an `l2_low` preset does to F06, F09, F15, F18, etc.
3. **Figures B and C are purely diagnostic.** The primary control is the radios; the contribution figures *interpret* the choices rather than re-litigating them.

## 8. What remains scientifically honest

- The paper-safe reproduction bundle still reproduces the committed `_quantiles.csv` numbers.
- Fixed-by-default factors either (a) duplicate uncertainty elsewhere or (b) are absorbed after a few simulated years. None of them represent hidden scenario disagreement.
- Structural shocks remain on their own panel; never merged.
- F29 (missing absolute power cells) is explicitly disclosed as an underconstrained gap, not hidden.
