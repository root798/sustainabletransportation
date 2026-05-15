# AUTO_REVIEW_REPORT.md

Automated review of the repository's paper-adjacent files for language hazards that must be caught before manuscript finalisation. **No manuscript source files were found in the repository** — the manuscript is external and must be hand-edited using the change maps below. This report documents every hazard detected in support files and indicates which must be preserved (advisory) vs which must be fixed (live hazard).

---

## 1. Search targets

For each hazard, we ran a repo-wide grep over Markdown + text files, excluding `__pycache__`, `.git`, legacy nested clone `CLEAR_ATS/`, and `__MACOSX`:

- `forecast` / `prediction` variants
- `peak emissions YYYY` / `peak year YYYY` without a "modelled" qualifier
- `Ohio turning year = YYYY` or `Ohio halves by YYYY` as a numeric year
- `U.S. Average` adjacent to derived metrics (energy, emissions, peak, turning)
- Post-saturation narrow-band language implying confidence
- Legacy references to the pre-revision boundary (2033 / 2035)

## 2. Findings — all matches are in support files, not manuscript

### 2.1 `forecast` / `prediction` hits (10 files)

All hits are **legitimate** — they appear in "do-not-use" advisory tables, quarantine notes, or legacy audit records:

- `audits/step_06_paper_alignment/RESULTS_ALIGNMENT.md` — in the forbidden-wording table.
- `audits/step_06_paper_alignment/METHODS_ALIGNMENT.md` — same.
- `audits/step_06_paper_alignment/CAPTION_ALIGNMENT.md` — same.
- `audits/step_06_paper_alignment/REVIEWER_RESPONSE_FINAL.md` — same.
- `audits/step_05_dashboard_alignment/CA_OH_INTERPRETATION_BOUNDARY.md` — advisory.
- `audits/step_05_dashboard_alignment/CA_OH_FIGURE_SUPPORT.md` — advisory.
- `audits/step_05_dashboard_alignment/CA_OH_REVIEWER_RESPONSE_SUPPORT.md` — advisory.
- `v4_streamlit_app/VALIDATION_REPORT_V3_1.md` — legacy V3.1 validation (archived).
- `v4_streamlit_app/DATA_MISALIGNMENT_AUDIT_V3_1.md` — legacy V3.1 audit (archived).
- `audits/step_00_legacy/*` — archived; not paper-facing.

**Action**: no change required. Advisory uses of the word "forecast" / "prediction" inside do-not-use tables are expected.

### 2.2 Numeric Ohio turning year

All hits are in contexts where the text **explicitly** labels Ohio's turning year as "not reached within horizon" or as a horizon-edge caveat:

- `v4_streamlit_app/pages/03_Turning_Points.py:107` — chart caption saying "typically not reached …". Correct.
- `reports/paper_support/captions/ohio__annual_emissions.txt` — "modelled turning year not reached within horizon." Correct.
- `audits/step_04_uncertainty_architecture/CHECKPOINT_REMAINING_NUMBERS.csv` — audit row documenting the NaN result. Correct (not paper-facing).
- `audits/step_04_uncertainty_architecture/CHECKPOINT_REMAINING_NUMBERS_AUDIT.md` — documents the anti-pattern and warns against it. Correct.
- `audits/step_06_paper_alignment/*` — advisory / do-not-use contexts.

**Action**: no change required. Every active reference treats Ohio's turning year as "not reached in horizon".

### 2.3 Numeric peak-year references (2036 / 2046 / 2076)

All matches occur in contexts already labelled "modelled":

- `reports/validations/FRONTEND_VALIDATION_PHASE2.md:97,136` — human verification checklist items (`Modelled peak emissions / Modelled peak year 2036 | 2076`). Correct.
- `audits/step_05_dashboard_alignment/FRONTEND_VALIDATION_PHASE2.md:97,136` — same.

**Action**: no change required. No bare "peak year 2036" appears in support files.

### 2.4 `U.S. Average` adjacent to derived-metric words (18 files)

