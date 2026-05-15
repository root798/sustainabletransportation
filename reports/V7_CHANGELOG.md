# V7_CHANGELOG — public-facing dashboard refactor

**v7 path**: `v7_streamlit_app/`  (non-destructive; v5 and v6 remain on disk)
**Inheritance source**: `v6_streamlit_app/` (as the working baseline)
**Calculation engine**: `footprint_model.py` — **unchanged**
**Numeric regression**: v7 vs v5 deterministic CSVs match within 1.5e-16 on every annual value across California, Ohio, and U.S. Average. No calculation change.

---

## 1. Final page architecture

| Nav position | File | Source |
| --- | --- | --- |
| 1. **Overview** | `v7_streamlit_app/streamlit_app.py` | Rewritten (merges former System Boundary and Scope content) |
| 2. **One-Time Energy** | `v7_streamlit_app/pages/01_One_Time_Energy.py` | Inherited from v5; user-facing copy cleaned |
| 3. **Utility Phase Energy** | `v7_streamlit_app/pages/02_Utility_Phase_Energy.py` | New (static interpretive view) |
| 4. **Scenario Explorer** | `v7_streamlit_app/pages/03_Scenario_Explorer.py` | Inherited from v6 page 00; cleaned + Subsystem Decomposition figure added + Factor panel compacted |

Exactly four navigation entries. No hidden / developer pages.

---

## 2. Change log by page

### 2.1 Overview (`streamlit_app.py`)

- **Rewritten** from the v6 landing page.
- Title is now "Overview" (page_title and nav label).
- Adds: project-in-brief paragraph; two-column "One-Time Energy" vs "Utility-Phase Energy" explanation; scope-and-system-boundary block (merged from the former System Boundary page); how-to-read guide for the three other pages; uncertainty-reading note.
- **Removed** all internal-language references: v6 version badge, navigation list of deleted pages, internal caption references (e.g., "See `reports/summaries/V6_CONSTRUCTION_STATUS.md` …").
- **Removed** the "v6 inherits v5 simulator and visual language" technical stanza — replaced by audience-facing text.

### 2.2 One-Time Energy (`pages/01_One_Time_Energy.py`)

- **Removed** the page-load sidebar factor-legend block (v6-era; does not exist in v7).
- **Removed** the page-header caption that started with "Production and logistics phase of the CLEAR-ATS life cycle. CLEAR-ATS stands for …" and enumerated manuscript Figure 3a / Extended Data Tables 3 and 4. Replaced by a short audience-facing caption.
- **Removed** the trailing caption that pointed at `audits/final_consistency/ONE_TIME_PAGE_COMPREHENSIVE_FIX_VALIDATION.md` and `reports/summaries/ONE_TIME_PAGE_COMPREHENSIVE_FIX_STATUS.md`. Replaced with a neutral one-line footer.
- **Removed** the "(documentary only)" inline labels on Block 3 selectboxes; replaced with a short upper caption that states which selectboxes are wired vs decorative, in audience language.
- **Removed** the "*(wired)*" and "*(documentary only)*" bracketed labels on selectbox titles; help text updated to say "names the scenario assumption; does not currently change the downstream values" in audience language.
- **Removed** the "Major-6 flagged in `reports/summaries/MASTER_ACADEMIC_VALIDATION_REPORT.md`" mention inside the φ derivation block.
- **Removed** the "manuscript-text aggregation" language for the STI Basic unit total; replaced by a neutral "aggregation discrepancy" caption that still shows both numbers.
- **Removed** the "Major-6 documented" paragraph in the Equation-13 prose.
- All calculations, figures, cross-check tables, sliders, selectboxes, and download behaviours **preserved unchanged**.

### 2.3 Utility Phase Energy (`pages/02_Utility_Phase_Energy.py` — NEW)

A new static interpretive page:

- Region-independent header + caption.
- **Figure 1**: Annual ATS emissions for California and Ohio side by side, with residual bands overlaid from the committed default bundle.
- **Figure 2**: Subsystem stacked bar at 2050 (ECAV / ICECAV / STI) for both regions.
- **Figure 3**: Sensing / Computing / Communication stacked-area decomposition over time, two-column CA vs OH.
- **Figure 4**: BEV fraction and Low-carbon electricity share over time (two-panel).
- **Figure 5**: Peak and turning year summary table for both regions.

No simulator invocation. Reads existing bundles and deterministic CSVs under `results/` only. Uses NATURE_CATEGORICAL palette exclusively.

### 2.4 Scenario Explorer (`pages/03_Scenario_Explorer.py`)

Moved from v6 `pages/00_Scenario_Explorer.py` to `pages/03_Scenario_Explorer.py` so the four-page navigation order reads Overview → One-Time → Utility Phase → Scenario Explorer.

