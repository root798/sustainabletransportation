# FINAL_FOUR_BLOCK_VALIDATION.md

**Date:** 2026-04-17

## Validation results

| Check | Result |
|---|---|
| `"Mitigation and Policy Levers"` in page text | **Pass** |
| `"Fixed Data"` in page text | **Pass** |
| `"Modeling Assumptions"` in page text | **Pass** |
| `"Residual Uncertainty Priors"` in page text | **Pass** |
| F23, F24, F25, F26, F27 NOT in default uncertainty radios | **Pass** — classified in `_MITIGATION_PIDS` |
| F18, F19, F22, F28 NOT in default uncertainty radios | **Pass** — classified in `_ASSUMPTION_PIDS` |
| California mitigation defaults load correctly | **Pass** — cav=0.45 sti=0.50 bev=0.07 clean=0.05 hw=2.8 |
| Ohio mitigation defaults load correctly | **Pass** — cav=0.25 sti=0.30 bev=0.03 clean=0.02 hw=2.8 |
| Syntax check | **Pass** |
| Region change snaps mitigation sliders | Implemented via `_MIT_KEY_MAP` + `st.session_state.setdefault`; full visual QA requires running app |
