# FINAL_BLOCKERS_AND_RISKS.md

Final register of blockers and risks at the end of the autonomous multi-stage run. Every entry is classified as blocker, risk, or polish item. No entry below prevents a revision submission that follows the `MANUSCRIPT_CHANGE_MAP.md` and `REBUTTAL_CHANGE_MAP.md` instructions.

---

## Blockers — require external input

### B1. U.S. Average consumption-table source confirmation

- **Status**: unresolved; quarantined.
- **Detail**: `scenarios/us_average/scenario.json:consumption_rates` has 12 of 18 sensing / communication cells diverging 10–30× from the matching California and Ohio cells under an unresolved source mismatch. Forensic trace in `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md` identifies commit `26cb28c` (2025-03-12, author xiw019) as the direct JSON edit, but no derivation script or literature cite exists in the repository.
- **Impact on paper**: U.S. Average derived metrics (energy, emissions, peak, turning, interpretation boundary) are not paper-safe to cite. CA and OH are fully paper-safe.
- **What would unblock**: the original author's notes / spreadsheet / reference naming the source of the inflated sensing / communication values. Alternatively, a decision to rescale the 12 anomalous cells to the CA/OH arithmetic midpoint.
- **Action if the block persists**: restrict the manuscript to CA and OH; keep the quarantine banner on every dashboard page; leave `scripts/build_paper_figures.py` restricted to `PAPER_REGIONS = ("california", "ohio")`.

## Risks — known but not blocking

### R1. `hardware_supply_shock:severe` `ecav_scale_factors.computing` perturbation is silently skipped

- **Status**: documented in `STRUCTURAL_SHOCK_IMPLEMENTATION.md §9`.
- **Detail**: the `_SHOCK_ATTR_MAP` in `TransportModel` covers `growth_rates.*` and a few `emission_factors.*` / `model_variants.target_year` paths. It does not cover nested `consumption_rates.ecav_scale_factors.computing`. The `severe` severity's efficiency-doubling component still fires; the scale-factor inflation is skipped.
- **Impact on paper**: the `hardware_supply_shock:severe` trajectory is partially understated. `moderate` and `mild` severities are unaffected.
- **What would unblock**: extend `_SHOCK_ATTR_MAP` with `consumption_rates.ecav_scale_factors.computing → self._ecav_scale_computing_shock` and add a runtime path that re-scales the `ecav_power` computing column under a schedule entry. A ~30-line patch in a follow-up stage.

### R2. Sampled-parameters list in v4 Uncertainty Analysis is hand-authored

- **Status**: flagged in `STEP_05B_DASHBOARD_IMPLEMENTATION.md §6`.
- **Detail**: the sampled-parameters table in `v4_streamlit_app/pages/04_Uncertainty_Analysis.py` is maintained by hand and mirrors the content of `scenarios/{region}/scenario.json:data_uncertainty`. If the scenario file is edited and the UI page is not, the two diverge silently.
- **Impact on paper**: no direct paper impact (the table is UI context, not a methods source). Indirect impact: the paper's Methods section relies on `METHODS_ALIGNMENT.md §M2`, which was also hand-authored against the current scenario file.
- **What would unblock**: auto-generate the table from `scenarios/{region}/scenario.json:data_uncertainty` at page load. Small dashboard refactor.

### R3. Stage-1 support files are bound to current backend numerics

- **Status**: expected behaviour, flagged here for awareness.
- **Detail**: numeric claims in `RESULTS_ALIGNMENT.md`, `CAPTION_ALIGNMENT.md`, `REVIEWER_RESPONSE_FINAL.md`, and the figure captions under `reports/paper_support/captions/` are bound to MC 200 @ seed 42 on the current scenario files. If the scenario files are re-authored or the MC ensemble is regenerated with different parameters, every numeric claim must be re-derived. `scripts/build_paper_figures.py` handles caption regeneration automatically; the Stage-1 Markdown files are NOT regenerated automatically and must be re-synced by hand.
- **What would unblock**: a small generator that rewrites Stage-1 Markdown files from the backend. Out of scope for this run.

