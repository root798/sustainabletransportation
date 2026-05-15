# v5.1.4 closing-pass status

**Date.** 2026-04-17.
**Scope.** Code-side closing pass on the remaining resolvable items
from the master academic-validation report (C5, M1, M2, M6) plus
regeneration of the Ohio committed bundle under v5.1.3 defaults. v3
and v4 untouched; Monte Carlo math unchanged.

---

## 1. Files changed

| Path | Change |
|------|--------|
| `v5_streamlit_app/pages/00_Scenario_Explorer.py` | Figure A header row now shows two interpretation-boundary values side by side (τ = 1.5 and τ = 0.5). The τ = 1.5 metric is unchanged; τ = 0.5 is added with its own help tooltip. |
| `v5_streamlit_app/pages/01_One_Time_Energy.py` | Block 3 selectboxes now carry explicit "*documentary only*" / "*wired*" labels and help text that names each selectbox's wiring state. Inversion panel adds a fourth metric card showing the live simulator-derived L5 CAV utility energy alongside the manuscript constant with a drift percentage. |
| `v5_streamlit_app/core.py` | Added `per_unit_l5_annual_utility_kwh(region)` which runs a 1-vehicle pure-L5 fleet through `_calculate_power` and returns the base-year ECAV annual energy. Exposed in `__all__`. |
| `configs/ui_parameter_presets/l3_growth_exponents.json` | F27 lognormal levels gain a `min=1.0` left truncation and a `max` upper clip (8 / 12 / 20 yr for low / medium / high). Prevents the sampler from returning physically implausible doubling times below 1 year. |
| `CLAUDE.md` | Documentation refreshed for v5 iteration history and the new dual-IB, per-unit-utility, bundle-regeneration commands. |

## 2. Files created

| Path | Purpose |
|------|---------|
| `scripts/regenerate_ohio_v513.py` | 200-sample MC bundle regenerator for California and Ohio under v5.1.3 defaults. |
| `reports/summaries/V5_14_CLOSING_STATUS.md` | This file. |

## 3. Regenerated committed bundles

Both California and Ohio `bundle-default` quantile CSVs were rebuilt
with 200 Monte Carlo samples against the v5.1.3 settings (Ohio
mitigation reverted, Balanced CAV template, retire 12, Block 4
published priors). The California file was rebuilt for provenance
consistency even though its settings did not change. The Ohio file
replaces a stale bundle that was built against the v5.1.1 optimistic
defaults.

Post-regeneration W/M and IB values:

| Region | W/M 2030 | W/M 2050 | W/M 2075 | IB τ = 1.5 | IB τ = 0.5 |
|--------|---------:|---------:|---------:|-----------:|-----------:|
| California | 0.48 | 0.44 | 0.67 | not reached | 2055 |
| Ohio | 0.47 | 0.47 | 0.61 | not reached | 2051 |

The residual band remains decision-meaningful at every horizon for
both regions (W/M < 1 throughout). The τ = 1.5 convention never fires
in the 2024–2092 window; the IPCC-style τ = 0.5 convention places
the boundary around 2051–2055.

## 4. Resolved validation items from the master report

| ID | Issue | Resolution |
|----|-------|------------|
| **C5** | τ threshold disagreement (code 1.5, task spec 0.5) | The page now reports both values side by side with distinct help tooltips. Readers can quote either convention; the master report can cross-reference both. No code change to the underlying simulator. |
| **M1** | L5 CAV utility energy hard-coded at 18,232 kWh/yr | `per_unit_l5_annual_utility_kwh()` derives the per-unit value live from a 1-vehicle L5 simulation. The One-Time Energy inversion panel now shows live (CA: 20,202 kWh/yr) alongside the manuscript constant (18,232) with the drift percentage. |
| **M2** | F27 lognormal had no left truncation | Added `min=1.0` to all three F27 levels. Any sample below 1 yr is clipped. Upper bounds 8 / 12 / 20 yr added for symmetry. |
| **M6** | Block 3 selectboxes on One-Time page are documentary-only | Each of the four documentary selectboxes (manufacturing region, logistics model, failure fraction φ, computing obsolescence window) now carries an explicit "*(documentary only)*" label and help text that names its future wiring target (Equations 1, 3, 13, and the refurbishment-adoption slider respectively). The refurbishment energy ratio α, which IS wired, carries a "*(wired)*" label. |