Every match is in a file whose explicit purpose is to document or enforce the quarantine:

- `US_AVERAGE_SOURCE_TRACE.md`, `US_AVERAGE_TRACE_VALIDATION.md` — the forensic trace itself.
- `CHECKPOINT_DESIGN_CONSTRAINTS.md`, `CHECKPOINT_REMAINING_NUMBERS_AUDIT.md` — audit constraints.
- `TABLE_SANITIZATION.md`, `RESULTS_ALIGNMENT.md`, `REVIEWER_RESPONSE_FINAL.md`, `CAPTION_ALIGNMENT.md` — Stage 1 support files; every U.S. Average reference is explicitly labelled quarantined.
- `scenarios/us_average/README.md` — per-region README with the anomaly warning.
- `v3_streamlit_app/reports/PARITY_AUDIT_*`, `SCENARIO_*_AUDIT.md` — legacy v3 audit documents.
- `reports/changelogs/SEMANTIC_ALIGNMENT_CHANGELOG.md` — documents the quarantine rewrite.
- `reports/decisions/US_AVERAGE_DECISION_NOTE.md` — the decision memo.

**Action**: no paper-facing file contains an unqualified U.S. Average derived metric. The only live manuscript risk is the external manuscript draft itself (see `MANUSCRIPT_CHANGE_MAP.md`).

### 2.5 Saturation-as-confidence hazard

Every support file that discusses saturation already carries the "cap artefact, not predictability" language (`CA_OH_SATURATION_EVIDENCE.md`, `CAPTION_ALIGNMENT.md`, `REVIEWER_RESPONSE_FINAL.md`, generated caption `.txt` files, dashboard pages).

**Action**: no change required in support files. The hazard remains only in whatever paragraph of the external manuscript discusses saturation; the change map addresses it.

### 2.6 Legacy boundary year (2033 / 2035)

Grep for `interpretation.*2033` or `interpretation.*2035`:

- All hits are historical / comparison references in `audits/step_04_*` / `audits/step_05_*`, documenting the pre-L2 vs post-L2 shift. These are correct — they document *why* the current 2030 / 2031 are lower than the prior submission.

**Action**: no change required in support files.

---

## 3. Live hazards outside this repository

- **Manuscript draft (external).** Must be hand-edited per `MANUSCRIPT_CHANGE_MAP.md`.
- **Response letter draft (external).** Must be hand-edited per `REBUTTAL_CHANGE_MAP.md`.
- **Any figure imported from the prior submission.** Replace with the current `reports/paper_support/figures/` outputs per `FIGURE_INSERTION_MAP.md`.

## 4. Summary matrix

| hazard | repo support files | manuscript (external) | response letter (external) |
| --- | :---: | :---: | :---: |
| "forecast" / "prediction" in claims | ✅ clean (advisory only) | **❓ must be edited** | **❓ must be edited** |
| Numeric Ohio turning year | ✅ clean | **❓ must be edited** | **❓ must be edited** |
| Bare "peak year YYYY" without "modelled" | ✅ clean | **❓ must be edited** | **❓ must be edited** |
| U.S. Average derived metric | ✅ clean | **❓ must be edited** | **❓ must be edited** |
| Post-saturation confidence language | ✅ clean | **❓ must be edited** | **❓ must be edited** |
| Old boundary year (2033 / 2035) | ✅ clean | **❓ must be edited** | **❓ must be edited** |

## 5. Recommended editor workflow

1. Open the external manuscript.
2. For each hazard row in the table above, grep the manuscript; apply the fixes from `MANUSCRIPT_CHANGE_MAP.md`.
3. Open the external response letter.
4. Apply `REBUTTAL_CHANGE_MAP.md`.
5. Re-render figures from `reports/paper_support/figures/` using `FIGURE_INSERTION_MAP.md`.
6. Re-paste captions from `CAPTION_ALIGNMENT.md`.
7. Sanitise tables per `TABLE_SANITIZATION.md`.
8. Re-run the auto-review grep against the updated manuscript once it is checked into version control.
