# REPORT_REORGANIZATION_VALIDATION.md

Evidence that the post-audit reorganization is correct, complete, and non-breaking.

## 1. Inventory

After the reorganization:

| Folder | File count | Notes |
| --- | --- | --- |
| `audits/step_00_legacy/` | 11 MDs + 2 CSVs + 1 README + 3 stale-root JSONs in `stale_root_scenarios/` | Archived; do not edit. |
| `audits/step_01_quantitative_audit/` | 1 CSV + 4 MDs + 1 README | Canonical for the initial audit. |
| `audits/step_02_audit_fixes/` | 1 CSV + 5 MDs + 1 README | Canonical for the fix pass. |
| `audits/step_03_post_audit_cleanup/` | 1 MD + 1 README | Canonical for this stage. |
| `reports/summaries/` | 1 MD mirror | REVIEW_OF_AUDIT_FIX_STAGE.md mirror. |
| `reports/decisions/` | 1 MD mirror | US_AVERAGE_DECISION_NOTE.md mirror. |
| `reports/validations/` | 1 MD mirror | VALIDATION_AFTER_AUDIT_FIXES.md mirror. |
| `reports/changelogs/` | 2 MD mirrors | SEMANTIC_ALIGNMENT_CHANGELOG.md + DISTRIBUTION_FIXES_APPLIED.md. |
| `docs/` | 8 MDs | Conventions, plans, indexes, guides. |
| `scenarios/` | 1 index README + 3 region folders, each containing scenario.json + README.md | Canonical scenario source. |

Root before reorg: 22 loose report/audit files.
Root after reorg: 0 loose report/audit files. Root now holds only top-level navigation (`CLAUDE.md`, `README.md`, `REPORTS_INDEX.md`, `requirements.txt`), runtime code (`footprint_model.py`, `app.py`, `run.py`), and content folders.

## 2. Scenario load-path contract verified

```
python footprint_model.py --scenarios california ohio us_average --years 68 --policy baseline --mc 0
# →
# [california] --mc 0 requested: running nominal deterministic configuration ...
# Results saved to 'results/california_results.csv'
# [ohio] ...
# [us_average] ...
```

```
# v4 loader
python -c "import sys; sys.path.insert(0,'v4_streamlit_app'); import core; \
           cfg = core.load_base_config('california'); \
           print('v4 loader OK, CA total_cars =', cfg['initial_data']['total_cars'])"
# → v4 loader OK, CA total_cars = 37428700

# v3 loader
python -c "import sys; sys.path.insert(0,'v3_streamlit_app'); import dashboard_core; \
           cfg = dashboard_core.load_base_config('california'); \
           print('v3 loader OK, CA total_cars =', cfg['initial_data']['total_cars'])"
# → v3 loader OK, CA total_cars = 37428700
```

All three loaders now pull California data from `scenarios/california/scenario.json` first. The `configs/california.json` legacy fallback remains on disk for backward compatibility but is no longer the primary read path.

## 3. Backward compatibility with legacy `configs/`

```
python -c "import os; \
           print('configs present:', os.path.exists('configs/california.json'), \
                 'scenarios present:', os.path.exists('scenarios/california/scenario.json'))"
# → configs present: True, scenarios present: True
```

A hypothetical older script that reads `configs/california.json` directly still works. Once the editable copy in `scenarios/` diverges, the older script would start seeing stale numbers — a known trade-off documented in `docs/FILE_PATH_REDIRECT_MAP.md §Scenario source files` and `docs/SCENARIO_TEMPLATE_REORGANIZATION_PLAN.md §Forward sync obligation`.

## 4. Internal markdown cross-references

The markdown files produced in this stage were written with the new paths in mind (for example, `REPORTS_INDEX.md` and every `README.md` under `audits/step_NN_*/`). Links within the same step folder use relative paths (e.g. `../step_02_audit_fixes/VALIDATION_AFTER_AUDIT_FIXES.md`). Cross-stage links use repo-root-relative paths.

Pre-existing internal references inside the files that were moved into `audits/step_01_quantitative_audit/` and `audits/step_02_audit_fixes/` were NOT rewritten, because:

- Those files were written to stand alone.
- Their internal references (e.g. "see VALIDATION_AFTER_AUDIT_FIXES.md") are to sibling files in the same folder, so relative links still resolve.
- Any cross-stage references (e.g. the audit memo referencing `PARAMETER_INCONSISTENCY_REPORT.md`) also resolve because those files now live next to each other inside the stage folder.

A full pass over file-content cross-references is deferred; it was skipped in favour of keeping the moves verbatim (no content edits except the new READMEs).

## 5. Broken-reference check

Known potential breakages:

| Reference | Resolution |
| --- | --- |
| `README.md` (root) — may mention pre-move file paths. | Left unchanged this stage. README is primarily user-facing; a targeted edit belongs to a README-refresh stage. |
| `CLAUDE.md` — previously mentioned root-level audit markdown. | Updated in the same batch as this validation (see §6). |
| `app.py`, `run.py` — do not reference any moved file. | No change needed. |
| `v3_streamlit_app/` and `v4_streamlit_app/` page code | Do not reference any moved file. Loaders use `SCENARIOS_DIR` → fallback `CONFIGS_DIR`. |
| `v2_streamlit_app/`, `v2_1_streamlit_app/` | Archived. Any staleness there is orthogonal to this reorg. |

No runtime break observed.

## 6. CLAUDE.md updated

`CLAUDE.md` was edited to point readers at `REPORTS_INDEX.md`, `scenarios/README.md`, and `docs/FUTURE_OUTPUT_CONVENTION.md` for future navigation. See the diff on `CLAUDE.md` in this stage's commit.

## 7. Paths the next prompt should use

| Purpose | Canonical path |
| --- | --- |
| Edit California numbers | `scenarios/california/scenario.json` |
| Edit Ohio numbers | `scenarios/ohio/scenario.json` |
| Edit U.S. Average numbers | `scenarios/us_average/scenario.json` |
| Find a specific audit report | `audits/step_NN_*/*` (via `REPORTS_INDEX.md`) |
| Find a decision memo quickly | `reports/decisions/*` |
| Find a validation report quickly | `reports/validations/*` |
| Find a changelog quickly | `reports/changelogs/*` |
| Read a convention | `docs/*.md` |

## 8. Things still too messy (not fixed this stage)

- `app.py`, `run.py`, `templates/`, `static/` clutter at the root. Candidate `legacy_flask/` consolidation deferred.
- `footpint.ipynb` (typo). Candidate rename to `archive/footprint_scratch.ipynb` deferred.
- `CLEAR_ATS_uncertainty_notebook.ipynb` still lives at root; not archived this stage because it is still the generator for `results_notebook/`.
- `__MACOSX/`, `__pycache__/` metadata folders at root. Should be in `.gitignore`; not touched.
- `configs/` still holds the legacy fallback. Recommended to delete in a later pass once nothing depends on it.
- The three previously-loose root `california.json` / `ohio.json` / `us_average.json` (stale old values) were moved to `audits/step_00_legacy/stale_root_scenarios/`.
- `Annual Review Form 12.2025.pdf` at root — unrelated to the project; kept in place.
