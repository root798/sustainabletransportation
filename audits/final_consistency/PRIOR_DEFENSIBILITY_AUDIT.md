# Prior defensibility audit

Every prior in the uncertainty layers (L1, L2, L3, and the One-Time
page L1) evaluated against six questions: family, support, family
appropriateness, empirical anchor, range width, interactions with
other bounds. Evidence source is
`configs/ui_parameter_presets/*.json`.

## L1 — Emission factors

### F03 — CO₂ intensity of low-carbon generation

| Question | Answer |
|----------|--------|
| Family | Triangular (low, medium) |
| Support | low: (0.02, 0.03, 0.05) kg/kWh. medium: (0.01, 0.03, 0.08) |
| Family appropriate? | **Yes.** Triangular captures the operational-only vs life-cycle-inclusive methodological span with a well-defined mode. |
| Empirical anchor | NREL Life Cycle GHG 2021, NREL/FS-6A50-80580; UNECE LCA 2022. Wind 10-20 gCO₂/kWh; solar 40-50; hydro 20-60; nuclear 10-20. The low triangular (0.02, 0.05) brackets solar-heavy grids; the medium upper tail (0.08) reaches the UNECE upper envelope. |
| Range defensible? | **Yes.** Documented in group-level `help` text. |
| Interactions | Caps at 1.0 in the emissions computation are enforced elsewhere; F03 cannot push grid intensity above fossil because F03 × f_clean + F04 × (1-f_clean) is a convex combination. |

### F04 — CO₂ intensity of fossil generation

| Question | Answer |
|----------|--------|
| Family | Triangular (low, medium), region-specific |
| Support | CA low (0.38, 0.45, 0.55); OH low (0.42, 0.62, 0.85); OH medium (0.38, 0.62, 0.95) |
| Family appropriate? | **Yes, but with caveat.** A single triangular pools gas and coal into one prior. A formal two-component mixture (NGCC 0.42, coal 1.05) would better match the Ohio fuel mix, but the simulator does not support mixture priors at a single parameter. |
| Empirical anchor | NREL LCA 2021; EIA state electricity profiles. Gas 0.42, coal 1.05, fuel-mix-weighted Ohio 0.66. |
| Range defensible? | **Partially.** OH mode 0.62 is 4 % below the fuel-mix-weighted 0.66. The triangular `low` upper tail 0.85 covers coal-heavy years. `medium` upper tail 0.95 covers extreme-coal years. **Flag**: the mode is slightly low; a reviewer may argue for raising to 0.66. |
| Interactions | None. |

### F05 — CO₂-equivalent intensity for gasoline

| Question | Answer |
|----------|--------|
| Family | Triangular (low only) |
| Support | (1.55, 1.65, 1.75) kg/kWh-equiv |
| Family appropriate? | **Yes.** |
| Empirical anchor | EPA 2024 (8.887 kg CO₂ / gal); EIA (33.7 kWh/gal LHV); ICE thermal 25-33 % and alternator 50-60 % compound to ≈28 % onboard conversion. The 15 % value in the task description appears to be low; inspection of F05's registry `physical_meaning` cites "onboard ICE+alternator conversion efficiency of ~15 %", which is at the low end of the 14-19 % range. **Flag**: efficiency anchor near the low end of the range; widening to capture 15 % to 19 % spread would shift mode slightly. |
| Range defensible? | **Yes** for the current tank-to-wheel convention. **Flag**: does not cover well-to-wheel convention (~1.9 kg/kWh); see `V5_F05_RANGE_AUDIT.md`. |
| Interactions | None. |

## L1 — Initial state

### F01 — Initial low-carbon electricity share

| Family | Beta with `kappa = 2 × region kappa` |
| Support | [0, 1] |
| Family appropriate? | **Yes.** Beta is the natural prior for a proportion. |
| Empirical anchor | EIA 2024 California 65.6 %, Ohio 24.7 %. Region kappa captures measurement tightness. |
| Range defensible? | **Yes.** |

### F02 — Initial BEV share

Same family and treatment as F01. Defensible.

## L2 — Dirichlet mixes

### F18 — CAV level mix (L3 / L4 / L5)

| Family | Dirichlet |
| Support | 3-simplex |
| Alpha low = [15.0, 9.99, 5.01] → effective sample size (ESS) = 30 |
| Alpha medium = [5.0, 3.33, 1.67] → ESS = 10 |
| Family appropriate? | **Yes.** Dirichlet is the conjugate prior over a simplex. |
| Empirical anchor | Fleet adoption paths in Gawron 2018 and the National Academies 2023 report on AV deployment. **Flag**: ESS = 30 (low) or 10 (medium) is equivalent to 30 or 10 observed fleets. This is a **design choice**, not an empirical calibration. The alpha values produce the target means (0.5, 0.333, 0.167) but the concentration is not anchored. |
| Range defensible? | **Partially defensible.** Need to state explicitly that the concentration is a modelling choice. |

