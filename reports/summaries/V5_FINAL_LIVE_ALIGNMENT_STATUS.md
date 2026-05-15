# V5 final live-alignment status

**Date.** 2026-04-17.
**Scope.** `v5_streamlit_app/pages/00_Scenario_Explorer.py` (single Scenario
Explorer page) plus the supporting `core.py` and `figure_style.py`.
**v3 and v4 remain untouched.**
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## 1. Mitigation sliders behave live in a scientifically clear way

- Moving any Block 1 slider triggers an immediate Streamlit rerun.
- The live deterministic trajectory (solid red line in Figure A) updates
within one rerun.
- The committed residual band does not silently re-centre. It is
explicitly labelled as one of three states:
  - **committed**: all settings at state defaults.
  - **stale**: any Block 1 slider, Block 3 template, or Block 4 radio is
off-default and the live band has not been requested.
  - **live**: the reader has clicked Recompute residual band and a stored
live MC is in session state.
- Moving Block 4 radios invalidates any stored live band so the page
never shows a cached live band that does not match the new radio
state.

Source: `audits/final_consistency/V5_REACTIVITY_AND_BAND_STATUS_AUDIT.md`.

## 2. Figure A no longer misleads users about live vs committed uncertainty

- A status pill sits above Figure A:
  - green check: live band.
  - blue info: committed band matches current settings.
  - amber warning: committed band does NOT match current settings.
- Band legend name toggles between "Committed p05 to p95 band" and
"Live p05 to p95 band".
- Median line toggles between a dotted committed median and a solid
live median.
- Figure caption states sample count, timestamp, and settings bound.
- "Recompute residual band" button and "Clear live band" button sit
immediately next to the status pill.

Source: `audits/final_consistency/V5_REACTIVITY_AND_BAND_STATUS_AUDIT.md`.

## 3. Figure B and Figure C match the final residual-only semantics

- Figure B shows 10 residual parameters only (F03, F04, F05, F09–F11,
F15–F17, F20).
- Mitigation levers (F23–F27), assumption parameters (F18, F19, F22,
F28), fixed-data anchors (F01, F02), and hidden duplicates (F06–F08,
F12–F14, F21) are filtered out.
- Figure C defaults to L1 and L2 only. L3 is available behind an opt-in
toggle that documents it as the mitigation-lever layer rather than
residual uncertainty.
- The Mitigation leverage block reads from the same residual-only
DataFrame, so the top-driver callouts in the leverage block always
match Figure B.

Source: `audits/final_consistency/V5_RESIDUAL_DRIVER_SEMANTIC_FIX.md`.

## 4. Block 1 / 2 / 3 / 4 meaning is strict

- Block 1 (sidebar): five mitigation levers. Changing these changes the
scenario.
- Block 2 (main-page expander): four fixed-data anchors. Read-only by
default; advanced mode adds sliders for sensitivity checks.
- Block 3 (main-page expander): structural assumptions — CAV template,
STI template, retire year, fleet-growth form. Moving these rewrites
the runtime configuration and changes the deterministic trajectory.
- Block 4 (main-page header): residual uncertainty radios for ten L1
and L2 parameters. Changing these invalidates any stored live band.

Parameters cannot appear in more than one block. The taxonomy is
enforced programmatically by `V5_NON_RESIDUAL_PARAMS` in core.py and
surfaces consistently on the page.

Source: `audits/final_consistency/V5_PARAMETER_CONTROL_SIMPLIFICATION.md`.

## 5. Low / medium controls are only retained where evidence-justified

- **{fixed, low, medium}** retained only on the three L1 emission
factors (F03, F04) where the LOW / MEDIUM distinction reflects a real
methodological choice (operational-only vs life-cycle-inclusive grid
intensity; gas-only vs gas+coal fossil mix).
- **{fixed, low}** everywhere else on the main page.
- MEDIUM was removed from the L2 per-subsystem scale factors (F09–F11,
F15–F17) because MEDIUM was simply a wider sigma without new evidence.

Source: `audits/final_consistency/V5_PARAMETER_CONTROL_SIMPLIFICATION.md`.

## 6. Sidebar-style access is implemented cleanly

- Region, Policy, Committed-band mode, and the five Block 1 mitigation
sliders live in `st.sidebar`.
- `initial_sidebar_state="expanded"` keeps the sidebar visible on first
load.
- Block 2, Block 3, and Block 4 remain in the main panel.
- Figures occupy full main-panel width; no horizontal collision with the
sidebar.

Source: `audits/final_consistency/V5_SIDEBAR_CONTROL_LAYOUT_FIX.md`.

## 7. The page is both academically correct and useful for real-time exploration

- The four-block framework is explicit in copy, controls, and data.
- Band status is never ambiguous.
- Figure B and Figure C match the page's narrative about what Block 4
means.
- The page recomputes a live deterministic line on every interaction
and the live residual band at the click of a button (0.48 s).
- All user-visible prose follows Nature editorial conventions (no
contractions, acronyms defined on first use, no body-prose em-dashes,
numbers-as-words under 10).

---

## Files changed

