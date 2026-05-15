# STI_COMPUTING_EFFICIENCY_CHECK.md

**Date:** 2026-04-14
**Question:** Does `efficiency_doubling_years` influence STI computing energy?
**Answer:** **YES. The efficiency factor is correctly applied to STI computing.** No backend patch needed. Documentation sentence added to the dashboard's footer-adjacent note.

---

## Code trace (`footprint_model.py`)

### Cohort efficiency factor

`TransportModel._calculate_efficiency_factor(t_add, t_base=0)` (line 514) returns
`0.5 ** ((t_add − t_base) / efficiency_doubling_years)` for newly-added CAV cohorts
and is cached in `self.cohort_efficiencies[t_add]`. The same value is looked up
whether the cohort is ECAV, ICECAV, or STI.

### Application of `eff_factor` in `_calculate_power` (line 654)

Three places multiply by `eff_factor`:

1. Line 680 — **ECAV computing**: `power['e_computing'] += e_cav * lvl_fraction * power_dict['computing'] * eff_factor`
2. Line 683 — **ICECAV computing**: `power['i_computing'] += i_cav * lvl_fraction * power_dict['computing'] * self.icecav_power_factor * eff_factor`
3. Line 700 — **STI computing**: `power['s_computing'] += n_sti * sti_fraction * lvl_fraction * power_dict['computing'] * eff_factor`

**All three `computing` terms receive the same `eff_factor`.** Sensing and
communication terms are NOT scaled by `eff_factor`, consistent with the
model's convention that hardware efficiency gains apply to the compute path
only. STI computing is therefore on an equal footing with ECAV/ICECAV
computing with respect to the hardware efficiency doubling prior.

## Empirical validation

Live run on California baseline at three efficiency-doubling settings:

| doubling (years) | STI Computing @ 2030 (GWh/yr) | @ 2050 | @ 2070 | ECAV Computing @ 2050 |
|---|---:|---:|---:|---:|
| 2.0 (fast) | 0.570 | 0.650 | 0.651 | 0.020 |
| 5.0 (baseline-ish) | 1.023 | 1.759 | 1.804 | 0.928 |
| 10.0 (slow) | 1.276 | 3.124 | 3.582 | 3.682 |

Clear monotone sensitivity: slower doubling → higher STI computing energy.
Ratio STI-Computing(doubling=10) / STI-Computing(doubling=2) at 2050 is
**4.8×**, which is the expected order of magnitude for an exponential 0.5^(t/d)
decay integrated over the STI-addition cohort distribution.

## Why STI computing curves can look *flatter* than ECAV late-horizon

The visual impression that STI computing is "less responsive" than ECAV
computing is a **mix effect**, not a bug:

- CA fleet is large and mostly ICE-heavy until the 2060s. ECAV count is tiny
  early, then explodes after BEV share saturates; so ECAV computing grows
  rapidly with fleet turnover, amplifying the efficiency-decay signature.
- STI count grows linearly from zero to its 2075 target; once it plateaus,
  annual STI additions → 0, and the remaining computing draw is dominated
  by long-lived old cohorts whose eff_factor has already decayed most of its
  distance to zero, so the curve flattens out near its asymptote.

Both behaviours are consistent with `0.5^(elapsed / doubling)` physics
applied to each cohort and summed.

## Dashboard-level note

No backend patch. The dashboard's subsystem-breakdown section now carries
an inline caption stating that the hardware efficiency doubling prior
applies to **all three computing channels (ECAV / ICECAV / STI)** and NOT
to sensing or communication, to prevent readers misreading the flat STI
computing tail as insensitivity to the prior. See
`v4_streamlit_app/pages/00_Scenario_Explorer.py` in the subsystem-breakdown
block.