### R4. Archived v2 / v2.1 apps still reference `configs/`

- **Status**: intentional, flagged in `docs/ROOT_CLEANUP_RECOMMENDATIONS.md`.
- **Detail**: `v2_streamlit_app/` and `v2_1_streamlit_app/` plus their `data_contracts/` still read from `configs/` only. They do not know about `scenarios/`. They also do not know about the step-04E L2 additions or the saturation metadata.
- **Impact on paper**: zero. These apps are archived; paper-facing work uses v4 (and v3 as the mature legacy dashboard).
- **What would unblock**: retirement decision — either delete the v2 / v2_1 trees or repoint their `data_contracts/` at `scenarios/`. Recommended: delete in a later housekeeping stage once no external consumer depends on them.

### R5. `CLEAR_ATS/` nested clone

- **Status**: isolated in place; not imported at runtime.
- **Detail**: a full legacy clone of an earlier repo state (`CLEAR_ATS/footprint_model.py`, `CLEAR_ATS/app.py`, `CLEAR_ATS/configs/`, `CLEAR_ATS/v2_streamlit/`). Not in the active Python path.
- **Impact on paper**: zero. Can confuse anyone navigating the repo by folder.
- **What would unblock**: deletion in a housekeeping pass.

## Polish items — documentation / indexing

### P1. `REPORTS_INDEX.md` missing recent step folders

- `REPORTS_INDEX.md` lists `step_00_legacy`, `step_01_quantitative_audit`, `step_02_audit_fixes`, `step_03_post_audit_cleanup`. It does not yet list `step_04_uncertainty_architecture`, `step_05_dashboard_alignment`, `step_06_paper_alignment`, `step_07_structural_shocks`, or `final_consistency`. Stage 5 will fix.

### P2. `CLAUDE.md` out of date for new sections

- `CLAUDE.md` documents the scenario / configs / audit / reports layout but does not yet mention the shock registry (`scenarios/shocks/`), the paper-support package (`reports/paper_support/`), or `scripts/build_paper_figures.py`. Stage 5 will update if in scope.

### P3. `footpint.ipynb` typo + legacy notebook stale

- Root-level `footpint.ipynb` (typo) and `CLEAR_ATS_uncertainty_notebook.ipynb` (stale vs current backend) are retained in place. Cleanup deferred per `docs/ROOT_CLEANUP_RECOMMENDATIONS.md §To IGNORE in later prompts`.

### P4. No shock figures yet

- `scripts/build_paper_figures.py` covers baseline. A `scripts/build_shock_figures.py` would build shock-vs-baseline overlays. Not required for the revision submission, which can describe shocks textually.

### P5. No dashboard shock page yet

- `v4_streamlit_app/pages/05_Structural_Shocks.py` is designed in `STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md §8` but not implemented. Backend data is ready for it.

## Revision-readiness summary

- **Paper-facing writing**: ready. Nine Stage-1 support files provide paste-ready Results, Methods, captions, tables, reviewer response, and change maps for the external manuscript and response letter.
- **Paper-facing figures**: ready. Eight PDFs + PNGs in `reports/paper_support/figures/{california,ohio}/` plus eight caption `.txt` files.
- **Backend uncertainty**: ready. L1 + L2 + L3 expansion is implemented; saturation metadata is produced as a sidecar; structural shocks are implemented as separate labelled scenarios with clean output separation.
- **Dashboard**: ready. Post-boundary shading, saturation markers, "Modelled" labels, Ohio "Not reached in horizon", U.S. Average quarantine banners all live in v4 (and partially v3).
- **Reproducibility**: all baseline and shock outputs are bit-reproducible at fixed seed; CLI contract in `footprint_model.main` covers both `--mc 0` deterministic and `--mc 200 --seed 42` ensemble plus `--shock {name}` orchestration.

No hard blocker remains for revision submission under the "California and Ohio only; U.S. Average quarantined" scope.
