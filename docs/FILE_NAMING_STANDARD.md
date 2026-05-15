# FILE_NAMING_STANDARD.md

Naming convention for reports, memos, changelogs, validations, and scenario files in this repository. Applies to all future work.

## 1. Prefix vocabulary

Every report-type file must start with one of the prefixes below, in **UPPER_SNAKE_CASE**, followed by a descriptive suffix.

| Prefix | Meaning | Example |
| --- | --- | --- |
| `AUDIT_` | Systematic inspection of existing state (no changes applied). | `AUDIT_PARAMETER_INVENTORY.csv` |
| `REVIEW_` | Critical review of a completed stage. | `REVIEW_OF_AUDIT_FIX_STAGE.md` |
| `DECISION_` | Decision memo with explicit classification. | `DECISION_US_AVERAGE_SCENARIO.md` |
| `VALIDATION_` | Proof that a fix / change / reorg is correct. | `VALIDATION_AFTER_AUDIT_FIXES.md` |
| `CHANGELOG_` | Ordered record of changes applied in a stage. | `CHANGELOG_SEMANTIC_ALIGNMENT.md` |
| `PLAN_` | Planning document written before changes are applied. | `PLAN_REPORT_FOLDER_REORGANIZATION.md` |
| `INDEX_` | Listing / index of a folder or topic. | `INDEX_SCENARIO_SOURCE_OF_TRUTH.md` |
| `REPORT_` | General report that does not fit another prefix. | `REPORT_DISTRIBUTION_PROBLEMS.md` |
| `MEMO_` | Short scientific interpretation memo. | `MEMO_QUANTITATIVE_AUDIT.md` |
| `GUIDE_` | Instructions on how to use or edit something. | `GUIDE_SCENARIO_FILE_CONVENTION.md` |
| `SCENARIO_` | A scenario template file (human-editable). | `scenarios/california/scenario.json` (lowercase by convention) |

The prefix is the single most important word for later search. Pick the one that best matches the primary purpose. If in doubt, `REPORT_` is the safe default.

## 2. Keep descriptive suffix specific

- Good: `VALIDATION_AFTER_AUDIT_FIXES.md` (what was validated is clear).
- Bad: `VALIDATION.md` (too generic).

Avoid dates in filenames — use file-system mtime or Git history instead. Exception: paper-submission snapshots, where the date is the version label.

## 3. Extensions

| Extension | Use for |
| --- | --- |
| `.md` | Free-form reports, reviews, changelogs, memos. |
| `.csv` | Machine-readable inventories. |
| `.json` | Scenario templates, machine-readable configs. |
| `.py`, `.ipynb` | Code (never a report). |

## 4. Folder placement

Prefix alone is not enough — placement matters.

| Folder | What lives there |
| --- | --- |
| `audits/step_NN_*/` | Chronological audit stages. Canonical home for AUDIT, REVIEW, CHANGELOG, VALIDATION, DECISION, and MEMO files from that stage. |
| `docs/` | Conventions, plans, indexes, guides. |
| `reports/summaries/` | Mirrors of REVIEW files (for fast lookup). |
| `reports/decisions/` | Mirrors of DECISION files. |
| `reports/validations/` | Mirrors of VALIDATION files. |
| `reports/changelogs/` | Mirrors of CHANGELOG files. |
| `scenarios/{region}/` | SCENARIO templates (canonical). |
| `scenarios/` | `README.md` index. |
| repo root | Only `CLAUDE.md`, `README.md`, `REPORTS_INDEX.md`, `requirements.txt`, and runtime code. |

## 5. Backward compatibility

Existing filenames were not all renamed to strict conformance in this stage — that would break links in paper drafts and in historical Git archaeology. `docs/FILE_PATH_REDIRECT_MAP.md` lists each old path, the new path, the reason, and whether the old path was preserved.

## 6. Legacy file rule

Files in `audits/step_00_legacy/` are **archived**. Do not rename them. Do not edit their content. If you need to supersede one, reference it from the superseding file in a later step folder.
