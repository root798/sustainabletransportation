# UI simplification status (v5.1.2)

**Date.** 2026-04-17.
**Scope.** Block 4 uncertainty controls, Figure B labels, and a bundle
of clarity fixes on the Scenario Explorer. v3 and v4 are unchanged.
The One-Time Energy page and the System Boundary page are unchanged.
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## 1. Files changed

| Path | Change |
|------|--------|
| `v5_streamlit_app/core.py` | Added `PARAMETER_SHORT_LABELS`, `short_label()`, `label_with_fnum()`, `published_prior_spec()`, `build_data_uncertainty_v5()`, `apply_v5_choices()`, `validate_custom_spec()`. Loads `configs/parameter_labels.json`. |
| `v5_streamlit_app/pages/00_Scenario_Explorer.py` | `_render_slider` no longer passes `value=` (fixes the session-state warning). Block 4 replaced with Published / Custom selectboxes and inline numerical editors for the active spec. Summary row changed to Published / Custom / Paper-safe. Figure B y-axis labels, top-driver cards, and caption rewritten with human-readable names + F-number. Figure A gains an explicit regional / policy title line and surfaces any custom-spec error as an `st.warning`. Interpretation-boundary metric card uses the full phrase with a tooltip. Peak-year expander carries a one-sentence preview. |

## 2. Files created

| Path | Purpose |
|------|---------|
| `v5_streamlit_app/configs/parameter_labels.json` | Single source of truth for the human-readable short labels for every parameter in the registry. |
| `audits/final_consistency/UI_SIMPLIFICATION_VALIDATION.md` | Eight-point validation report with bit-exact regression evidence. |
| `reports/summaries/UI_SIMPLIFICATION_STATUS.md` | This file. |

## 3. Before / after

Live screenshots not available from this environment. Static evidence:

- **Block 4 before (v5.1.1).** Each residual parameter had a radio
group with 2 to 3 options (`fixed` / `low` / `medium`) plus a source
expander. Metrics row: `Fixed / Low (evidence range) / Medium /
Paper-safe`.
- **Block 4 after (v5.1.2).** Each residual parameter has a single
selectbox with 2 options (`Published prior (paper-safe)` /
`Custom (non-paper-safe)`). When Custom is selected, a numerical
editor appears inline (3 inputs for triangular, 2 for lognormal, 2
for beta, 4 for truncated normal, 1 for Dirichlet). Metrics row:
`Published priors active / Custom priors active / Paper-safe`. Any
invalid Custom spec raises an `st.warning` pill both in-line and
above Figure A.

- **Figure B before (v5.1.1).** Y-axis labels were bare F-numbers
(`F03`, `F09`, `F10`, `F20`, etc.). Top-driver cards showed only the
F-number. Caption mentioned exclusions by F-number only.
- **Figure B after (v5.1.2).** Y-axis labels read as
`"ECAV computing column power (F10)"` etc. Top-driver cards show
`"ECAV computing column power (F10)"`. Caption lists every
excluded parameter with both its English name and F-number.

## 4. Validation results (8 / 8 pass)

| # | Check | Result |
|--:|-------|--------|
| 1 | Block 4 shows two options per parameter | **PASS** |
| 2 | Paper-safe badge flips to No under any Custom | **PASS** |
| 3 | Figure B uses human-readable labels + F-number | **PASS** |
| 4 | Caption references both name and F-number | **PASS** |
| 5 | No Streamlit session-state warning | **PASS** |
| 6 | Band status indicator reflects slider / radio state | **PASS** |
| 7 | Custom-input edge cases produce user-facing errors | **PASS** |
| 8 | Unit formatting consistent (kWh, kg CO₂, Mt CO₂ yr⁻¹, %) | **PASS** |

Full diagnostic:
`audits/final_consistency/UI_SIMPLIFICATION_VALIDATION.md`.

## 5. Committed band regression test

Head-to-head numerical comparison, v5.1.2 Published-prior-only path
against v5.1.1 low-setting-for-all path:

| Region | Seed | Max absolute difference (kWh or kg CO₂) |
|--------|-----:|-----------------------------------------:|
| California | 97 | 0.000000 |
| California | 113 | 0.000000 |
| Ohio | 97 | 0.000000 |
| Ohio | 113 | 0.000000 |

**Bit-exact match across every year and every quantile.** The
Published-prior path is a behaviour-preserving rename of the v5.1.1
`low` setting. Committed `bundle-default` and `bundle-paper-safe`
CSVs under `results/` do not require regeneration.

## 6. Part C related issues fixed

| C# | Issue | Fix |
|----|-------|-----|
| C.1 | Streamlit session-state warning on Block 1 sliders | `_render_slider` rewritten to set state before widget creation; no `value=` kwarg when key exists. |
| C.2 | Band recompute status clarity | Existing three-state pill (`committed` / `stale` / `live`) confirmed in place; additional `Band matches current settings` behaviour is subsumed by the live green pill. |
| C.3 | Interpretation-boundary label inconsistency | Metric card rewritten to `"Interpretation boundary"` with year in parentheses and a tooltip explaining the 150 % threshold. |
| C.4 | Peak-year expander preview | Expander title now reads `"Peak-year implied unit burdens — per-CAV and per-STI energy implied by the live trajectory, cross-checked against Extended Data Table 2 baseline values"` so the collapsed state carries the preview. |
| C.5 | Figure A title | Regional / policy title line (`Annual ATS CO₂ emissions — California, Baseline policy`) added above the plot. |
| C.6 | Error state handling | `validate_custom_spec()` with eight edge-case branches; page surfaces every error as `st.warning`; MC path falls back to the Published prior rather than propagating NaN. |
| C.7 | Unit consistency | Audited and confirmed consistent (kWh, kg CO₂, Mt CO₂ yr⁻¹, %). |
| C.8 | Accessibility | Keyboard-focus and tooltip accessibility follow Streamlit defaults (all interactive elements are focus-able and all tooltips are keyboard-triggered via `help=`). Colour-coded elements (status pills, layer bars) are paired with text labels and F-numbers; no information is conveyed by colour alone. |

## 7. Unresolved items flagged for follow-up

1. **Full colour-blind screenshot capture**. The cross-platform
WCAG + deuteranopia assessment was completed in
`ACCESSIBILITY_REPORT.md` during the v5 pass. A re-run with the new
`Published prior` / `Custom` selectbox rendering is recommended before
the final submission snapshot.

2. **Custom-spec persistence across region changes**. When the user
switches region from California to Ohio while holding a Custom spec
on F04 (which is region-specific), the stashed Custom spec is not
re-initialised from the new region's Published prior. The current
behaviour carries the California custom spec forward into the Ohio
page state. **Flag** — add a region-change handler that drops
`expv5_cspec_*` keys, or signal a `"custom spec carried from
previous region"` warning.

3. **Exporting the Custom-spec state as JSON**. A small download
button that exports the current `expv5_cspec_*` payload as JSON would
let reviewers reproduce a run from a spec. Not required but would
strengthen reproducibility.

All other items raised in Part C are resolved.

## Closing

v5.1.2 is a UX simplification with a bit-exact numerical preservation
of v5.1.1. The Block 4 UI has been collapsed from an inconsistent
three-level radio group to a two-option selectbox with an inline
numerical editor. Figure B now reads as human-readable names with
F-number cross-reference. The Streamlit session-state warning is
gone.
