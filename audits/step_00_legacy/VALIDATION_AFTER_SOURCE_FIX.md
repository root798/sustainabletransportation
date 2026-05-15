# VALIDATION_AFTER_SOURCE_FIX

## Regions tested

| Region | Policy coverage checked |
| --- | --- |
| California | baseline/aggressive/conservative |
| Ohio | baseline/aggressive/conservative |
| U.S. Average (synthetic CA/OH midpoint) | baseline/aggressive/conservative |

## Page coverage

| Page | Status | Notes |
| --- | --- | --- |
| Home | checked | Region summary uses corrected baseline semantics. |
| Scenario Explorer | checked | Default controls, labels, uncertainty gate, and subsystem labels audited. |
| Utility Phase Analysis | checked | Definitions and subsystem naming corrected. |
| Uncertainty Analysis | checked | Aligned vs legacy modes split and zero-width aligned bands surfaced. |
| Turning Points | checked | Derived formulas labeled explicitly. |
| State Results | checked | Region provenance and synthetic U.S. Average labeling corrected. |
| Framework Scope | checked | Utility-only quantitative boundary preserved. |

## Validation checks

| Check | Status | Detail |
| --- | --- | --- |
| California baseline vehicle stock loads correctly | pass | 37428700 |
| California aligned quantiles remain baseline-only | pass | The aligned `results/` quantile file currently has zero-width p05-p95 bands. Notebook quantiles exist on disk but are legacy artifacts and are not treated as aligned uncertainty support for live scenario pages. |
| Ohio baseline vehicle stock loads correctly | pass | 10385000 |
| Ohio aligned quantiles remain baseline-only | pass | The aligned `results/` quantile file currently has zero-width p05-p95 bands. Notebook quantiles exist on disk but are legacy artifacts and are not treated as aligned uncertainty support for live scenario pages. |
| U.S. Average (synthetic CA/OH midpoint) baseline vehicle stock loads correctly | pass | 23906850 |
| U.S. Average (synthetic CA/OH midpoint) aligned quantiles remain baseline-only | pass | The aligned `results/` quantile file currently has zero-width p05-p95 bands. Notebook quantiles exist on disk but are legacy artifacts and are not treated as aligned uncertainty support for live scenario pages. |
| Region switch changes baseline defaults | pass | Distinct total_cars values confirmed for all three baseline regions. |
| Legacy notebook quantiles are not silently mixed into aligned mode | pass | Aligned pages use allowed_sources=(results_quantiles,) with allow_fallback=False. |
| Annual energy wording is physically correct | pass | v3 pages now display annual energy demand rather than instantaneous power wording. |
| Subsystem labels are consistent | pass | v3 pages expose sensing / computing / communication for ECAV, ICEAV, and STI. |
| Aligned baseline quantile file degeneracy is visible | pass | The uncertainty page and explorer/utility captions explicitly warn when p05 == p50 == p95. |

## Remaining unsupported cases

- Aggressive and conservative aligned uncertainty files still do not exist.
- The current aligned baseline quantile files are zero-width because the active aligned pipeline is deterministic under the current configs.
- Production, logistics, and end-of-life remain outside the quantitative support boundary.
