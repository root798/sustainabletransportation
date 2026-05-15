# FRAMEWORK_HARDENING_PRE_AUDIT.md

**Date:** 2026-04-17
**Scope:** six unresolved items inspected against the current active codebase state.

---

## Audit table

| # | Issue | Current implementation | Real risk | Proposed fix |
|---|---|---|---|---|
| F29 | 18 absolute ECAV/STI power cells have no direct prior | Disclosed in Tier 3 Advanced Detail and support-boundary table; hidden from user controls; variance enters only through per-subsystem scale factors | LOW — adding cell-level priors would reintroduce S2-01/S2-02 duplication; current approach is intentional | Strengthen justification text in the dashboard and write a hardened audit note explaining why cell-level priors are explicitly excluded |
| COPULA | Independence assumed across F23–F28 trajectory drivers | "Correlation note" in Tier 3 acknowledges it as a documented simplification; no code exists for copula sampling | MEDIUM — the independence assumption is the single largest remaining methodological vulnerability; positive adoption-decarbonisation correlation would narrow tails, so the current independent bands are conservative | Implement a Gaussian copula for F23–F27 with a documented default rank-correlation matrix; regenerate bundles |
| US_AVG | U.S. Average quarantine | Region appears in REGION_ORDER; `st.warning` displayed when selected; paper_safe=False in REGION_PAPER_SAFETY | LOW-MEDIUM — a careless user can still select it, generate a figure, and fail to notice the warning | Remove US Average from the default region selector; make it appear only behind an explicit "show quarantined" toggle; add a strong st.error instead of st.warning |
| POLICY | Aggressive/conservative MC is exploratory only | One-line `st.info` when policy ≠ baseline; no structural gating | MEDIUM — the info is easy to miss; an exported figure under aggressive policy has no watermark | Add a visible "EXPLORATORY" badge and gating warning; prevent paper-safe badge from displaying when policy is non-baseline |
| OH_EXP | Parameter importance experiment is California-only | `scripts/parameter_contribution_experiment.py` has `REGION = "california"` hardcoded; CSV contains only CA data; dashboard falls back to CA data when OH is selected | MEDIUM — weakens the state-to-state parity story; Ohio drivers could differ (e.g. F04 e_fossil is larger for OH coal grid) | Extend the script to run both regions; regenerate; update the dashboard loader to surface region-specific data |
| TRUNC | Truncated normal is normal+clamp approximation | `_sample_distribution` treats `truncated_normal` as `normal` and applies post-sampling min/max clamp (lines 135–204 of footprint_model.py); FAQ §8.3 says ~2% clamp rate at LOW sigmas | LOW — clamp rate is documented and negligible at current settings; a true truncated normal sampler (scipy.stats.truncnorm) exists but would add a dependency | Keep current implementation; quantify clamp rate precisely for all active parameters; document in a short audit note |

---

## Structural context (no blockers)

- Active page: `pages/00_Scenario_Explorer.py` — single-page, parameter-level, three-tier control.
- Bundle outputs: 12 committed CSVs (CA+OH × default+paper-safe × mc_runs/quantiles/metrics). All regenerated 2026-04-16.
- Layer contribution: CA+OH both covered in `LAYER_CONTRIBUTION_EXPERIMENT.csv`.
- Parameter contribution: CA only in `PARAMETER_CONTRIBUTION_EXPERIMENT.csv`.
- Presets: `configs/ui_presets/` has 15 layer-level files + `configs/ui_parameter_presets/` has per-parameter files. Fully wired through `core.py::load_grouped_uncertainty_preset`.
- Support docs: `FINAL_DASHBOARD_REVIEW_READY_STATUS.md`, `FINAL_UNCERTAINTY_REVIEWER_FAQ.md`, `PARAMETER_CLASSIFICATION_FINAL.md` all exist and are mutually consistent.

No structural blocker to proceeding.
