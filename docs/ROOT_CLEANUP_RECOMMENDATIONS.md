# ROOT_CLEANUP_RECOMMENDATIONS.md

Inventory of every file at the repository root after the reorganization, classified by whether it stays, was moved, is legacy, or should be ignored in future prompts.

## Files that STAY in the root (runtime + top-level navigation)

| File | Reason |
| --- | --- |
| `CLAUDE.md` | Read by Claude Code at session start. |
| `README.md` | Public-facing project README. |
| `REPORTS_INDEX.md` | Top-level index of every report and memo; primary entry point for finding anything. |
| `requirements.txt` | Root-level Python dependency manifest. |
| `footprint_model.py` | Core simulation engine; the only code file that must be at the root. |
| `app.py` | Legacy Flask dashboard. Still runnable; kept because the README and CLAUDE.md reference it. |
| `run.py` | Legacy orchestrator; still works. |

## Files MOVED during this stage (canonical paths under subfolders)

All 22 audit / review / decision / validation / changelog / CSV files that were previously loose at the root are now under `audits/` with mirror copies in `reports/`. See `FILE_PATH_REDIRECT_MAP.md` for the full list.

Three scenario JSONs (`california.json`, `ohio.json`, `us_average.json`) were duplicated under `scenarios/{region}/scenario.json`. Originals under `configs/` remain as a legacy fallback.

## LEGACY / archived — present but not actively edited

| Path | Status |
| --- | --- |
| `v2_streamlit_app/`, `v2_1_streamlit_app/` | Archived earlier Streamlit iterations. Still runnable; stale REGION_NOTES and older turning-year logic. Do not modify unless the archive itself needs a revision note. |
| `cache/` | Flask app's JSON simulation cache. Runtime-managed; safe to leave. |
| `logs/` | Empty log directory for Flask app. Leave alone. |
| `static/`, `templates/` | Flask UI assets. Only used by `app.py`. Leave alone. |
| `results_notebook/` | Legacy notebook-pipeline outputs. Dashboards expose them as "legacy" with mismatch warnings. Do not overwrite; do not edit in place; flag as not paper-safe. |
| `footpint.ipynb` (typo in filename) | Early scratch notebook. Not referenced anywhere; could be deleted in a later housekeeping pass, but keep for now. |
| `CLEAR_ATS_uncertainty_notebook.ipynb` | Generator for `results_notebook/`; stale relative to current `TransportModel`. Archive; do not edit. |
| `__MACOSX/`, `__pycache__/` | OS / Python metadata. Should be gitignored (probably already are). Leave alone. |

## To IGNORE in later prompts

- `audits/step_00_legacy/*` — archived predecessor reports. Reference them only when writing historical context.
- `results_notebook/*` — stale outputs.
- `v2_streamlit_app/*`, `v2_1_streamlit_app/*` — archived Streamlit apps.
- `footpint.ipynb`, `CLEAR_ATS_uncertainty_notebook.ipynb` — archived notebooks.

When a future prompt asks Claude to "read the reports", it should look in `audits/step_01_quantitative_audit/`, `audits/step_02_audit_fixes/`, `audits/step_03_post_audit_cleanup/`, and `reports/`. The legacy folder is explicitly not part of the active stack.

## Files that need clearer labeling (not done this round)

| Path | Recommended future action |
| --- | --- |
| `footpint.ipynb` | Rename to `archive/footprint_scratch.ipynb` (typo + archival). Not done this round to avoid touching notebook files at the last minute. |
| `app.py`, `run.py`, `templates/`, `static/` | Consider consolidating under a `legacy_flask/` folder in a later stage. Not done this round because `README.md` still documents the Flask path. |
| `cache/` | Add to `.gitignore` if not already. |

## Rule of thumb for future root additions

If a new file is:
- **A report** → goes to `audits/step_NN_*/` (and optionally mirrored to `reports/{summaries,decisions,validations,changelogs}/`).
- **A convention / plan / index** → goes to `docs/`.
- **A scenario template** → goes to `scenarios/{region}/`.
- **A simulation output** → goes to `results/`.
- **A runtime code module** → goes under the appropriate app folder (`v3_streamlit_app/`, `v4_streamlit_app/`), unless it is the core simulator (which stays at the root).

If a new file does not match any of the above, it probably should not be created. The root should stay thin.