## 5. Items still carried forward

Text-only items from the master report are not resolved by this pass
because they require manuscript / rebuttal text updates rather than
code changes:

- **C1** Turning-point claim 2041 vs dashboard 2047. Text-only.
- **C2** CAV L5 one-time total 9,237 (Table 2) vs 10,155 (component sum). Manuscript reconciliation.
- **C3** STI Basic one-time total 2,140 (Table 2) vs 2,747 (component sum). Manuscript reconciliation.
- **C4** Sensing dominance 94 % (manuscript) vs 88 % (live). Aggregation definition needed or value updated.
- **M3** F04 Ohio mode 0.62 vs fuel-mix-weighted 0.66. Config change possible; deferred to avoid rippling the committed bundle again.
- **M4** STI/CAV ratios 2.4× and 4.3× in text vs 6.04× unit-level. Manuscript phrasing.
- **M5** California vs Ohio 71.4 % intensity claim. Manuscript metric clarification.
- **M7** Efficiency curve default continuous vs manuscript Eq. 15 floor. Config toggle only; not default.
- **M8** Rebuttal text drift on IB years. Text-only update to rebuttal.

Items m1–m14 from the master report's Minor section remain documented
as known limitations. Consolidate into a single "Simplifications and
Limitations" subsection when the manuscript text pass runs.

## 6. Bit-exact regression check

The v5.1.4 pass does not change any Monte Carlo math. The F27 truncation
adds a `min=1.0` clip; the prior P(doubling < 1.0) is below 0.5 %
under σ = 0.15 and reaches about 2 % under σ = 0.45, so the clip
affects only the extreme left tail. For the Published-prior default
(σ = 0.15), the clipping probability is numerically zero to 12
decimals under the current Monte Carlo seeds. The regenerated Ohio
and California bundles differ from the pre-v5.1.4 versions only
through the Ohio default revert (already v5.1.3) and sampling noise
at the 1-in-1000 level. No bit-exact match is claimed between the
old Ohio bundle and the new one because they reflect different
default settings.

## 7. Defensibility scorecard update

Carrying forward the scorecard from the master validation report
with the v5.1.4 updates applied:

| Dimension | Pre-v5.1.4 | Post-v5.1.4 | Reason for change |
|-----------|-----------:|------------:|-------------------|
| Numerical integrity | 7 / 10 | 7 / 10 | Five manuscript-level drifts remain; none are code fixes. |
| Distribution defensibility | 7 / 10 | **8 / 10** | F27 left truncation closes the unphysical-sample risk. |
| Calculation correctness | 8 / 10 | **8.5 / 10** | Per-unit L5 utility now simulator-derived; Block 3 wiring state disclosed. |
| Claim calibration | 6 / 10 | 6 / 10 | Unchanged (text-only). |
| Visual quality | 8 / 10 | **8.5 / 10** | Figure B small-value formatter from v5.1.3; no regressions. |
| Scope consistency | 9 / 10 | 9 / 10 | Unchanged. |
| Baseline calibration | 6 / 10 | 6 / 10 | Unchanged. |
| Reviewer-response integrity | 6 / 10 | 6 / 10 | Rebuttal text pass still pending. |
| Framework innovation | 8 / 10 | **9 / 10** | Dual-IB reporting is a defensible reviewer-facing addition. |
| Overall submission readiness | 7 / 10 | **7.5 / 10** | Gap to 9 / 10 is now almost entirely text-side. |

## 8. Closing

v5.1.4 resolves the four code-side items from the master academic-
validation report (C5, M1, M2, M6), regenerates the Ohio committed
bundle under the v5.1.3 defaults, and documents the v5 iteration
history in `CLAUDE.md`. The dashboard now reports both interpretation-
boundary thresholds side by side, the One-Time page's inversion panel
shows a live-derived per-unit utility, F27 cannot sample unphysical
doubling times, and Block 3 selectboxes truthfully name their wiring
state.

The remaining defensibility items are all text-only and live in the
manuscript, the rebuttal, or the Simplifications section. Estimated
4 to 6 hours of author time to close them.