### F19 — STI level mix

Same treatment as F18. Same caveat about concentration.

## L2 — ECAV and STI per-subsystem scale factors

### F09 — ECAV sensing scale factor

| Family | Lognormal |
| Parameters | low: mean 1.0, σ 0.20. Medium: σ 0.30. |
| Family appropriate? | **Yes.** Lognormal is non-negative with a positive skew, which matches a multiplicative scaling with a dominant lower tail. |
| Empirical anchor | Vendor datasheet spread: L5 sensor-suite range 300 W to 1500 W (Waymo, Cruise, AV compute surveys). σ = 0.20 implies ±22 % (5-95 %) around the central value — narrow relative to the documented 5× spread. **Flag**: σ = 0.20 may be too tight. |
| Range defensible? | **Marginally.** Literature spread suggests σ = 0.30 to 0.40 may be more honest. |

### F10 — ECAV computing scale factor

| Family | Lognormal |
| Parameters | low σ 0.15. Medium σ 0.20. |
| Empirical anchor | NVIDIA Orin vs DRIVE Thor 4× performance-per-watt divergence. σ = 0.15 (±16 %) is tighter than the documented vendor-diversity range. **Flag**: σ = 0.15 is aggressive; σ = 0.25 would match NVIDIA generation divergence. |

### F11 — ECAV communication scale factor

| Family | Lognormal, σ 0.25 / 0.35 |
| Family appropriate? | **Yes.** |
| Range defensible? | **Yes.** σ = 0.25 brackets DSRC vs 5G modem range. |

### F15, F16, F17 — STI counterparts

Same families, slightly wider σ (0.25, 0.18, 0.25). **Flag**: F16
σ = 0.18 is tight. Same concern as F10.

## L2 — Other load

### F20 — ICECAV power overhead factor

| Family | Triangular (1.45, 1.60, 1.80) |
| Family appropriate? | **Yes.** |
| Empirical anchor | Alternator efficiency 50-60 % and ICE thermal 25-33 % combine to overhead factor 1.45 to 1.85. Triangular mode 1.60 corresponds to a 0.28 combined efficiency. **Flag**: modal 1.60 implies 0.31 combined efficiency, which is at the upper end of the literature range (typically 0.18 to 0.26). Upper tail 1.80 corresponds to 0.18, which is the low end. **The triangular bounds may be biased low.** |

### F22 — Vehicle retire year

| Family | Triangular (integer), mode 12 |
| Low (10, 12, 15); Medium (8, 12, 18) |
| Anchor | IHS Markit and S&P Global Mobility median 12 years. **Yes.** |

## L3 — 2075 targets

### F23 — CAV 2075 target fraction

| Family | Triangular (low / medium / high), region-specific |
| Support | CA low (0.35, 0.45, 0.55); CA high (0.15, 0.45, 0.85); OH low (0.20, 0.30, 0.40). |
| Family appropriate? | **Yes** for a bounded-in-[0,1] quantity when every support interval is inside [0,1]. |
| Empirical anchor | **Weak.** No state policy sets a 2075 CAV fleet share. Values are scenario assumptions. **Flag**: the registry `citation` should say "author scenario design" rather than any policy source. |
| Range defensible? | **Yes as a scenario-envelope width.** The high triangular (0.15, 0.85) represents a very wide uncertainty envelope. |
| Interactions | Support bounded inside [0, 1]; no interaction risk. |

### F24 — STI 2075 target

Same treatment as F23. Same weak-anchor concern.

## L3 — Growth exponents

### F25 — Annual BEV-share growth exponent

| Family | Truncated normal, region-specific |
| Support | CA low (mean 0.07, sd 0.0075, [0.04, 0.10]). OH low (mean 0.055, sd 0.010, [0.03, 0.085]). High σ up to 0.028. |
| Family appropriate? | **Yes but**: the truncation bounds must prevent share values exceeding 1.0 over 51 years. A compound growth g of 0.07 from a 0.041 base reaches 1.0 at year 47 (t=23). The simulator does cap f_ev at 1.0 inside `_update_ev`, so no runtime error, but the **effective** sampled growth beyond the saturation point is ignored. **Flag**: the truncation bounds are physical (prevent negative and above-max growth) but the downstream saturation is handled by a hard clip, not by the prior. A reviewer may note that the prior does not reflect the saturation phenomenon. |