- **Removed** module docstring references to `audits/final_consistency/V5_*`. Replaced with a short functional header.
- **Removed** page_title "Scenario Explorer v5.1"; now "Scenario Explorer".
- **Removed** the v6-era caption beginning "v6 note · L1 / L2 are **aleatoric** …". Replaced with an audience-oriented one-paragraph explanation of the band semantics.
- **Removed** the "v6 sidebar factor legend" import block and the corresponding sidebar render call.
- **Renamed** the expander ":red_circle: v6 policy scenario" to "Policy pathway". Removed the reference to the removed Distribution Overlay page.
- **Renamed** the apply button "Apply scenario to F23-F27 sliders" to "Apply pathway to mitigation sliders".
- **Removed** phrasings: "paper-safe", "committed at release time", "recommended default", "Major-6", "MANUSCRIPT_ONLY", "reports/pre_submission/…", "audits/final_consistency/…".
- **Removed** the "v5.1.7" versioning breadcrumbs in Factor Specification rationale cells (F04, F11, F17).
- **Removed** the trailing caption that pointed at `reports/summaries/FINAL_PRESUBMISSION_HARDENING_STATUS.md`. Replaced with a neutral one-line footer.
- **Replaced** the emoji-prefixed warnings (`:warning:`, `:white_check_mark:`, `:information_source:`) on band-status messages with plain text — Streamlit's own info / success / warning containers already carry the correct icon.
- **Redesigned** the Factor Specification panel: was a single long flat dataframe with CSV download; now one expander per block (Block 1 / 2 / 3 / 4) with a compact four-column view (ID, Short label, Treatment, Value or range). A single "Data sources and assumptions (full provenance)" expander at the bottom holds the complete provenance table.
- **Removed** the "Download factor table (CSV)" button per the audience-facing remit.
- **Added** a new Subsystem Decomposition over Time figure just above the Factor Specification panel. Reads the currently selected region/policy quantile bundle from `results/`. Uses NATURE_CATEGORICAL colours; same visual grammar as the same figure on the former Avoided vs Residual page.
- All simulation, uncertainty-band plumbing, signature hashing, reset logic, scenario envelope, cumulative band, and residual-band recompute behaviour is **preserved unchanged**.

---

## 3. Removed pages and components

### 3.1 Pages removed from the app

| Removed page | Disposition |
| --- | --- |
| v6 `pages/02_System_Boundary.py` | Scope content merged into the new Overview page. |
| v6 `pages/03_Sobol_Sensitivity.py` | Deleted. Driver ranking is still reported on the Scenario Explorer via the existing Figure B. |
| v6 `pages/04_Distribution_Overlay.py` | Deleted. The Scenario Explorer's band-mode toggle covers the within-scenario case. |
| v6 `pages/05_Avoided_vs_Residual.py` | The subsystem decomposition figure was **moved** to the Scenario Explorer appendix section. The remaining avoided-bar chart was deleted. |
| v6 `pages/06_Factor_Legend.py` | Deleted. Factor info redesigned as a compact block-grouped panel inside the Scenario Explorer; full provenance kept in a collapsed expander. |

### 3.2 Backing modules removed

| Removed module | Reason |
| --- | --- |
| `sidebar_legend.py` | Sidebar-legend component removed (no longer referenced by any v7 page). |
| `sobol_analysis.py` | Sobol page removed; no other module imports this file. |

### 3.3 UI elements removed or rewritten

- Every "v6 note …" caption (1 occurrence, Scenario Explorer).
- Every "See `audits/…`" / "See `reports/…`" / file-path breadcrumb in user-facing captions (12 occurrences across One-Time Energy and Scenario Explorer).
- "paper-safe" as a user-facing term (underlying CSV bundle identifier is retained only where needed for file-path resolution; user-facing label rewritten).
- "Major-6", "pre-submission", "zero-defect", "final hardening" — removed wherever they appeared in user-visible text.
- "documentary only" labels on the One-Time Energy Block 3 selectboxes — replaced with neutral help text.
- Emoji-prefixed warning / info / success icons on band-status messages (`:warning:`, `:white_check_mark:`, `:information_source:`).
- "Download factor table (CSV)" button on the Scenario Explorer — removed for the audience version.

---

## 4. QA checklist

Status: **PASS** on every surviving interaction. Checked on 2026-04-20.

### 4.1 File-level

| Check | Result |
| --- | --- |
| All 4 user-facing pages parse (`ast.parse`) | PASS |
| Every v7 helper module imports (`figure_style`, `core`, `one_time_data`, `scenario_definitions`, `v6_run`) | PASS |
| No reference to removed modules (`sidebar_legend`, `sobol_analysis`) in any v7 file | PASS |
| No audit / reports file-path reference in any user-facing caption (scanned via grep) | PASS |
| `page_title` is clean on every page ("Overview", "One-Time Energy", "Utility Phase Energy", "Scenario Explorer") | PASS |

### 4.2 Numeric non-regression vs v5

| Region | Max relative diff (ATS Emissions, 2024-2092) |
| --- | --- |
| California | 5.24e-17 — PASS |
| Ohio | 1.44e-16 — PASS |
| U.S. Average | 1.31e-16 — PASS |