| Path | Change |
|------|--------|
| `v5_streamlit_app/pages/00_Scenario_Explorer.py` | Rewritten for sidebar layout, live-band status, filtered figures, simplified radios, provenance-tagged mitigation help. |
| `v5_streamlit_app/core.py` | Added `apply_assumption_templates`, `V5_NON_RESIDUAL_PARAMS`, `V5_ALLOWED_LEVELS`, `v5_allowed_levels`, `v5_default_level`, `v5_parameter_default_choices`, `v5_paper_safe_choices`, `compute_live_residual_band`, `load_parameter_contribution_experiment(residual_only=...)`. |
| `v5_streamlit_app/configs/mitigation_defaults.json` | Ohio CAV target 0.25 → 0.30; Ohio BEV 0.03 → 0.055; Ohio clean-grid 0.02 → 0.035; provenance tags added to every lever; `_sources` rewritten. |

## Files created

| Path | Purpose |
|------|---------|
| `audits/final_consistency/V5_REACTIVITY_AND_BAND_STATUS_AUDIT.md` | Part 1. Three-state band model. |
| `audits/final_consistency/V5_RESIDUAL_DRIVER_SEMANTIC_FIX.md` | Part 2. Residual-only filter + excluded parameter list. |
| `audits/final_consistency/V5_PARAMETER_CONTROL_SIMPLIFICATION.md` | Part 3. Per-parameter decision log. |
| `audits/final_consistency/V5_MITIGATION_DEFAULT_PROVENANCE_FIX.md` | Part 4. Provenance tags per lever, defaults updated. |
| `audits/final_consistency/V5_SIDEBAR_CONTROL_LAYOUT_FIX.md` | Part 5. Sidebar layout description. |
| `audits/final_consistency/V5_RESIDUAL_WIDTH_REASSESSMENT.md` | Part 6. W/M comparison across three configurations. |
| `audits/final_consistency/V5_PAGE_COPY_FINAL_ALIGNMENT.md` | Part 7. Final copy pass and editorial rules applied. |
| `reports/summaries/V5_FINAL_LIVE_ALIGNMENT_STATUS.md` | Part 8. This file. |
| `scripts/v5_residual_width_reassessment.py` | Harness for Part 6. |

## Band status

**The band is live-capable.** The committed band remains available as a
fast default. A status pill above Figure A always tells the reader
whether the band is committed, stale, or live. A button next to the
pill recomputes the band (≈0.48 s for 80 samples, ≈1.2 s for 200).

## Figure B / C semantics

**Residual-only.** Mitigation levers, assumption parameters, fixed-data
anchors, and hidden duplicates are filtered out. Ten residual
parameters remain, distributed across L1 and L2. Figure C defaults to
L1 + L2; L3 is available behind an opt-in toggle.

## Parameters that still have low / medium

| Param | Why |
|-------|-----|
| F03 (CO₂ intensity of low-carbon generation) | LOW trims the life-cycle tail (0.02–0.05). MEDIUM retains the life-cycle tail (0.01–0.08). A real methodological choice. |
| F04 (CO₂ intensity of fossil generation) | LOW is region-specific (CA gas-only vs OH coal+gas). MEDIUM widens the upper tail further. Regional defaults differ substantively. |

Every other main-page radio is {fixed, low}.

## Parameters moved out of ordinary uncertainty

| Param | Where it lives now |
|-------|--------------------|
| F23, F24, F25, F26, F27 | Block 1 (sidebar sliders). |
| F18, F19 | Block 3 (level-mix templates in main-page expander). |
| F22 | Block 3 (vehicle service-life selectbox). |
| F28 | Block 3 (fleet-growth-form selectbox). |
| F01, F02 | Block 2 (fixed-data table; editable only in advanced mode). |
| F06, F07, F08, F12, F13, F14, F21 | Hidden. Fixed at identity or vanishing effect. |

## Decision-meaningful uncertainty

W/M under the v5.1 corrected default (L3 fixed, assumption parameters
fixed, residual L1 and L2 at "low"):

| Region | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|--------|---------:|---------:|---------:|--------:|
| California | 0.46 | 0.48 | 0.76 | not reached within horizon |
| Ohio | 0.42 | 0.52 | 0.64 | not reached within horizon |

Both regions clear the W/M < 1 threshold at every reported horizon.
The band is decision-meaningful through 2075 without any arbitrary
tightening of priors.

Source: `audits/final_consistency/V5_RESIDUAL_WIDTH_REASSESSMENT.md`.

## What still remains unresolved

1. **Rebuttal text update.** The rebuttal letter still cites California
IB = 2030 and Ohio IB = 2031. Under the v5.1 corrected defaults, the
IB is not reached within the 2024–2092 horizon. The rebuttal must be
updated to reflect the new values. Data is correct; text is stale.
Cross-reference: `audits/final_consistency/REBUTTAL_NUMBER_CROSSCHECK.md`.
2. **L3 reader-opt-in in Figure C** is simple but requires a reader to
enable it. Document clearly in the manuscript methods section that
"Figure C on the dashboard shows L1 + L2 only by default because L3
is a Block 1 concern."
3. **Paper-safe committed bundles** have not yet been regenerated
against the v5.1 simplified allowed-level set. The live-MC recompute
button produces the correct v5.1 band on demand, but the committed
bundle still reflects the earlier (looser) paper-safe choices. If a
paper-safe reproducibility claim depends on the committed bundle,
regenerate it via `scripts/regenerate_default_bundle_quantiles.py`
with the v5.1 `v5_paper_safe_choices()` input.
