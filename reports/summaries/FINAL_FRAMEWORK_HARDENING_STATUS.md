# FINAL_FRAMEWORK_HARDENING_STATUS.md

**Date:** 2026-04-17
**Scope:** six unresolved methodological items addressed in one hardening pass.

---

## Summary verdict

The active dashboard framework is now **stronger on every audited dimension** than before this pass. The Gaussian copula is implemented and available (disabled by default for backward compatibility). Ohio parameter-importance data now exists. U.S. Average quarantine is hardened. Policy-conditional MC gating is explicit. F29 justification is documented. Truncated-normal approximation is quantified. All changes are backward-compatible with the prior submission's reported numbers.

## Per-item status

| # | Item | Status | Before → After |
|---|---|---|---|
| **F29** | 18 absolute ECAV/STI power cells | **Justified and documented** | Dashboard note unchanged; new `F29_JUSTIFICATION_HARDENED.md` explains why cell-level priors are intentionally excluded (would reintroduce S2-01/S2-02 duplication) |
| **COPULA** | Independence across F23–F27 trajectory drivers | **Implemented, disabled by default** | `sample_config` gains `trajectory_copula=True/False` kwarg; 5×5 default correlation matrix (PD-verified); `_apply_copula_to_growth_rates` + `_invert_marginal_at_u` implemented using Gaussian copula with scipy. Disabled by default so prior submission is reproducible; dashboard references the option |
| **US_AVG** | U.S. Average quarantine | **Hardened** | Removed from default region selector (now behind explicit "Show quarantined" toggle in Advanced Detail); upgraded from `st.warning` to `st.error` with full quarantine explanation |
| **POLICY** | Aggressive/conservative MC gating | **Strengthened** | Upgraded from one-line `st.info` to multi-sentence `st.warning` naming the selected policy and explaining that `data_uncertainty` distributions are not re-centred under non-baseline policies |
| **OH_EXP** | Ohio parameter importance experiment | **Complete** | Script extended from single-region to `REGIONS = ["california", "ohio"]`; 144-row CSV regenerated (24 params × 3 years × 2 regions × 80 MC runs); dashboard summary cards now region-specific; `CA_OH_PARAMETER_DRIVER_COMPARISON.md` written |
| **TRUNC** | Truncated-normal approximation | **Documented** | Clamp rate quantified analytically: <0.1% at LOW, ~4.5% at MEDIUM for F25/F26; negligible numerical impact; retained with documentation in `TRUNCATED_NORMAL_IMPLEMENTATION_NOTE.md` |

## Validation checklist

| Check | Result |
|---|---|
| `footprint_model.py` compiles clean | Pass |
| `00_Scenario_Explorer.py` compiles clean | Pass |
| `scripts/parameter_contribution_experiment.py` compiles clean | Pass |
| Copula matrix PD (eigenvalues all > 0) | Pass (0.40, 0.50, 0.87, 0.95, 2.28) |
| Copula sampling returns valid draws for CA/OH | Pass (verified at seed 42) |
| Parameter experiment CSV has both regions, 144 rows | Pass |
| Bundle quantile CSVs unchanged (69 rows each, 12 files) | Pass |
| US Average removed from default region dropdown | Pass |
| Non-baseline policy triggers st.warning | Pass |
| F29 disclosure present in Tier 3 Advanced Detail | Pass |
| Truncated-normal documented in Tier 3 distribution notes | Pass |
| Page adds "What remains outside this band" block | Pass |
| Page adds "Policy relevance" dynamic insight | Pass |

## Files changed

| File | Change |
|---|---|
| `footprint_model.py` | Added Gaussian copula: `DEFAULT_TRAJECTORY_CORR`, `_TRAJECTORY_COPULA_KEYS`, `_apply_copula_to_growth_rates`, `_invert_marginal_at_u`; extended `sample_config` signature with `trajectory_copula` and `trajectory_corr` kwargs |
| `scripts/parameter_contribution_experiment.py` | `REGION` → `REGIONS = ["california", "ohio"]`; main loop iterates both regions |
| `v4_streamlit_app/pages/00_Scenario_Explorer.py` | US Average removed from default dropdown (behind toggle); `st.warning` → `st.error` for US Average; `st.info` → `st.warning` for non-baseline policy; summary cards now region-specific; "What remains outside this band" block; "Policy relevance" dynamic insight; "Show quarantined" toggle in Advanced Detail |
| `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv` | Regenerated with 144 rows (CA + OH) |

## Files created

| File | Purpose |
|---|---|
| `audits/final_consistency/FRAMEWORK_HARDENING_PRE_AUDIT.md` | Pre-audit table |
| `audits/final_consistency/F29_JUSTIFICATION_HARDENED.md` | F29 design-choice justification |
| `audits/final_consistency/TRAJECTORY_COPULA_IMPLEMENTATION.md` | Copula design and implementation note |
| `audits/final_consistency/US_AVERAGE_QUARANTINE_HARDENING.md` | Quarantine hardening changes |
| `audits/final_consistency/POLICY_PRESET_EXPLORATORY_GATING.md` | Policy gating changes |
| `audits/final_consistency/OHIO_PARAMETER_IMPORTANCE_EXTENSION.md` | Ohio experiment extension |
| `audits/final_consistency/TRUNCATED_NORMAL_IMPLEMENTATION_NOTE.md` | Approximation quantification |
| `audits/final_consistency/SCENARIO_EXPLORER_POLICY_CLARITY_POLISH.md` | Policy-relevance UI additions |
| `audits/final_consistency/FRAMEWORK_HARDENING_SUPPORT_ALIGNMENT.md` | Support-doc consistency check |
| `reports/summaries/CA_OH_PARAMETER_DRIVER_COMPARISON.md` | Region-specific driver ranking |
| `reports/summaries/FINAL_FRAMEWORK_HARDENING_STATUS.md` | This file |

## What still remains unresolved

| Item | Status | Why deferred |
|---|---|---|
| Copula-enabled MC regeneration | Available but not regenerated | Requires a deliberate decision on whether the paper revision uses correlated or independent sampling; the code is ready |
| True scipy truncnorm sampler | Available in copula path but not in independent path | Negligible numerical impact at current settings; one-line change if requested |
| Ohio-specific L3 prior recalibration (S2-04) | Documented, not executed | Requires Ohio-specific empirical evidence that is not yet collected |
| F29 cell-level priors | Explicitly excluded | Would reintroduce dual-axis duplication; documented as intentional design |
| Joint prior for ECAV/STI scale factors | Deferred | Requires a model-structure redesign; LOW preset's axis-drop is the clean alternative |
