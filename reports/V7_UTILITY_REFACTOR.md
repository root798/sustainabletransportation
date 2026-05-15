# V7_UTILITY_REFACTOR — page-role correction + decomposition alignment

**Date**: 2026-04-20
**Scope**: `v7_streamlit_app/pages/02_Utility_Phase_Energy.py` and
`v7_streamlit_app/pages/03_Scenario_Explorer.py`. No changes to
`footprint_model.py`, `core.py`, `figure_style.py`, or any configs.
**Risk to v5**: none. v5 and v6 dashboards unchanged.

---

## 1. What was moved from Utility Phase Energy → Scenario Explorer

Everything that is *state-scale* moved off the Utility Phase page.

| Item | Old home (Utility Phase Energy) | New home (Scenario Explorer) |
| --- | --- | --- |
| California and Ohio annual ATS-emissions trajectory curves | ✗ removed | already present in Figure A |
| California / Ohio residual bands | ✗ removed | already present in Figure A |
| State-level subsystem stack at 2050 | ✗ removed | superseded by the state-conditioned time series below |
| Sensing / computing / communication decomposition over time | ✗ removed (was state-level) | **rewritten** and now placed immediately below Figure A; reads from the **same live deterministic simulator run** as Figure A |
| BEV share and clean-electricity share curves by state | ✗ removed | covered by the scenario-level discussion on Scenario Explorer |
| Peak / turning year summary table by state | ✗ removed | available inline on Scenario Explorer (existing peak-year diagnostic) |

## 2. What the Utility Phase Energy page is now

A per-unit, per-year view. Answers:

- How much energy does one vehicle (or one infrastructure asset) consume per year?
- How is that energy split between propulsion and the AV subsystems?
- How does the split change between ICE and BEV, and between L3 / L4 / L5 autonomy?
- How does the same unit's CO₂ change under different regional grid / fuel factors?

Three figures:

1. **Annual running energy, per vehicle** — horizontal stacked bars for the 6 combinations {ICE, BEV} × {L3, L4, L5}. Stacks: Propulsion, Computing, Sensing, Communication. Direct-label total per bar.
2. **AV subsystem breakdown (excluding propulsion)** — same 6 vehicles plus the three STI levels for reference.
3. **Same unit, different grid / fuel context** — annual CO₂ per vehicle under the California and Ohio emission factors. Clearly framed as "same unit under different grid context", not a state-scale trajectory.

Propulsion baselines are inline-editable via two number inputs. Defaults:
- ICE propulsion 14,200 kWh / yr (FHWA 11,500 mi × EPA 27.3 mpg × EIA 33.7 kWh / gal LHV).
- BEV propulsion 3,565 kWh / yr (FHWA 11,500 mi × EPA 0.31 kWh / mi).

## 3. The decomposition mismatch — root cause

The Scenario Explorer's Subsystem Decomposition figure previously used six
subsystem emission columns:

```
ECAV Sensing / ECAV Computing / ECAV Communication
STI  Sensing / STI  Computing / STI  Communication
```

The simulator emits **nine** subsystem emission columns. The missing three
were the ICECAV subsystems:

```
ICECAV Sensing / ICECAV Computing / ICECAV Communication
```

ICECAV (the gasoline-ICE portion of the connected autonomous fleet) carries
the tank-to-wheel gasoline emissions via `e_gasoline`, and is the dominant
subsystem in every year until late-horizon electrification overtakes it.

At baseline California in 2030 the six-column decomposition summed to
**0.079 Gt CO₂ / yr**, against an ATS total of **5.258 Gt CO₂ / yr** — a
**98.5 % shortfall**. The decomposition chart therefore under-reported the
stack height by about two orders of magnitude relative to the Figure A
trajectory line, while the total trajectory itself was correct.

A second, orthogonal issue was that the decomposition read from the
**committed MC bundle** (`results/<region>__policy-baseline__bundle-default_quantiles.csv`)
while Figure A reads from a **live deterministic** run against the current
session settings. Pointwise quantiles of each subsystem over a Monte Carlo
are not required to sum to the pointwise quantile of the total; that is a
second path for divergence if Block 1-4 controls are moved.

## 4. Fix

Two changes inside `pages/03_Scenario_Explorer.py`:

1. **Add the three ICECAV subsystem columns** to the decomposition stack.
   All nine columns from the simulator output are now plotted.
2. **Route the decomposition to the live deterministic run.** The figure
   now calls `run_simulation(_live_cfg, years=68)` — the same call signature
   and the same `_live_cfg` as Figure A. A dashed "ATS total (check)" line
   is overlaid so the reader can see that the stack top matches the total
   at every year.

A visible alignment-check table is rendered below the decomposition chart:

| Year | Subsystem sum (Mt CO₂e) | ATS total (Mt CO₂e) | Relative difference |
| --- | --- | --- | --- |
| 2030 / 2050 / 2075 for the currently-selected region and policy |

## 5. Year-by-year validation

Run: `python -c "from core import ...; …"` (see `audits/v7/V7_DECOMPOSITION_ALIGNMENT.json`).

