# Fix Log — v4 Streamlit App

## Bug 1: Session-state mutation after widget instantiation (CRITICAL)

**Root cause**: v3 `00_Scenario_Explorer.py` called `update_widget_values()` which writes to `st.session_state[widget_key(key)]` *after* widgets with those keys were already created in the same script run.  Streamlit raises `StreamlitAPIException: st.session_state.explorer_region cannot be modified after the widget with key explorer_region is instantiated`.

**Affected file**: `v3_streamlit_app/pages/00_Scenario_Explorer.py`, lines 58-60 (`update_widget_values`), 146-149 (called during region change).

**Fix**: Complete architectural redesign.  v4 uses:
1. One-time initialisation in `if "exp_init" not in st.session_state:` block *before* any widget.
2. `on_change` callbacks on selectbox widgets — state is mutated only inside callbacks, not in the main script body.
3. No `update_widget_values()` function — each callback writes directly to the correct `st.session_state` keys.

**Validation**: Region switching, policy switching, reset buttons, real-time toggle all work without session-state errors.

## Bug 2: `width="stretch"` parameter (CRITICAL)

**Root cause**: v3 used `width="stretch"` on `st.plotly_chart()`, `st.dataframe()`, `st.button()`, and `st.download_button()` across all pages.  This parameter does not exist in current Streamlit — the correct parameter is `use_container_width=True`.

**Affected files**: ALL v3 pages (40+ occurrences).

**Fix**: v4 uses `use_container_width=True` everywhere.

**Validation**: No `TypeError: unexpected keyword argument` errors.

## Bug 3: Potential IndexError on year lookup

**Root cause**: v3 used `df.loc[df["Year"] == 2030, ...].iloc[0]` without adequate bounds checking.

**Affected file**: `v3_streamlit_app/pages/00_Scenario_Explorer.py`, line 287.

**Fix**: v4 uses `row_near = df.loc[df["Year"] == yr_near]` followed by `if not row_near.empty:` check.

## Bug 4: Cross-page session state coupling

**Root cause**: v3 `02_Utility_Phase_Analysis.py` reads `st.session_state.get("explorer_applied", ...)` from the Scenario Explorer page.  If the explorer hasn't run yet, defaults are used, but they can diverge from actual explorer state.

**Fix**: v4 pages are self-contained.  Each page loads its own config and runs its own simulation.  No cross-page session state dependency.

## Bug 5: "Power (kWh)" semantic mislabelling

**Root cause**: `footprint_model.py` names its output columns `ATS Total Power (kWh)`, `ECAV Power (kWh)`, etc.  These are annual energy demands (kWh/year), not instantaneous power (kW).  The v3 `DISPLAY_LABEL_MAP` partially corrects this, but the underlying column names still say "Power".

**Fix**: v4 `core.py` has a corrected `DISPLAY_LABELS` map that always shows "energy demand (kWh/yr)".  Subsystem chart labels explicitly say "energy" not "power".  The model's output column names are not changed (backwards compatibility), but all user-facing labels are corrected.

## Bug 6: Missing `from __future__ import annotations` type hint issues

**Root cause**: v3 uses Python 3.10+ type hints (`dict[str, Any]`, `list[str]`) without `from __future__ import annotations` in some files.

**Fix**: v4 adds `from __future__ import annotations` to all page files.

## Bug 7: Cumulative metrics ambiguity

**Root cause**: v3 `04_Turning_Points.py` shows "Cumulative emissions" without specifying the time window.  Users don't know if it's a 68-year total or something else.

**Fix**: v4 explicitly labels cumulative metrics with "(full horizon)" or "(running sum from 2024)".  The cumulative overlay in the Scenario Explorer uses `cumsum()` with explicit documentation.
