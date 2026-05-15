# FRAMEWORK_HARDENING_SUPPORT_ALIGNMENT.md

**Date:** 2026-04-17
**Scope:** cross-check that active support docs match the post-hardening state.

## Documents checked

| Document | Status | Action |
|---|---|---|
| `reports/summaries/FINAL_DASHBOARD_REVIEW_READY_STATUS.md` | Consistent with current state. Authoritative W/M / IB numbers are from the regenerated bundles (2026-04-16) and are unchanged by this pass. | No update needed. |
| `reports/rebuttal_support/FINAL_UNCERTAINTY_REVIEWER_FAQ.md` | FAQ §8.1 (F29), §8.2 (independence), §8.3 (truncated normal) all match the hardening notes. §8.2 should gain a sentence about the copula being available but disabled by default. | Minor wording update recommended. |
| `audits/uncertainty_governance/PARAMETER_CLASSIFICATION_FINAL.md` | Per-parameter classifications match the active page registry. Ohio experiment data now exists; PARAMETER_CLASSIFICATION_FINAL already covered both regions in its allowed-level table (Ohio-specific F04 override noted). | No update needed. |
| `audits/uncertainty_governance/UNCERTAINTY_FEATURE_REGISTRY.csv` | Still reflects the pre-hardening state (no copula column, no "present_in_ohio_experiment" flag). | Recommend adding a `copula_eligible` column (values: yes for F23–F27, no otherwise) and an `ohio_experiment` column (yes / no). Deferred — the CSV is a secondary artefact; the primary registry is now `PARAMETER_CLASSIFICATION_FINAL.md`. |
| Landing page `streamlit_app.py` | References `PARAMETER_CLASSIFICATION_FINAL.md` in its footer; mentions parameter-level uncertainty design. Matches the current page architecture. | No update needed. |

## Remaining alignment gap

`FINAL_UNCERTAINTY_REVIEWER_FAQ.md` §8.2 currently reads:

> "All trajectory priors (F23–F28) are sampled independently within each MC run. … A copula or correlated-draw model would narrow the tails …"

Post-hardening, the copula is now **implemented** (available via `trajectory_copula=True` in `sample_config`). The FAQ should be updated to say:

> "A Gaussian copula for F23–F27 is implemented in `footprint_model.py` and is available via `sample_config(..., trajectory_copula=True)`. It is disabled by default for backward compatibility with the prior submission; the reported bands use independent sampling. Enabling it is expected to narrow tails because positive adoption–decarbonisation correlation concentrates probability mass away from the extreme 'all-high / all-low' corners."

This is a wording-only update. No other document requires changes.