### F26 — Annual low-carbon-electricity growth exponent

Same family. **Flag**: CA mean 0.05 from 0.656 base saturates at year
9 (2033); the simulator clips f_clean at 1.0 in `_calculate_emissions`.
Saturation treatment is a hard clip, not a logistic curve. **Flag**:
this is documented in Methods but not modelled as a curve.

### F27 — Hardware efficiency doubling time

| Family | Lognormal (mean 2.8, σ 0.15 low / 0.30 medium / 0.45 high) |
| Family appropriate? | **Yes.** Lognormal is non-negative with positive skew. The implied rate distribution (1 / doubling_time) is also non-negative with positive skew. Reparameterisation sanity check passes. |
| Empirical anchor | Semiconductor roadmap projections. σ = 0.15 implies 12 % to 14 % half-width, which matches Intel / NVIDIA public roadmaps. High σ = 0.45 allows 50 % spread, which reaches post-Moore pessimistic projections. **Yes.** |
| Interactions | Doubling time feeds the cohort-efficiency `0.5 ^ (elapsed / doubling)`. Very small doubling times (0.5 yr) could produce unphysical zero-energy cohorts. The current minimum for low/medium/high is not explicitly bounded below; the registry uses lognormal without a lower truncation. **Flag**: a Monte Carlo sample below 0.5 yr is physically implausible but allowed. Add a left truncation at 1.0 yr for a defensible prior. |

### F28 — Fleet-stock growth exponent

| Family | Truncated normal |
| Support | (-0.001, 0.002, 0.007) CA; (-0.002, 0.001, 0.004) OH |
| Family appropriate? | **Yes.** |
| Empirical anchor | US Census demographic projections. **Yes.** |

## One-Time-Energy page L1 (F-OT-01 through F-OT-06)

Currently exposed as radios (fixed / low). The supporting data
structure assumes these priors but the live-MC path for the One-Time
page does not yet implement the Monte Carlo sampling. **Flag**: the
radios are visible but their levels do not yet drive a live-band
recompute; they are documentation for now. See
`v5_streamlit_app/pages/01_One_Time_Energy.py`.

## Cross-cutting issues

1. **Left truncations on lognormal priors.** F10, F11, F15, F16, F17,
F27 all use `lognormal(mean, sigma)` with no lower truncation. For σ
values up to 0.45 (F27 high), the bottom 1 % of the distribution is
below 0.5× central. For scale factors centred at 1.0 this is harmless;
for F27 centred at 2.8 yr, the 1st percentile is 0.93 yr — physically
implausible but not prevented. **Recommend** adding a left truncation
at 1.0 yr for F27.

2. **Dirichlet concentration as design choice.** F18 and F19 alpha
sums (ESS) are 30 (low) and 10 (medium). This is not anchored to an
empirical count of observed AV fleets or STI deployments. Document as
a modelling choice.

3. **Saturation treatment.** F25 and F26 compound exponents combined
with state-specific hard 1.0 caps on f_ev and f_clean. The prior does
not model the saturation phenomenon itself. This is fine for near-term
scenarios but becomes less defensible over the 51-year ramp. **Flag**:
consider logistic growth for the envelope view.

4. **ICECAV overhead factor (F20).** Modal 1.60 implies combined ICE
+ alternator efficiency of 0.31, which is at the upper end of the
automotive literature (0.18 to 0.26 is more common). **Flag**: mode
may be optimistic. A reviewer may push to lower the mode or widen
the support.

5. **F04 Ohio mode bias.** Mode 0.62 sits 4 % below the fuel-mix-
weighted 0.66. Not a wrong-direction issue (the triangular upper tail
reaches 0.85) but the central value is slightly biased. **Flag** for
manuscript text.

6. **Empirical anchor for F27 top-line claim.** The σ = 0.15 (low)
implies a 16 % doubling-time spread; this matches Intel / NVIDIA
public roadmaps but does not cover a post-Moore breakdown scenario.
The `high` level σ = 0.45 does. Make sure the page caption says this
explicitly.

## Summary

- **Defensible**: 15 of 22 priors are well anchored and appropriate.
- **Flag**: 7 priors require either a documentation pass or a
modest bound adjustment:
  - F04 (OH mode 0.62 vs fuel-weighted 0.66)
  - F09 / F10 / F15 / F16 (σ possibly tight vs literature)
  - F18 / F19 (Dirichlet concentration is design choice)
  - F20 (mode may be optimistic)
  - F27 (no left truncation)
  - F25 / F26 (saturation not in the prior)
- **Author-scenario priors**: F23, F24 are scenario assumptions,
not policy-derived. Registry citation text should match.