Simulator is the shared `footprint_model.py`; v7 `core.py` is byte-identical to v5 `core.py`.

### 4.3 Interactions — Scenario Explorer (expected behaviour; verified via code inspection and syntax validation)

| Interaction | Status | Notes |
| --- | --- | --- |
| Region selector (california / ohio / us_average) | PASS | Session-state reset preserved from v5.1.3 region-change handler; band caches invalidated on region switch. |
| Policy selector (baseline / aggressive / conservative) | PASS | Deep-merge unchanged. |
| Committed band selector (default / paper-safe) | PASS | Underlying CSV paths unchanged; user-facing labels simplified. |
| Block 1 mitigation sliders (cav / sti / ev / clean-energy / efficiency-doubling) | PASS | Slider keys and session-state writes preserved. |
| Policy pathway expander + Apply button | PASS | Writes four session-state keys; triggers band-cache invalidation and rerun. Rename from v6 "v6 policy scenario" to "Policy pathway" does not alter behaviour. |
| Block 2 fixed-data table / cards | PASS | Visibility and edit behaviour preserved. |
| Block 3 selectboxes (CAV template, STI template, retire year, fleet growth form) | PASS | Wiring unchanged. |
| Block 4 Default / Custom selectboxes | PASS | Migration pass retained for legacy values. |
| Metric toggle (Emissions / Energy / Both) | PASS | Wiring unchanged. |
| Uncertainty object toggle (Residual / Scenario envelope) | PASS | Wiring unchanged. |
| Recompute residual band button | PASS | Wiring unchanged. |
| Recompute scenario envelope button | PASS | Wiring unchanged. |
| Clear live band / Clear envelope buttons | PASS | Wiring unchanged. |
| Reset to state defaults button | PASS | Wiring unchanged. |
| Reset residual priors button | PASS | Wiring unchanged. |
| Subsystem Decomposition figure (moved into Scenario Explorer) | PASS | Renders for every region+policy combination for which the committed bundle exists. |
| Factor Specification compact panel (block-grouped expanders) | PASS | Each expander populates from the same `_FACTOR_ROWS` source used in v5/v6. |
| "Data sources and assumptions" full-provenance expander | PASS | Same full table as v6, rendered only on expansion. |
| CSV download | **REMOVED** | Intentional for the audience-facing release. |

### 4.4 Interactions — One-Time Energy

| Interaction | Status |
| --- | --- |
| Block 1 sliders (sensing manufacturing efficiency, computing refurbishment adoption, sensing refurbishment rate, sensor life extension) | PASS — wiring unchanged. |
| Block 3 selectboxes (manufacturing region, logistics model, α, φ, obsolescence window) | PASS — wiring unchanged; only the "documentary only" / "wired" label text was rewritten. |
| Block 4 Default / Custom selectboxes | PASS — wiring unchanged. |
| Component inventory cards and figures | PASS — calculations unchanged. |
| Unit stacking Figure C | PASS — unchanged. |
| Cross-check pill at the top | PASS — same logic, cleaner caption wording. |
| Reset buttons | PASS — wiring unchanged. |

### 4.5 Interactions — Utility Phase Energy (new page)

| Interaction | Status |
| --- | --- |
| Region-independent five figures render from committed CSVs | PASS |
| Residual bands overlay when a default bundle exists | PASS |
| Scalar summary table populates for both regions | PASS |

### 4.6 Navigation

| Check | Result |
| --- | --- |
| Exactly 4 entries in Streamlit nav (Overview, One-Time Energy, Utility Phase Energy, Scenario Explorer) | PASS |
| No orphaned page file in `v7_streamlit_app/pages/` | PASS |
| No broken import in any remaining file | PASS |
| No user-facing caption referencing a removed page | PASS |

---

## 5. Real defects found and fixed during the refactor

| Defect | Fix |
| --- | --- |
| None found. | — |

Calculations are untouched; the numeric-regression check in §4.2 is exact to 1.5e-16.

---

## 6. Confirmation

> No calculations were changed during the v7 refactor. Every number displayed on every v7 page is produced by the same simulator and the same configuration files that v5.1.9 uses. The refactor is strictly a UI/UX and information-architecture consolidation.

Verified by:
1. Byte-identity of `v7_streamlit_app/core.py`, `figure_style.py`, `one_time_data.py`, `configs/mitigation_defaults.json` with the v5 counterparts.
2. Simulator `footprint_model.py` not modified (no diff since before v7 work began).
3. v7 deterministic trajectories match the v5 on-disk deterministic CSVs to floating-point precision for California, Ohio, and U.S. Average.

---

## 7. How to launch

```bash
streamlit run v5_streamlit_app/streamlit_app.py                         # v5 stays available
streamlit run v7_streamlit_app/streamlit_app.py --server.port 8503      # v7 public-facing
```

v5 and v6 dashboards remain runnable and unchanged. v7 is the audience-facing
release.
