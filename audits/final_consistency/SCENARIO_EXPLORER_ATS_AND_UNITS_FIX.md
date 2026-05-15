# SCENARIO_EXPLORER_ATS_AND_UNITS_FIX.md

**Date:** 2026-04-14
**Scope:** Scenario Explorer page on the v4 Streamlit dashboard; shared core helpers reused in v3.

---

## A. Root cause

Two issues were mixed up in the user's observation that the ATS curve looked
"not correct":

1. **Unit-label bug in the energy auto-scale helpers.** `v4_streamlit_app/core.py::_auto_scale` and `fmt_energy`, and their v3 twins
   `v3_streamlit_app/dashboard_core.py::scale_series` and `format_energy`,
   were authored as if the energy series were in **Wh** (divisors 1e12 / 1e9 / 1e6).
   The backend actually stores **kWh/yr** per CSV column convention
   (`'ATS Total Power (kWh)'` etc. are annual energy totals, not watts).
   Correct conversions: 1 TWh = 1e9 kWh; 1 GWh = 1e6 kWh; 1 MWh = 1e3 kWh.
   Effect: every energy chart's y-axis label and every `fmt_energy(...)`
   metric card was a **factor-of-1000 underscaled label**; the curve shape
   itself was correct because every series went through the same faulty
   divisor, but numbers like California 2040 ATS = 5.923 TWh/yr were labelled
   "5.92 GWh/yr". Scales applied to *emissions* and *counts* were already correct.

2. **X-axis left-blank region.** `xaxis=dict(autorange=True)` on Plotly lets
   shape-attached annotations (notably the "2075 paper target-reach" vline
   label) widen the computed xmin below 2024 so the annotation text box does
   not clip. Every Scenario Explorer chart was affected.

The **ATS definition itself was correct** end-to-end (audited below); the
apparent curve-vs-subsystem inconsistency was driven by the unit-label bug
and the stretched x-axis making the curves look compressed.

### Files and functions involved

- `footprint_model.py`:
  - `TransportModel._calculate_power` (line 655) — computes the 9-channel
    power dict (`e_sensing/computing/communication`, `i_*`, `s_*`).
  - `TransportModel._calculate_emissions` (line 709) — returns per-channel
    emissions plus `e_emission / i_emission / s_emission / cav_emission /
    ats_emission`.
  - `TransportModel.run_simulation` (line 784 onwards) — records
    `'ATS Total Power (kWh)' = sum(power.values())`, plus
    `'ECAV Power (kWh)'`, `'ICECAV Power (kWh)'`, `'STI Power (kWh)'`,
    `'ATS Emissions (kg CO2)' = emissions['ats_emission']`, and the three
    subsystem emission columns.
- `v4_streamlit_app/core.py`:
  - `_auto_scale` — **had the unit bug**.
  - `fmt_energy` — **had the unit bug**.
- `v3_streamlit_app/dashboard_core.py`:
  - `scale_series` — same unit bug, now patched for parity.
  - `format_energy` — same unit bug, now patched for parity.
- `v4_streamlit_app/pages/00_Scenario_Explorer.py`:
  - All 7 charts previously used `xaxis=dict(autorange=True)`; only the two
    annual top charts had been pinned to an explicit range. Now every chart
    is pinned.

---

## B. ATS formula check

### Implemented formula (unchanged by this patch)

```
# Power (kWh/yr, annual energy)
ECAV Power   = ECAV Sensing + ECAV Computing + ECAV Communication
ICECAV Power = ICECAV Sensing + ICECAV Computing + ICECAV Communication
STI Power    = STI Sensing + STI Computing + STI Communication
ATS Total Power (kWh) = sum of all 9 channel powers
                      = ECAV Power + ICECAV Power + STI Power

# Emissions (kg CO2/yr)
ECAV Emissions   = ECAV Power   × (f_clean·e_clean + (1-f_clean)·e_fossil)
ICECAV Emissions = ICECAV Power × e_gasoline
STI Emissions    = STI Power    × (f_clean·e_clean + (1-f_clean)·e_fossil)
ATS Emissions    = ECAV Emissions + ICECAV Emissions + STI Emissions
```

Source of truth: `footprint_model.py::TransportModel.run_simulation` at
lines 784–807. Confirmed by reading the function: no double-counting, no
omission.

### Identity check on live deterministic CSVs

| Region | `max|ATS Total Power − (ECAV+ICECAV+STI)|` | `max|ATS Total Power − Σ 9 channels|` | `max|ATS Emissions − (ECAV+ICECAV+STI Em)|` |
|---|---:|---:|---:|
| California | 9.54e-07 kWh/yr | 9.54e-07 kWh/yr | 4.77e-07 kg CO₂/yr |
| Ohio | 7.15e-07 kWh/yr | 4.77e-07 kWh/yr | 4.77e-07 kg CO₂/yr |

The identity holds to floating-point rounding. It held **before and after**
the patch (this patch does not touch the backend).

### Dashboard plotting sanity

- Energy chart: ECAV / ICECAV / STI stacked areas plus an "ATS total (live
  deterministic)" dashed line, all scaled by a single `_e_factor` taken
  from `ATS Total Power`. Dashed total sits on the top of the stack by
  mathematical identity (verified 1e-7 drift, unchanged).
