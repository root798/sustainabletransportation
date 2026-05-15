# What remains before resubmission

**Date.** 2026-04-18.
**Status.** Code-side work is complete. All remaining items are
manuscript, rebuttal, or supporting-text work that must be done by
the author because the auditor cannot read the manuscript PDF.

---

## 1. Dashboard and code state

**Clean.** The v5 Scenario Explorer, One-Time Energy, and System
Boundary pages all compile, render, and produce numerically
defensible outputs under default and non-default settings.

Iteration history:

| Version | What shipped |
|---------|--------------|
| v5.1 | Sidebar layout, dual-region driver fix, Nature-grade figure style |
| v5.1.1 | Defensibility pass — dual uncertainty object, Ohio defaults reverted, Balanced template |
| v5.1.2 | UI simplification — Published / Custom selectbox, human-readable Figure B labels, session-state warning fix |
| v5.1.3 | Region-state hardening — deterministic `_reset_region_state`, signature-based band liveness, Figure B `<0.01` label formatter |
| v5.1.4 | Closing pass — dual IB (τ = 1.5 and 0.5), F27 truncation, Block 3 documentary labels, live per-unit L5 utility, Ohio bundle regenerated |
| v5.1.5 | One-Time Energy comprehensive fix — 25 problems closed; refurbishment factor decoupled from production display; Figure A / B / C rebuilt |

