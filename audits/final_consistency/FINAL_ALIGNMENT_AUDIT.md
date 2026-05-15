# FINAL_ALIGNMENT_AUDIT.md

Repository-wide consistency audit at the end of the autonomous multi-stage run. Covers support files, figures, dashboards, backends, scenario templates, shock outputs, and legacy archives.

---

## 1. Boundary consistency — ✅ clean

Live check (MC 200, seed 42, refreshed at step 04E):

| region | footprint_model | v3 dashboard_core | v4 core |
| --- | ---: | ---: | ---: |
| California | 2030 | 2030 | 2030 |
| Ohio | 2031 | 2031 | 2031 |

All three codepaths import the same `compute_interpretation_boundary` + constants from `footprint_model.py`. No duplication.

## 2. Turning-year consistency — ✅ clean

| region | peak | turning |
| --- | ---: | --- |
| California | 2036 | 2046 |
| Ohio | 2076 (horizon edge) | **not reached in horizon** |

All dashboards and captions use the "Modelled" qualifier and render Ohio as "Not reached in horizon".

## 3. Saturation metadata — ✅ clean

Sidecar sidefiles: `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json`.

| region | Clean Energy Fraction first_saturation_year |
| --- | ---: |
| California | 2040 |
| Ohio | 2075 |
| U.S. Average | null (not tracked; quarantined) |

v4 Scenario Explorer + Uncertainty Analysis pages consume the sidecar through `core.load_saturation_metadata`. Figure captions auto-include cap-artefact language where applicable.

## 4. Paper-safety gating — ✅ clean

`REGION_PAPER_SAFETY` flag:

| region | paper_safe (v3 + v4) |
| --- | :---: |
| California | ✅ True |
| Ohio | ✅ True |
| U.S. Average | ❌ False (banner shown on every page that renders US avg) |

`scripts/build_paper_figures.py` restricts output to `PAPER_REGIONS = ("california", "ohio")`. U.S. Average is never emitted. Confirmed by listing `reports/paper_support/figures/` — only `california/` and `ohio/` subfolders exist.

## 5. Scenario loader priority — ✅ clean

Four active loaders (CLI `footprint_model.load_config`, v3 `dashboard_core.load_base_config`, v4 `core.load_base_config`, v3 `data_contracts.load_results.load_config`) all prefer `scenarios/{region}/scenario.json` and fall back to `configs/{region}.json`. Verified in `audits/step_04_uncertainty_architecture/US_AVERAGE_TRACE_VALIDATION.md §A–B`.

Remaining `configs/`-only references are archived (v2 / v2_1 apps, legacy nested `CLEAR_ATS/` clone) and documented as out-of-scope.

## 6. Shock pipeline separation — ✅ clean

- Baseline MC quantile CSVs have **no** `shock_active` column.
- Shock CSVs carry the `shock_active` column; baseline CSVs do not.
- Shock outputs live exclusively under `results/shocks/`; baseline outputs live in `results/` root.
- `scripts/build_paper_figures.py` reads only `results/{region}__policy-baseline__model-fixed_table_quantiles.csv` + `results/{region}_results.csv`; it does NOT consume `results/shocks/`.
- U.S. Average shock runs are rejected by default; `--allow-quarantined` routes them to `results/shocks/quarantined/`.

## 7. Paper-support content — ✅ clean

Every paper-facing support file (Stage 1) uses CA/OH only. Forbidden wording (`forecast`, `prediction`, bare `peak year YYYY`, numeric Ohio turning year, U.S. Average derived metric, post-saturation confidence) is only present inside advisory "do-not-use" tables or quarantine notices. See `AUTO_REVIEW_REPORT.md §2` for the full inventory.

Figure files on disk match the captions under `reports/paper_support/captions/`; the captions match `CAPTION_ALIGNMENT.md` which itself was copied from the machine-generated text.

## 8. Dashboard vs backend numeric agreement — ✅ clean

Human-verification checklist in `FRONTEND_VALIDATION_PHASE2.md §G` covers every metric card and chart annotation for CA/OH. The spot-checks pass:
- CA Scenario Explorer: boundary 2030, Clean saturation 2040 marker, BEV late-horizon annotation, modelled turning 2046.
- OH Scenario Explorer: boundary 2031, Clean saturation 2075, "Not reached in horizon" + horizon-edge caveat.
- Uncertainty Analysis: Paper-safe column, saturation diagnostics table.
- Turning Points: "Not reached in horizon" box for Ohio, horizon-edge warning.

## 9. Structural shock separation from MC — ✅ clean

Verified in `STRUCTURAL_SHOCK_VALIDATION.md §V1–V10`:

| check | result |
| --- | :---: |
| Baseline byte-identical with/without shock flag | ✅ |
| `shock_active` column absent from baseline CSVs | ✅ |
| All 10 shock CSVs under `results/shocks/` | ✅ |
| US avg rejected unless `--allow-quarantined` | ✅ |
| Baseline quantile CSVs have no shock contamination | ✅ |
| `scripts/build_paper_figures.py` does not read `results/shocks/` | ✅ |

## 10. Stale / archived path isolation — ✅ clean

- `audits/step_00_legacy/` — archived; not consumed by any active codepath.
- `audits/step_00_legacy/stale_root_scenarios/` — three old root-level JSONs moved here in step 03.
- `CLEAR_ATS/` nested clone — unchanged; not imported.
- `v2_streamlit_app/`, `v2_1_streamlit_app/` — still on disk, read `configs/` directly (intentional, archived).
- `results_notebook/` — legacy notebook artefacts, flagged as "legacy" with mismatch warnings in dashboards.

None of these leak into active paper-facing outputs.

## 11. Root-level clutter — ⚠️ minor

Files still at the root (expected):
- `CLAUDE.md`, `README.md`, `REPORTS_INDEX.md`, `requirements.txt` (navigation)
- `footprint_model.py`, `app.py`, `run.py` (runtime)
- `Annual Review Form 12.2025.pdf` (unrelated to the project)
- `footpint.ipynb` (typo; archived in place)
- `CLEAR_ATS_uncertainty_notebook.ipynb` (generator for legacy `results_notebook/`, archived in place)

Not paper-facing hazards, but cleanup deferred per `docs/ROOT_CLEANUP_RECOMMENDATIONS.md`.

## 12. Reports index + cross-references

`REPORTS_INDEX.md` at the repo root lists `step_00_legacy`, `step_01_quantitative_audit`, `step_02_audit_fixes`, `step_03_post_audit_cleanup`, and points at `docs/`, `reports/`, `scenarios/`. The index does not yet list `step_04_uncertainty_architecture`, `step_05_dashboard_alignment`, `step_06_paper_alignment`, or `step_07_structural_shocks`. Stage 5 will update the index.

## 13. Minor issues found

- **`hardware_supply_shock:severe`** includes a `consumption_rates.ecav_scale_factors.computing` perturbation that the current shock-attr mapping does not handle. The efficiency-doubling portion still fires; the scale-factor portion is silently skipped. Documented in `STRUCTURAL_SHOCK_IMPLEMENTATION.md §9`. **Not a paper-safety hazard** — the shock still produces a reasonable trajectory; the "severe" effect is partially understated. Flagged for a follow-up implementation round.
- **`REPORTS_INDEX.md`** does not list step-04 through step-07 folders. Stage 5 will update.
- **`CLAUDE.md`** mentions scenario conventions but does not yet link to the shock registry or the paper-support package. Stage 5 may update.

## 14. No hard blockers detected

Every paper-facing surface is internally consistent. The known issues above are documentation / indexing polish items for Stage 5, not blockers for revision submission.