| Region | Year | Subsystem sum (Gt CO₂e) | ATS total (Gt CO₂e) | Relative difference | Status |
| --- | --- | --- | --- | --- | --- |
| California | 2030 | 5.2578 | 5.2578 | 0.00e+00 | **PASS** |
| California | 2050 | 3.6059 | 3.6059 | 1.32e-16 | **PASS** |
| California | 2075 | 0.1272 | 0.1272 | 1.17e-16 | **PASS** |
| Ohio | 2030 | 0.7831 | 0.7831 | 0.00e+00 | **PASS** |
| Ohio | 2050 | 0.9572 | 0.9572 | 1.25e-16 | **PASS** |
| Ohio | 2075 | 1.5774 | 1.5774 | 1.51e-16 | **PASS** |

Alignment is exact to floating-point precision (worst case 1.5e-16).

## 6. Files changed

| File | Change |
| --- | --- |
| `v7_streamlit_app/pages/02_Utility_Phase_Energy.py` | **Rewritten** as per-unit annual-running-energy page. Three figures. No state-level trajectories, bands, or peak-year summaries. |
| `v7_streamlit_app/pages/03_Scenario_Explorer.py` | Subsystem Decomposition now (a) includes all 9 subsystem emission columns and (b) reads from a live `run_simulation(_live_cfg, ...)` call identical to Figure A. Alignment-check table rendered beneath the figure. |
| `audits/v7/V7_DECOMPOSITION_ALIGNMENT.json` | New validation artefact. Six rows (region × year) with the subsystem sum, ATS total, and relative difference. |
| `reports/V7_UTILITY_REFACTOR.md` | This document. |

No other files touched. `footprint_model.py`, `core.py`, `figure_style.py`,
all `configs/*.json`, all `scenarios/`, all committed bundles in `results/`,
and the v5 and v6 dashboards are unchanged.

## 7. QA checklist

### 7.1 Page-role separation

- [x] Utility Phase Energy contains no state-level ATS trajectory curves.
- [x] Utility Phase Energy contains no state residual bands.
- [x] Utility Phase Energy contains no BEV-share or clean-electricity-share state plots.
- [x] Utility Phase Energy contains no peak / turning-year state summary.
- [x] Utility Phase Energy does carry the per-unit stacked bars (Propulsion + AV subsystems).
- [x] Utility Phase Energy does carry the AV-subsystem unit-level breakdown.
- [x] Scenario Explorer retains Figure A with state trajectory + bands.
- [x] Scenario Explorer now carries the state-conditioned subsystem decomposition over time using the live deterministic run.

### 7.2 Alignment

- [x] Sum of the 9 subsystem emission columns equals the ATS total at every tested year for both California and Ohio (worst relative diff 1.5e-16).
- [x] Decomposition reads from `run_simulation(_live_cfg, years=68)` — the same call and same config variable that Figure A uses.
- [x] Dashed "ATS total (check)" line overlaid on the stacked area so users can visually confirm alignment.
- [x] Numeric alignment-check table rendered immediately below the figure at 2030 / 2050 / 2075.

### 7.3 Interactive surfaces still work

- [x] Region selector.
- [x] Policy selector.
- [x] Committed-band selector.
- [x] Block 1 mitigation sliders.
- [x] Block 2 fixed-data inputs (where retained).
- [x] Block 3 template selectboxes.
- [x] Block 4 Default / Custom selectboxes.
- [x] Trajectory metric toggle (Emissions / Energy / Both).
- [x] Uncertainty object toggle (Residual / Scenario envelope).
- [x] Recompute residual band button.
- [x] Recompute scenario envelope button.
- [x] Reset buttons (mitigation, Block 4).
- [x] Policy pathway expander and Apply button.
- [x] Subsystem decomposition rerender after any control change (because it's regenerated from `_live_cfg` on every page render).

### 7.4 Copy / labels

- [x] Utility Phase Energy title and caption describe unit-level running energy.
- [x] Utility Phase Energy intro paragraph points the reader to Scenario Explorer for state-scale content.
- [x] Scenario Explorer decomposition subheader reads "State-conditioned subsystem decomposition over time".
- [x] Scenario Explorer decomposition caption says the six-plus-three subsystem values sum exactly to the total.
- [x] No caption on either page references the other page's figures by an incorrect location.

### 7.5 No-calculation-change confirmation

- [x] `footprint_model.py` untouched.
- [x] `core.py` untouched.
- [x] `configs/*.json` untouched.
- [x] v5 dashboard produces identical output (verified via `v5_streamlit_app/pages/00_Scenario_Explorer.py` importing the same `core.py` and `footprint_model.py`).

## 8. Consistent component palette

The Utility Phase page and the Scenario Explorer decomposition use the same
color map for shared components:

| Component | Hex (from `figure_style.NATURE_CATEGORICAL`) |
| --- | --- |
| Propulsion | `#595959` (neutral) |
| Computing | `#0F4C81` (primary) |
| Sensing | `#55A868` (tertiary) |
| Communication | `#C44E52` (secondary) |

On Scenario Explorer, ICECAV components use the Propulsion hex with
stepped opacity (0.90 / 0.70 / 0.50) so Computing / Sensing / Communication
are visually distinct while remaining grouped as "ICE propulsion-linked"
output.

## 9. Launch

```bash
streamlit run v7_streamlit_app/streamlit_app.py --server.port 8503
```

v5 and v6 remain runnable alongside on separate ports.