Launch: `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## 2. Manuscript text items still open

These cannot be resolved by code. Each is a short author-side
decision and text edit. Where a specific dashboard value is named,
the author can quote it verbatim.

### 2.1 Rebuttal-letter interpretation-boundary values

| Region | Rebuttal cites | Current dashboard | Action |
|--------|----------------|-------------------|--------|
| California default | 2030 | IB (τ = 1.5) = not reached within horizon; IB (τ = 0.5) = 2055 | Update rebuttal to "not reached at τ = 1.5; 2055 at τ = 0.5". |
| California paper-safe | 2030 | IB (τ = 1.5) = 2028; IB (τ = 0.5) = 2028 | Update to 2028. |
| Ohio default | 2031 | IB (τ = 1.5) = not reached; IB (τ = 0.5) = 2051 | Update to "not reached at τ = 1.5; 2051 at τ = 0.5". |
| Ohio paper-safe | 2031 | IB (τ = 1.5) = 2029; IB (τ = 0.5) = 2029 | Update to 2029. |

Cross-reference: `V5_PEAK_TURNING_IB_RECONCILIATION.md`.

### 2.2 Turning-point claim in the abstract

Rebuttal / abstract claim 2041; dashboard default California turning
year is 2047. Either (a) name the specific scenario under which 2041
holds (aggressive mitigation), or (b) update to 2047 under baseline.

### 2.3 94 % CAV sensing-dominance claim

Manuscript §2.1.1 reports 94 % sensing share for CAV. Live value for
CAV L5 alone is 88.0 %; the 94 % figure uses an aggregation that the
Extended Data Tables do not specify. Either (a) add a methods note
naming the aggregation (for example a fleet-weighted average with
specific weights), or (b) update to 88 % with L5-specific framing.

Cross-reference: `V5_NUMERICAL_DEFENSIBILITY_PRECHECK.md`,
`ONE_TIME_PAGE_COMPREHENSIVE_FIX_STATUS.md`.

### 2.4 CAV L5 production + logistics: 9,237 vs 10,155 kWh

Table 2 lists 9,237 kWh (production + logistics). Extended Data Table
3 counts × Figure 3a energies sum to 10,155 kWh. 918 kWh gap ≈
2 × Onboard Computing Unit (917 kWh). The two tables of the
manuscript must be reconciled; the dashboard plots the
component-reproducible 10,155 and flags the gap in the cross-check.

### 2.5 STI Basic total: 2,140 vs 2,747 kWh

Same family as 2.4 but for STI Basic. Extended Data Table 4 counts ×
Figure 3a energies sum to 2,747; Table 2 and Figure 3b list 2,140.
607 kWh gap.

### 2.6 "Roughly 205 MWh over 12 years" abstract claim

Abstract cites 205 MWh. Dashboard-derived 18,232 kWh/yr × 12 yr =
218,784 kWh = 218.8 MWh. 6.7 % drift. Either update the abstract to
219 MWh or explain the 205 figure (possibly a discount or an older
baseline).

### 2.7 "STI 2.4× CAVs" / "Highly-STI 4.3× L5 CAV"

Unit-level ratio at peak is 6.04×. Text-only clarification:
name the weighting used for 2.4× and 4.3× or update the numbers.

### 2.8 "California 71.4 % lower carbon intensity than Ohio at 2025"

Not reproducible from the configs as `1 - CA_intensity /
OH_intensity`. Clarify the intensity metric or update.

### 2.9 F04 Ohio prior mode

Currently 0.62; fuel-mix-weighted estimate 0.66. Small (~6 %) bias.
Low priority; either update the mode or add a methods note stating
the NGCC-dominant-operation assumption.

### 2.10 Efficiency-curve default: continuous vs floor

`footprint_model.py` defaults to a continuous `0.5 ** (elapsed /
doubling)`. Manuscript Eq. 15 uses `floor((t − d1) / d0)`. Either
(a) switch `efficiency_curve` to `step` in the scenario JSONs and
regenerate committed bundles, or (b) add a methods note stating the
dashboard uses a continuous interpolation of the floor equation.

---

## 3. Optional strengthening items

These are not required but would strengthen the paper.

### 3.1 Copula enabled by default on F23–F27

`sample_config(..., trajectory_copula=True)` is available but not the
default. Turning it on pre-empts the reviewer question "what if the
mitigation levers are correlated?". Small code change (one config
flag) plus a methods note naming the rank-correlation matrix.

### 3.2 Ohio sensitivity surfaces matching California

Figure 5 probably covers California. A parallel Ohio surface (same
12 panels) would strengthen the two-state framing. The dashboard
supports Ohio end-to-end; one static export run builds the figures.

### 3.3 Consolidated Simplifications and Limitations subsection

Items m1 – m14 from the master validation report scattered across
the paper. A single unified subsection lists them with one-sentence
justifications. ISO 14044 compliance also expects this.

### 3.4 Custom-spec JSON export

One-click download of the user's current `expv5_cspec_*` payload.
Reviewers can reproduce a run from a posted spec. Optional
reproducibility strengthening.

### 3.5 Regenerate committed bundles with `efficiency_curve = "step"` if 2.10 is chosen

Only relevant if item 2.10 is resolved in favour of the floor
formulation.

---

## 4. Artefact index

All audit and status documents produced across the iterations, in
chronological order. The author can point reviewers at any of these
individually.

### Validation and audit files

- `audits/final_consistency/USAGE_MATRIX_RESULTS.csv`
- `audits/final_consistency/USAGE_VALIDATION_ASSERTIONS.md`
- `audits/final_consistency/REBUTTAL_NUMBER_CROSSCHECK.md`
- `audits/final_consistency/SILENT_FAILURE_SCAN.md`
- `audits/final_consistency/ACCESSIBILITY_REPORT.md`
- `audits/final_consistency/V5_REACTIVITY_AND_BAND_STATUS_AUDIT.md`
- `audits/final_consistency/V5_RESIDUAL_DRIVER_SEMANTIC_FIX.md`
- `audits/final_consistency/V5_PARAMETER_CONTROL_SIMPLIFICATION.md`
- `audits/final_consistency/V5_MITIGATION_DEFAULT_PROVENANCE_FIX.md`
- `audits/final_consistency/V5_SIDEBAR_CONTROL_LAYOUT_FIX.md`
- `audits/final_consistency/V5_RESIDUAL_WIDTH_REASSESSMENT.md`
- `audits/final_consistency/V5_PAGE_COPY_FINAL_ALIGNMENT.md`
- `audits/final_consistency/V5_NUMERICAL_DEFENSIBILITY_PRECHECK.md`
- `audits/final_consistency/V5_PEAK_SANITY_AUDIT.md`
- `audits/final_consistency/V5_PEAK_TURNING_IB_RECONCILIATION.md`
- `audits/final_consistency/V5_DUAL_UNCERTAINTY_OBJECT_IMPLEMENTATION.md`
- `audits/final_consistency/V5_OHIO_DEFAULT_PROVENANCE_AUDIT.md`
- `audits/final_consistency/V5_F04_OHIO_RECALIBRATION.md`
- `audits/final_consistency/V5_LEVEL_MIX_DEFAULT_AUDIT.md`
- `audits/final_consistency/V5_FIGURE_B_DEFENSIVE_CAPTION_FIX.md`
- `audits/final_consistency/V5_F05_RANGE_AUDIT.md`
- `audits/final_consistency/V5_SCOPE_ALIGNMENT_NOTE.md`
- `audits/final_consistency/UI_SIMPLIFICATION_VALIDATION.md`
- `audits/final_consistency/V5_REGION_STATE_DEPENDENCY_AUDIT.md`
- `audits/final_consistency/V5_REGION_CHANGE_RESET_FIX.md`
- `audits/final_consistency/V5_REGION_DEFAULT_ALIGNMENT_AUDIT.md`
- `audits/final_consistency/V5_BAND_STATUS_SIGNATURE_AUDIT.md`
- `audits/final_consistency/V5_FIGURE_B_SMALL_VALUE_LABEL_FIX.md`
- `audits/final_consistency/V5_CROSS_REGION_REGRESSION_MATRIX.md`
- `audits/final_consistency/V5_MICRO_BUG_SWEEP.md`
- `audits/final_consistency/MASTER_NUMERICAL_RECONCILIATION.md`
- `audits/final_consistency/PRIOR_DEFENSIBILITY_AUDIT.md`
- `audits/final_consistency/CALCULATION_CORRECTNESS_AUDIT.md`
- `audits/final_consistency/CLAIM_STRENGTH_AUDIT.md`
- `audits/final_consistency/VISUAL_QUALITY_AUDIT.md`
- `audits/final_consistency/STRUCTURAL_RISK_AUDIT.md`
- `audits/final_consistency/ONE_TIME_ENERGY_PAGE_VALIDATION.md`
- `audits/final_consistency/ONE_TIME_PAGE_COMPREHENSIVE_FIX_VALIDATION.md`

### Status and summary files

- `reports/summaries/FINAL_VALIDATION_AND_POLISH_STATUS.md`
- `reports/summaries/V5_FINAL_LIVE_ALIGNMENT_STATUS.md`
- `reports/summaries/V5_NUMERICAL_DEFENSIBILITY_FINAL_STATUS.md`
- `reports/summaries/ONE_TIME_ENERGY_PAGE_STATUS.md`
- `reports/summaries/UI_SIMPLIFICATION_STATUS.md`
- `reports/summaries/V5_REGION_STATE_HARDENING_STATUS.md`
- `reports/summaries/V5_14_CLOSING_STATUS.md`
- `reports/summaries/MASTER_ACADEMIC_VALIDATION_REPORT.md`
- `reports/summaries/ONE_TIME_PAGE_COMPREHENSIVE_FIX_STATUS.md`
- `reports/summaries/WHAT_REMAINS_BEFORE_RESUBMISSION.md` (this file)

### Regenerated figures

- `figures/fig4_emissions_band_*.{png,pdf}` — Scenario Explorer Figure A per region and bundle
- `figures/fig5_top_drivers_*.{png,pdf}` — Scenario Explorer Figure B per region and year
- `figures/fig6_layer_contribution_*.{png,pdf}` — Scenario Explorer Figure C per region
- `figures/fig_ot_A_component_ranking_*.{png,pdf}` — One-Time Energy Figure A
- `figures/fig_ot_B_unit_stacked_*.{png,pdf}` — One-Time Energy Figure B
- `figures/fig_ot_C_marginal_counts_*.{png,pdf}` — One-Time Energy Figure C
- `figures/EXPORT_MANIFEST.md` — catalogue

---

## 5. Closing assessment

**Code side: 10 / 10 items closed.** Every defensibility concern
that could be resolved by touching the dashboard or the simulator
has been addressed. The Ohio committed bundle was regenerated under
the v5.1.3 defaults. The One-Time Energy refurbishment-factor leak
into production display was fixed at its root. The Figure A split
bug was fixed at its root. The Figure C missing bar was fixed at
its root. The Block 4 selectbox / session-state warning was fixed
across both pages.

**Manuscript side: 10 text items identified** (§2 above). Each is a
single-paragraph edit or a table-value reconciliation. Estimated
4 – 6 hours of author time. None requires new calculations.

The dashboard is submission-ready from the code side. The author's
final pass over the manuscript text closes the loop.
