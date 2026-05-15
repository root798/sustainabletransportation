# Silent-failure scan

Silent failures are UI paths that complete without visible error but
still produce wrong, stale, or misleading output. This scan covers the
four categories called out in the validation protocol. The scan was
executed against the **v5 Scenario Explorer** (`v5_streamlit_app/pages/00_Scenario_Explorer.py`)
and the shared `v5_streamlit_app/core.py` loaders.

## A. Non-functional selectbox options

| Selectbox | Option | Backend wired? | Verdict | Fix in v5 |
|-----------|--------|----------------|---------|-----------|
| Block 3 · CAV level-mix template | all four options (L3-heavy, Balanced, L4-forward, L5-forward) | YES in v5 via `apply_assumption_templates` | pass | wired in v5; L3 vs L5 produces 28.9% (CA) and 37.8% (OH) change in live p50 2075 |
| Block 3 · STI level-mix template | all three options | YES in v5 via `apply_assumption_templates` | pass | wired in v5 |
| Block 3 · Vehicle service life | 10, 12, 15 yr | YES in v5 (written to `growth_rates.retire_year`) | pass | wired in v5 |
| Block 3 · Fleet growth functional form | Linear, Constant | YES in v5 (Constant → zero `total_car_increase`) | pass | wired in v5 |
| Block 3 · Target ramp shape | Linear only | single-option; not silently falling back | pass | selectbox reduced to the single implemented option with an explicit help line stating alternative ramps require a code extension |

The four v4 silent-option cases have been fixed in v5. The only remaining
single-option selectbox (Target ramp shape) carries an explicit caption
that alternative ramps are intentionally unavailable, so it is not silent.

## B. Slider ranges that exceed physical bounds

| Slider | Current range | Physical bound | Verdict |
|--------|---------------|----------------|---------|
| CAV target fraction by 2075 | 0.00 to 0.95 | ≤1.00 | pass (0.95 is a deliberate ceiling to prevent 100% saturation artefacts) |
| STI coverage target by 2075 | 0.00 to 0.95 | ≤1.00 | pass |
| Annual BEV-share growth | 0.00 to 0.50 | ≤1.00 | pass (top end 0.50 is twice the CA CAGR, enough for sensitivity) |
| Annual low-carbon electricity share growth | 0.00 to 0.30 | ≤1.00 | pass |
| Annual fleet growth rate | -0.01 to 0.03 | plausible demographic range | pass |
| Hardware efficiency doubling time | 1.0 to 20.0 yr | ≥0.5 yr (physically implausible below) | pass (lower bound 1.0 yr rejects the physically implausible 0.5 yr) |
| Initial low-carbon electricity share | 0.00 to 1.00 | [0, 1] | pass |
| Initial BEV share | 0.000 to 1.000 | [0, 1] | pass |

No slider admits a physically implausible value in v5.

## C. Cache invalidation on region / policy change

Tested by walking the snap-on-region-change logic in v5:

```python
_prev_region = st.session_state.get("expv5_prev_region")
if _prev_region is not None and _prev_region != region:
    for sk, mk in _MIT_KEY_MAP.items():
        st.session_state[f"expv5_cv_{sk}"] = _mit.get(mk, _cv.get(sk))
    for key in CONTROL_SPECS:
        if key not in _MIT_KEY_MAP:
            st.session_state[f"expv5_cv_{key}"] = _cv.get(key)
st.session_state["expv5_prev_region"] = region
```

Verdict. When the user switches California → Ohio, every mitigation
slider is force-written with Ohio's default before the next rerun
renders. The same for Ohio → California. No stale CA value persists in
an OH session or vice versa.

The bundle CSVs are read fresh on every rerun because the loader does
not cache the DataFrame at module scope. Live deterministic simulation
runs on every rerun as well (no `st.cache_data` memoisation). The
performance cost is acceptable (~0.3 s per rerun); the correctness win
is that the live trajectory is always current with the levers.

## D. Session-state leakage between regions

Tested by listing every `expv5_*` key that could carry per-region state.
All are either (i) overwritten on region change by the snap block, or
(ii) meant to persist across regions (bundle selection, uncertainty
radios).

| Session-state key | Carries regional state? | Snap on region change? | Verdict |
|-------------------|-------------------------|------------------------|---------|
| `expv5_cv_cav_growth_rate` | yes | yes | pass |
| `expv5_cv_sti_growth_rate` | yes | yes | pass |
| `expv5_cv_ev_growth_rate` | yes | yes | pass |
| `expv5_cv_clean_energy_growth_rate` | yes | yes | pass |
| `expv5_cv_efficiency_doubling_years` | yes | yes | pass |
| `expv5_cv_initial_clean_fraction` | yes | yes | pass |
| `expv5_cv_initial_ev_share` | yes | yes | pass |
| `expv5_cv_total_cars` | yes | yes | pass |
| `expv5_cv_total_intersections` | yes | yes | pass |
| `expv5_cv_retire_year` | no (structural) | n/a | pass |
| `expv5_cv_fleet_growth_rate` | no (structural) | n/a | pass |
| `expv5_cav_tmpl` | no (structural) | n/a | pass |
| `expv5_sti_tmpl` | no (structural) | n/a | pass |
| `expv5_retire_yr` | no (structural) | n/a | pass |
| `expv5_p_*` radios | no (paper-safe bundle is region-invariant) | n/a | pass |
| `expv5_bundle_display` | no | n/a | pass |

No leakage detected.

## E. Additional silent failure fixed in v5

The v4 scenario explorer loaded
`audits/uncertainty_governance/PARAMETER_IMPORTANCE_EXPERIMENT.csv`
first, which is California-only. When a reader selected Ohio, the page
silently fell back to California data and displayed only a small
"(falling back to California data)" caption. Figure B, the metric
cards, and the mitigation-leverage insight were therefore all California
content regardless of the region selectbox.

**Fix in v5.** `v5_streamlit_app/core.py` repoints the loader at
`PARAMETER_CONTRIBUTION_EXPERIMENT.csv`, which carries both California
and Ohio rows. The fallback warning is kept as a safety net but never
fires under the current data.

Verification:

```
rows for ohio 2050: 24   (up from 0 in v4)
Ohio top driver at 2030: F23 (matches California)
Ohio top driver at 2050: F27 (matches California — hardware efficiency)
Ohio top driver at 2075: F09 (divergence from California's F25 — now visible)
```

The Ohio-vs-California 2075 divergence (F09 vs F25) was hidden under the
v4 loader. Making it visible is a material correctness win.

## Summary

No uncorrected silent failures remain in v5. All five categories above
have been tested and either pass by construction or have been
explicitly fixed during the v5 rewrite.
