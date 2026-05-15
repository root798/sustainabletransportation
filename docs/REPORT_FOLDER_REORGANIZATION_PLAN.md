# REPORT_FOLDER_REORGANIZATION_PLAN.md

Plan that was executed to move audit, review, memo, changelog, and validation files out of the repo root into a step-based structure.

## Problem

Before this stage, 22 audit / review / memo / changelog / CSV files were loose at the repo root. No clear chronology, no grouping by kind, no per-stage README.

## Chosen structure

```
audits/
├── step_00_legacy/             (pre-audit artefacts; archived)
│   └── README.md
├── step_01_quantitative_audit/ (full audit, pre-fix)
│   └── README.md
├── step_02_audit_fixes/        (fix pass)
│   └── README.md
└── step_03_post_audit_cleanup/ (current stage)
    └── README.md

docs/
├── FILE_NAMING_STANDARD.md
├── FILE_PATH_REDIRECT_MAP.md
├── ROOT_CLEANUP_RECOMMENDATIONS.md
├── SCENARIO_FILE_CONVENTION.md
├── SCENARIO_SOURCE_OF_TRUTH_INDEX.md
├── SCENARIO_TEMPLATE_REORGANIZATION_PLAN.md
├── REPORT_FOLDER_REORGANIZATION_PLAN.md      (this file)
├── FUTURE_OUTPUT_CONVENTION.md
└── REPORT_REORGANIZATION_VALIDATION.md

reports/
├── summaries/    (REVIEW_* mirrors)
├── decisions/    (DECISION_* mirrors)
├── validations/  (VALIDATION_* mirrors)
└── changelogs/   (CHANGELOG_* mirrors)

scenarios/
├── README.md
├── california/, ohio/, us_average/   (each with scenario.json + README.md)

REPORTS_INDEX.md (root)
```

## Files moved

See `docs/FILE_PATH_REDIRECT_MAP.md` for the complete old → new path table.

Summary counts:

| Stage bucket | Files moved |
| --- | --- |
| `audits/step_00_legacy/` | 11 (all predating the current audit pipeline) |
| `audits/step_01_quantitative_audit/` | 5 (PARAMETER_AUDIT_CURRENT.csv + 4 MDs) |
| `audits/step_02_audit_fixes/` | 6 (DISTRIBUTION_AUDIT_TABLE.csv + 5 MDs) |
| `audits/step_03_post_audit_cleanup/` | 1 (REVIEW_OF_AUDIT_FIX_STAGE.md) |
| `reports/summaries/` (mirror) | 1 |
| `reports/decisions/` (mirror) | 1 |
| `reports/validations/` (mirror) | 1 |
| `reports/changelogs/` (mirrors) | 2 |

Mirrors are duplicates of canonical files, kept for fast look-up by kind. Canonical path for each report is always under `audits/step_NN_*/`.

## Why step-numbered folders

- Chronology is the single most important axis: someone reading a report needs to know what came before and after it.
- Step numbers give a stable sort order regardless of filename changes.
- A new stage (`step_04_*`) can be added without touching earlier folders.

## Why separate `reports/` categorised folders

- The step folders are optimised for "what happened when". The `reports/` folders are optimised for "show me the latest decision memo" or "show me all validation reports".
- Mirrors cost a `cp` command and a few kilobytes; the look-up convenience is worth it.

## Why `docs/` for conventions

- Planning, convention, naming, and index files describe *how* to work with the repo, not *what* was audited. They are long-lived; they do not belong in any one step folder.

## Rules for the next stage

- Any new report goes into `audits/step_NN_*/` where NN is the current stage number.
- Add a README at stage creation time.
- Mirror review / decision / validation / changelog files into `reports/` on stage completion.
- Update `REPORTS_INDEX.md` at stage completion.

## Things deliberately NOT moved

- Runtime code: `footprint_model.py`, `app.py`, `run.py`, `v3_streamlit_app/`, `v4_streamlit_app/`, `templates/`, `static/`.
- Simulation outputs: `results/`, `results_notebook/`.
- Notebooks: `footpint.ipynb`, `CLEAR_ATS_uncertainty_notebook.ipynb` (archived in place).
- The `configs/{region}.json` legacy fallbacks.
- The root `CLAUDE.md`, `README.md`, `requirements.txt`.