- Emissions chart: same structure with `stackgroup="emissions"` and a
  single `_em_factor`.
- MC overlay band and MC p50 line both come from
  `results/{region}__policy-baseline__model-fixed_table_quantiles.csv`
  columns `ATS Total Power (kWh)_p05/p50/p95` and
  `ATS Emissions (kg CO2)_p05/p50/p95`. They apply to the total only and
  are labelled as such in both the trace name and the chart caption.

### Fix

**No code change on the computation side.** The label mismatch that
prompted the investigation was a **unit-label bug** in the display
helpers, not an ATS-formula bug. The label correctness fix is recorded
in section D.

---

## C. Plot-range check

### Old x-axis behaviour

- Five of seven charts used `xaxis=dict(autorange=True)`.
- The remaining two (annual energy, annual emissions) used an explicit
  range already (from the prior `SCENARIO_EXPLORER_XAXIS_BUG_FIXED.md` pass).
- With autorange, Plotly expanded xmin below 2024 to accommodate
  shape-attached annotation text boxes ("2075 paper target-reach",
  saturation "cap artefact" labels). Result: a blank band on the left and
  compressed curves on the right.

### New x-axis behaviour

All seven Scenario Explorer charts now share one pinned range, derived
from the live deterministic dataframe:

```python
_xmin = int(df["Year"].min())
_xmax = int(df["Year"].max())
_page_xrange = [_xmin, _xmax]
fig.update_xaxes(range=list(_page_xrange), autorange=False)
```

For the default California baseline at `exp_years=68`, this evaluates to
`[2024, 2092]`. For any horizon slider value it evaluates to
`[2024, 2024 + exp_years]`. All four annual panels and the cumulative
pair, the counts chart, the fractions chart, and the subsystem breakdown
now align exactly on the same x-range.

### Why the new range is more appropriate

- It is derived from the data itself, not a global constant, so it
  naturally tracks the user-selectable horizon slider.
- Shape-attached annotation text cannot silently widen the range because
  `autorange=False` is explicit.
- All seven charts pin to the same object, so panels visually align.
- The 2075 paper-safe marker and its annotation (now anchored `"top right"`)
  remain inside the range and continue to render correctly.

---

## D. Other issues found and fixed

| Issue | Where | Fix |
|---|---|---|
| Unit-label bug: energy divisors 1e12 / 1e9 / 1e6 assumed series in Wh, but series is in kWh/yr. All energy y-axis labels and metric cards were a decade too small (e.g. CA 2040 ATS shown as "5.92 GWh/yr" instead of "5.92 TWh/yr"). | `v4_streamlit_app/core.py::_auto_scale`, `fmt_energy`; `v3_streamlit_app/dashboard_core.py::scale_series`, `format_energy` | Corrected divisors to `(1e9 TWh, 1e6 GWh, 1e3 MWh)`. Emissions and counts unchanged (already correct). |
| X-axis auto-expansion on 5/7 charts produced a large blank left region | `v4_streamlit_app/pages/00_Scenario_Explorer.py` (counts, fractions, cumulative pair, subsystem) | Added `fig.update_xaxes(range=list(_page_xrange), autorange=False)` on every chart and removed residual `xaxis=dict(autorange=True)` fragments. |
| Variable `_annual_xrange` was scoped to the two annual charts only | `00_Scenario_Explorer.py` | Renamed to `_page_xrange` since every chart now uses the same range. |
| Annual charts used `update_xaxes` but some still had `xaxis=dict(autorange=True)` hanging around in the `update_layout` call | `00_Scenario_Explorer.py` | Removed the residual `xaxis=...` arguments so the explicit range is authoritative. |

No other ATS-semantic, labelling, annotation, or provenance issue was
found during this pass. ATS identity holds exactly; subsystem definitions
match their series; legend entries match their traces; annual and
cumulative quantities are kept on separate figures; saturation markers
only fire when the sidecar reports a non-null `first_saturation_year`;
paper-safe 2075 markers and their post-2075 vrects remain inside range on
every chart.

---

## E. Files changed

| File | Change |
|---|---|
| `v4_streamlit_app/core.py` | Corrected unit divisors for energy in `_auto_scale` (kWh/yr → TWh/GWh/MWh at 1e9 / 1e6 / 1e3) and in `fmt_energy`. Added a docstring explaining the unit convention. |
| `v3_streamlit_app/dashboard_core.py` | Same fix in `scale_series` and `format_energy` for parity. |
| `v4_streamlit_app/pages/00_Scenario_Explorer.py` | Renamed `_annual_xrange` → `_page_xrange`. Added `fig.update_xaxes(range=list(_page_xrange), autorange=False)` on every chart (counts, fractions, cumulative energy, cumulative emissions, subsystem breakdown). Removed residual `xaxis=dict(autorange=True)` fragments. All seven charts now pin to the same scenario-driven range. |
| `audits/final_consistency/SCENARIO_EXPLORER_ATS_AND_UNITS_FIX.md` | This audit note. |
