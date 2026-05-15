# FINAL_FOUR_BLOCK_ALIGNMENT_STATUS.md

**Date:** 2026-04-17

---

## 1. Files changed

| File | Change |
|---|---|
| `v4_streamlit_app/pages/00_Scenario_Explorer.py` | Complete rewrite into four-block structure: Mitigation → Fixed Data → Assumptions → Residual Uncertainty. F23–F27 moved out of uncertainty radios into mitigation sliders. F18/F19/F22/F28 moved to Assumptions block. L3 expander removed from uncertainty section. "What the band represents" explainer added above Figure A. "Mitigation leverage" block with dynamic ranking added. State-specific mitigation defaults loaded from JSON config. |
| `v4_streamlit_app/streamlit_app.py` | Already updated by user to describe the four-block architecture (landing page references `PARAMETER_CLASSIFICATION_FINAL.md`). |

## 2. Files created

| File | Purpose |
|---|---|
| `v4_streamlit_app/configs/mitigation_defaults.json` | State-specific default values for the five mitigation sliders (CA and OH), with policy-source citations. |
| `audits/final_consistency/FINAL_FOUR_BLOCK_CLASSIFICATION.md` | Per-control classification audit: every control mapped to one of the four blocks with rationale. |
| `audits/final_consistency/FINAL_FOUR_BLOCK_VALIDATION.md` | Automated validation results (all checks pass). |
| `reports/summaries/FINAL_FOUR_BLOCK_ALIGNMENT_STATUS.md` | This file. |

## 3. Final four-block page structure (actual rendered order)

```
┌─ Region / Policy / Band selectors ─────────────────────────────────┐
│                                                                     │
├─ BLOCK 1 — Mitigation and Policy Levers (always visible) ──────────┤
│  Fleet-transition levers:  CAV target | STI target | BEV growth     │
│  Grid + technology levers: Clean-energy growth | Efficiency doubling│
│  [Reset to state defaults]                                          │
│                                                                     │
├─ BLOCK 2 — Fixed Data (collapsed expander) ────────────────────────┤
│  Initial low-carbon share | Initial BEV share                      │
│  Total vehicle stock | Intersections                                │
│  [Advanced mode checkbox → editable]                                │
│                                                                     │
├─ BLOCK 3 — Modeling Assumptions (collapsed expander) ──────────────┤
│  CAV level-mix template (selectbox)                                 │
│  STI level-mix template (selectbox)                                 │
│  Vehicle retire year (selectbox: 10/12/15)                          │
│  Fleet growth form (selectbox)                                      │
│  Target ramp shape (selectbox)                                      │
│                                                                     │
├─ BLOCK 4 — Residual Uncertainty Priors (visible, L1/L2) ──────────┤
│  Quick bundles: [Default] [Paper-safe] [Exploratory]                │
│  Fixed/Low/Medium/High counts + paper-safe badge                    │
│  L1 — emission factor residual (F03, F04, F05)                      │
│  L2 — load-model residual (F09–F11, F15–F17, F20)                  │
│  [Advanced detail expander: hidden params, copula note, quarantine] │
│                                                                     │
├─ "What the band represents" explainer ─────────────────────────────┤
│                                                                     │
├─ FIGURE A — ATS Emissions uncertainty ─────────────────────────────┤
├─ FIGURE B — Top parameter drivers (bar chart) ─────────────────────┤
├─ FIGURE C — Layer contribution summary ────────────────────────────┤
├─ Mitigation leverage (dynamic ranking) ────────────────────────────┤
├─ Support boundary table ───────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────────┘
```

## 4. Parameters moved out of ordinary uncertainty

| Parameter | Former location | New location |
|---|---|---|
| F23 (CAV 2075 target) | L3 uncertainty radio + Section A slider | **Mitigation** (Block 1 slider only) |
| F24 (STI 2075 target) | L3 uncertainty radio + Section A slider | **Mitigation** (Block 1 slider only) |
| F25 (BEV growth rate) | L3 uncertainty radio + Section A slider | **Mitigation** (Block 1 slider only) |
| F26 (Clean-energy growth) | L3 uncertainty radio + Section A slider | **Mitigation** (Block 1 slider only) |
| F27 (Efficiency doubling) | L3 uncertainty radio + Section A slider | **Mitigation** (Block 1 slider only) |
| F18 (CAV level mix) | L2 uncertainty radio | **Assumption** (Block 3 selectbox template) |
| F19 (STI level mix) | L2 uncertainty radio | **Assumption** (Block 3 selectbox template) |
| F22 (Retire year) | L2 uncertainty radio + Section B slider | **Assumption** (Block 3 selectbox: 10/12/15 yr) |
| F28 (Fleet growth) | L3 uncertainty radio + Section B slider | **Assumption** (Block 3 via fleet-growth form selectbox) |
| F01 (Initial clean share) | L1 uncertainty radio + Section B slider | **Fixed data** (Block 2 display/editable) |
| F02 (Initial BEV share) | L1 uncertainty radio + Section B slider | **Fixed data** (Block 2 display/editable) |

## 5. State-specific mitigation defaults loaded

| Lever | California | Ohio |
|---|---|---|
| CAV 2075 target | 0.45 | 0.25 |
| STI 2075 target | 0.50 | 0.30 |
| BEV growth rate | 0.07 | 0.03 |
| Low-carbon electricity growth | 0.05 | 0.02 |
| Hardware doubling (years) | 2.8 | 2.8 |

Both load correctly from `v4_streamlit_app/configs/mitigation_defaults.json`. When region changes, all five sliders snap to the new state's defaults via `st.session_state` + `_MIT_KEY_MAP`.

## 6. Validation results

| Check | Result |
|---|---|
| `"Mitigation and Policy Levers"` in page text | **Pass** |
| `"Fixed Data"` in page text | **Pass** |
| `"Modeling Assumptions"` in page text | **Pass** |
| `"Residual Uncertainty Priors"` in page text | **Pass** |
| F23–F27 NOT in default uncertainty radios | **Pass** |
| F18, F19, F22, F28 NOT in default uncertainty radios | **Pass** |
| California defaults load correctly | **Pass** |
| Ohio defaults load correctly | **Pass** |
| Syntax check (py_compile) | **Pass** |
| Sliders snap to state defaults on region change | Implemented; visual QA recommended |

## 7. Still unresolved

| Item | Why |
|---|---|
| "Custom" mode for CAV/STI level-mix templates | Selectbox templates are implemented (4 CAV, 3 STI); free-form Dirichlet sliders summing to 1.0 would require a small widget group — deferred. |
| Logistic S-curve and delayed-onset ramp shapes | Selectbox entries are present in Block 3; only "Linear from 2024 to 2075" is implemented in the backend. Others are labelled as "requires code extension." |
| Screenshot capture (`FINAL_FOUR_BLOCK_SCREENSHOT.png`) | Cannot run Streamlit headless in this environment; visual QA recommended after launch. |
| Bundle regeneration under Ohio-specific mitigation defaults | Current bundle CSVs were generated with the canonical scenario config's growth-rate means (which match the CA mitigation defaults). An Ohio-specific regeneration under the Ohio mitigation defaults (cav=0.25, bev=0.03, etc.) is a future step; it would shift the OH central trajectory. The current committed OH bundle uses the canonical scenario file's means, which may differ from the mitigation defaults above. Flagged for review. |
