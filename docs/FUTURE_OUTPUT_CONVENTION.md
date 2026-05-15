# FUTURE_OUTPUT_CONVENTION.md

Where every future output — audit, fix, architecture design, validation, paper support, scenario variant — should live. Read this before creating any new file.

## Folder → purpose map

| Folder | Contains | Canonical / mirror |
| --- | --- | --- |
| `audits/step_NN_*/` | All artefacts produced in stage NN. One folder per stage; step numbers strictly increase. | Canonical home for every report produced in that stage. |
| `docs/` | Conventions, plans, indexes, guides. Long-lived; not tied to any single stage. | Canonical. |
| `reports/summaries/` | REVIEW files (stage retrospectives / reviews). | **Mirror** of an `audits/step_NN_*/REVIEW_*.md`. |
| `reports/decisions/` | DECISION memos. | Mirror. |
| `reports/validations/` | VALIDATION reports. | Mirror. |
| `reports/changelogs/` | CHANGELOG files. | Mirror. |
| `scenarios/{region}/` | Canonical human-editable scenario template + README. | Canonical. |
| `results/` | Simulation outputs (CSV). Generated, not hand-edited. | Canonical. |
| repo root | Only top-level navigation (`CLAUDE.md`, `README.md`, `REPORTS_INDEX.md`, `requirements.txt`) and runtime code (`footprint_model.py`, `app.py`, `run.py`). | — |

## Destination by output type

| Output type | Where it goes |
| --- | --- |
| **Audit report** (inspection only) | `audits/step_NN_<descriptive>/AUDIT_*.md` + `AUDIT_*.csv` |
| **Fix-stage changelog** | `audits/step_NN_<descriptive>/CHANGELOG_*.md`, mirror to `reports/changelogs/` |
| **Validation report** | `audits/step_NN_<descriptive>/VALIDATION_*.md`, mirror to `reports/validations/` |
| **Decision memo** | `audits/step_NN_<descriptive>/DECISION_*.md`, mirror to `reports/decisions/` |
| **Stage review** | `audits/step_NN_<descriptive>/REVIEW_*.md`, mirror to `reports/summaries/` |
| **Architecture design doc** | `audits/step_NN_architecture_design/PLAN_*.md` or `audits/step_NN_architecture_design/DESIGN_*.md` |
| **Backend refactor notes** | `audits/step_NN_backend_refactor/CHANGELOG_*.md` + `VALIDATION_*.md` |
| **Dashboard alignment notes** | `audits/step_NN_dashboard_alignment/CHANGELOG_*.md` + `VALIDATION_*.md` |
| **Paper-support figures / tables** | `reports/paper_support/` (create when needed). Raw inputs from `results/`. |
| **Scenario template** | `scenarios/{region}/scenario.json` + `scenarios/{region}/README.md` |
| **Scenario variant** (e.g. for a sensitivity scenario) | `scenarios/{region}/scenario__<variant>.json` + `scenarios/{region}/README__<variant>.md`. Loader will need to be updated to accept variant suffixes. |
| **Uncertainty schema doc** (if the schema ever becomes multi-file) | `docs/SCHEMA_UNCERTAINTY_<version>.md` |
| **Human-editable number table** (e.g. a committed-means table) | `scenarios/{region}/reference_numbers.csv` — but only if the numbers are not derivable from `scenario.json`. |
| **CSV audit table** | Same folder as the accompanying MD. Rule: the CSV and the MD that describes it live side by side. |
| **Figure / plot artefact** | `reports/paper_support/figures/` once that folder exists; do not commit large binaries without a plan. |

## Naming

Follow `docs/FILE_NAMING_STANDARD.md`. Canonical prefixes: `AUDIT_`, `REVIEW_`, `DECISION_`, `VALIDATION_`, `CHANGELOG_`, `PLAN_`, `INDEX_`, `REPORT_`, `MEMO_`, `GUIDE_`.

## README / index files — when to create

- **When creating a new `audits/step_NN_*/` folder**: add `README.md` at the same time. Stage folders without READMEs are half-finished.
- **When creating a new region under `scenarios/`**: add `scenarios/{new_region}/README.md`.
- **When a folder accumulates more than 5 files**: add an `INDEX_*.md` or a `README.md` if it doesn't have one.
- **When moving files**: update `docs/FILE_PATH_REDIRECT_MAP.md` and `REPORTS_INDEX.md` in the same change.

## Where later dashboard / data-loading code should read from

- Scenario data: `scenarios/{region}/scenario.json`, falling back to `configs/{region}.json`. The backend loader contract is documented in `docs/SCENARIO_FILE_CONVENTION.md §Load path`.
- Simulation outputs: `results/`. Filename convention `{region}__policy-{policy}__model-{model}_{results,mc_runs,quantiles,metrics,metrics_quantiles}.csv`. Deterministic-only outputs are `{region}_results.csv`.
- Reference metrics / provenance tables: `audits/step_01_quantitative_audit/PARAMETER_AUDIT_CURRENT.csv` when needed.

## Anti-patterns

- Creating a report at the repo root. Always pick a destination from the table above.
- Duplicating canonical content instead of mirroring. Mirror = `cp` of a canonical file, never edited directly. If you find yourself editing a mirror, stop and edit the canonical copy.
- Dumping validation CSVs into `results/` or audit CSVs into `docs/`. Keep outputs and reports separate.
- Inventing new folder names. If the table above does not cover your case, add a row to `docs/ROOT_CLEANUP_RECOMMENDATIONS.md` first, then create the folder.
