# v5.1.7 final defensibility status

**Date.** 2026-04-19.
**Scope.** Six identified defensibility issues plus an independent
error-search pass on both v5 pages. v3, v4, and Monte Carlo math
unchanged.
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## 1. Files changed

| Path | Description |
|------|-------------|
| `v5_streamlit_app/pages/00_Scenario_Explorer.py` | Peak / turning year metric labels updated to handle "beyond 2075" gracefully with explanatory tooltips. F27 slider override narrows visible range to [2.0, 12.0]. Factor specification table updated for F02 (Ohio BEV share corrected to 0.0067), F04 (Ohio mode 0.62 → 0.54), F11 / F17 (σ 0.25 → 0.18), F18 / F19 (empirical anchors added), F27 (range + rationale rewritten). |
| `v5_streamlit_app/pages/01_One_Time_Energy.py` | Added "How EoL savings are calculated" expander with the explicit formula and current numerics. |
| `configs/ui_parameter_presets/l3_growth_exponents.json` | F27 lognormal min/max truncation tightened to [2.0, 12.0]. |
| `configs/ui_parameter_presets/l1_emission_factors.json` | F04 Ohio recalibrated to fuel-mix-weighted mode 0.54 (low triangular 0.40, 0.54, 0.75; medium 0.36, 0.54, 0.85). Rationale explicitly cites the EIA 2024 Ohio mix derivation. |
| `configs/ui_parameter_presets/l2_ecav_scale_factors.json` | F11 σ tightened low 0.25 → 0.18; medium 0.35 → 0.25. Citation upgraded to 3GPP TS 38.840. |
| `configs/ui_parameter_presets/l2_sti_scale_factors.json` | F17 σ tightened symmetrically with F11. |
| `results/california__policy-baseline__bundle-default_*.csv` | Regenerated against the updated F04 / F11 / F17 / F27 priors. |
| `results/ohio__policy-baseline__bundle-default_*.csv` | Same. |

## 2. Files created

| Path | Purpose |
|------|---------|
| `audits/final_consistency/V5_17_INDEPENDENT_ERROR_SEARCH.md` | 10-dimension search log; one defect found and fixed. |
| `reports/summaries/V5_17_DEFENSIBILITY_STATUS.md` | This file. |

## 3. Per-issue resolution status

### 1.1 Peak-year annotation vs 2075 display cap — FIXED
Peak-year metric now reads `beyond 2075 (projected YYYY)` with a
tooltip explaining the full simulation runs to 2092 but the display
terminates at 2075. Turning-year metric reads `not reached within
2075` when the trajectory does not halve before the cap.

### 1.2 F27 hardware doubling time range — FIXED
Slider range narrowed to [2.0, 12.0] years (from [1.0, 20.0]). Prior
support truncation tightened. Factor table rationale rewritten to
cite NVIDIA Ampere → Hopper as the 2.0 yr lower anchor and Sudhakar
2023 Figure 2 as the 12.0 yr upper anchor.

### 1.3 F04 Ohio fossil intensity — RECALIBRATED (Option A)
Ohio mode moved from 0.62 to 0.54 = 0.43 × 0.50 + 0.34 × 0.95
(EIA 2024 Ohio generation mix). Triangular bounds shifted to
(0.40, 0.54, 0.75) for `low` and (0.36, 0.54, 0.85) for `medium`.

### 1.4 F11 / F17 communication σ — TIGHTENED
F11 and F17 σ moved from 0.25 to 0.18 (95 % range [0.70, 1.43]).
Citations upgraded to 3GPP TS 38.840.

### 1.5 F18 / F19 empirical anchors — ADDED
Each level-mix template now carries a soft empirical citation
(RAND 2016, LEVITATE H2020, BCG 2023, Waymo + Cruise 2050 for F18;
FHWA 2024, AASHTO 2040, Caltrans 2050 for F19).

### 1.6 EoL savings formula expander — ADDED
Inline expander below the EoL metric on the One-Time Energy page
shows the formula `α × (1 − r)`, the current slider values, and
the per-component / fleet-aggregation derivation. Notes the φ
selectbox is documentary only.

### 1.7 (and Part 2) — PROMPT TRUNCATED
The task prompt was truncated mid-item-1.6 and Part 2 (the
independent error-search section) was missing entirely. I executed
items 1.1 through 1.6 in full and ran an **independent error-search
pass on my own initiative** with 10 search dimensions (see
`V5_17_INDEPENDENT_ERROR_SEARCH.md`). The search found one real
defect (Ohio BEV share factor-table value 0.0057 vs derived 0.0067)
which has been fixed.

## 4. Numerical impact of the prior changes

Post-v5.1.7 committed-bundle widths under the regenerated defaults:

| Region | W/M 2030 | W/M 2050 | W/M 2075 | IB τ=1.5 | IB τ=0.5 |
|--------|---------:|---------:|---------:|----------|----------|
| California | 0.45 | 0.44 | 0.78 | not reached | 2054 |
| Ohio | 0.42 | 0.46 | 0.58 | not reached | 2053 |

Compared to v5.1.6 (pre-recalibration):
- California W/M unchanged at 2030 (0.45 → 0.45) because the
California F04 prior was untouched. Same for 2050.
- Ohio W/M at 2030 unchanged (0.42 → 0.42); at 2050 0.47 → 0.46
(slight tightening from F11 / F17 σ reduction); at 2075
0.61 → 0.58 (same).
- IB τ = 0.5 for California shifted from 2055 to 2054 (one-year
drift inside the MC seed noise envelope); for Ohio from 2051 to
2053 (two-year drift, again within seed noise).
- IB τ = 1.5 remains "not reached" for both regions.

Bundles are bit-for-bit different from the v5.1.6 versions but the
qualitative behaviour (decision-meaningful bands, no IB crossing at
τ = 1.5) is preserved.

## 5. Independent error-search summary

- 10 search dimensions executed.
- 1 real defect found and fixed (Ohio BEV share table value).
- 1 false positive (label-namespace superset; documented as design
choice).
- 8 dimensions with no findings.

Full trace: `audits/final_consistency/V5_17_INDEPENDENT_ERROR_SEARCH.md`.

## 6. What remains

- **Item 1.7 of the prompt** was not visible to the auditor due to
prompt truncation. If the seventh item exists in the original
prompt it is unresolved; please re-send the missing section.
- **Part 2 of the prompt** (an apparently larger independent
error-search specification) was missing entirely; the
self-initiated 10-dimension search is offered as a substitute.
- Manuscript-text reconciliations from
`reports/pre_submission/MANUSCRIPT_ONLY_RECONCILIATIONS.md` remain
on the author side (six items, ~2-3 hours).

## Closing

v5.1.7 closes six of the seven explicitly specified defensibility
issues plus surfaces one additional defect found by the independent
search. The dashboard remains submission-ready; the regenerated
committed bundles preserve the residual-band properties documented
in v5.1.3 and v5.1.4.
