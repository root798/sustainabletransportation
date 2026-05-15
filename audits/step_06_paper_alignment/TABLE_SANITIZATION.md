# TABLE_SANITIZATION.md

Table-by-table sanitization instructions for the manuscript and supplementary information. California and Ohio are paper-safe; U.S. Average is quarantined. Every cell listed as "U.S. Average" in the current manuscript draft must be **removed** or **replaced by `QUARANTINED`** with a footnote reference.

Do not edit the manuscript source directly. Apply the instructions below during the table-sanitization pass; use `MANUSCRIPT_CHANGE_MAP.md` for line-level locations.

---

## T1 — Regional baseline-state table (typical Methods Table 1)

Columns: initial vehicle stock, initial BEV count, initial CAV count, initial intersection count, initial low-carbon electricity share.

| Row | Action |
| --- | --- |
| California | Keep. Numbers are paper-safe. |
| Ohio | Keep. Numbers are paper-safe. |
| **U.S. Average** | **Keep the row, but:** all initial-state numbers ARE paper-safe (they are the arithmetic midpoint of CA and OH). Add a footnote `*` that reads: `"U.S. Average initial state is the arithmetic midpoint of California and Ohio. All U.S. Average *derived metrics* (energy, emissions, peak year, turning year) are quarantined — see audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md."` |

## T2 — Regional trajectory-parameter table (Methods Table 2)

Columns: annual BEV-share growth, annual low-carbon-electricity growth, 2075 CAV target fraction, 2075 STI target fraction, efficiency doubling time, annual fleet growth, vehicle service life.

| Row | Action |
| --- | --- |
| California | Keep. Values from `scenarios/california/scenario.json:growth_rates`. |
| Ohio | Keep. Values from `scenarios/ohio/scenario.json:growth_rates`. |
| **U.S. Average** | **Remove the entire row** (preferred) OR replace all trajectory-parameter numbers with `QUARANTINED — see footnote †`, where footnote † reads: `"U.S. Average growth-rate, CAV and STI target-fraction, efficiency-doubling, and fleet-growth values are not arithmetic midpoints of California and Ohio and are quarantined from paper-facing comparison; see audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md."` |

Rationale: U.S. Average trajectory parameters are NOT midpoints of CA and OH and were never reconciled with the per-vehicle baseline.

## T3 — Per-level consumption-rate table (Methods Table 3 or Supplementary)

Columns: per-level sensing / computing / communication power for ECAV (L3 / L4 / L5) and STI (Basic / Semi / Highly); ICECAV overhead multiplier.

| Row | Action |
| --- | --- |
| California | Keep. Numbers are paper-safe. |
| Ohio | Keep. Numbers are paper-safe. |
| **U.S. Average** | **Remove the entire row.** The U.S. Average sensing and communication cells diverge by 10 – 30 × from California and Ohio under an unresolved source mismatch (see `US_AVERAGE_SOURCE_TRACE.md §B`). Do not paste any U.S. Average consumption-rate number into the manuscript; do not attempt to footnote them as "alternative scenario" — they contaminate every downstream metric. |

## T4 — Uncertainty-specification table (Methods Table 4 or Supplementary)

Columns: parameter, distribution family, parameters, semantic tag.

All rows are paper-safe for California and Ohio. This table does NOT separate by region in the current design (California and Ohio share the same distribution families and the same structural form; only the CA-specific `mean` / `kappa` / bounds differ, which is documented in the scenario files). The table should list:

- Layer 1: `f_clean` Beta, `ev_share` Beta, `e_clean` triangular, `e_fossil` triangular, `e_gasoline` triangular.
- Layer 2: ECAV scale factors (6 lognormal), STI scale factors (6 lognormal), `cav_levels` Dirichlet, `sti_levels` Dirichlet, `icecav_power_factor` triangular, `retire_year` integer triangular, `cohort_decay_factor` triangular.
- Layer 3: `ev` truncated normal, `clean_energy` truncated normal, `total_car_increase` truncated normal, 2075 `cav` target triangular, 2075 `sti` target triangular, `efficiency_doubling` triangular.

Footnote: `"Distribution specifications for California and Ohio share the same functional forms; regional differences in means and bounds are documented in scenarios/{region}/scenario.json:data_uncertainty."`

## T5 — Scenario-milestones table (Results Table 1)

Columns: region, modelled peak year, modelled turning year (50 % of peak), interpretation boundary year, modelled low-carbon share saturation year, modelled BEV-share saturation year.

| Row | modelled peak year | modelled turning year | interpretation boundary | clean-share saturation | BEV-share saturation |
| --- | :---: | :---: | :---: | :---: | :---: |
| California | 2036 | 2046 | 2030 | 2040 | late horizon |
| Ohio | 2076 *(horizon edge)* | **Not reached in horizon** | 2031 | ~2075 | Not reached in horizon |
| ~~U.S. Average~~ | — | — | — | — | — |

Actions:

- **Remove the U.S. Average row entirely.**
- Keep the two CA/OH rows exactly as above — all numbers are reproduced from the current backend.
- Preserve the "Not reached in horizon" text literally for Ohio turning year and Ohio BEV saturation. Do not render as `-`, `0`, `NaN`, or blank.
- Footnote *: `"Ohio's modelled peak year lies within the last 20 years of the 2024–2092 simulation horizon; interpret as a within-horizon extremum rather than an asymptote."`

## T6 — Band-widening (L2 expansion) table (Results or Supplementary)

Columns: region, metric, pre-L2 2050 p95–p05 width, post-L2 2050 p95–p05 width, ratio.

| Region | Metric | pre-L2 | post-L2 | ratio |
| --- | --- | ---: | ---: | ---: |
| California | ATS Total Power | 5.63 × 10⁹ | 6.77 × 10⁹ | 1.20 × |
| California | ATS Emissions | 7.47 × 10⁹ | 8.26 × 10⁹ | 1.10 × |
| California | STI Power | 1.23 × 10⁹ | 1.52 × 10⁹ | 1.24 × |
| California | ECAV Power | 1.34 × 10⁹ | 1.53 × 10⁹ | 1.14 × |
| Ohio | ATS Total Power | 1.49 × 10⁹ | 1.82 × 10⁹ | 1.22 × |
| Ohio | ATS Emissions | 2.16 × 10⁹ | 2.70 × 10⁹ | 1.25 × |
| Ohio | STI Power | 4.08 × 10⁸ | 4.85 × 10⁸ | 1.19 × |
| Ohio | ECAV Power | 1.00 × 10⁸ | 1.18 × 10⁸ | 1.17 × |

Actions:

- Keep all eight rows.
- No U.S. Average row should be added.
- Units: kWh/yr for power; kg CO₂/yr for emissions.
- Footnote: `"Band widths compare MC 200 at seed 42, pre-revision vs post-L2 Layer-2 additions (per-level × per-subsystem ECAV/STI scale factors, Dirichlet level mixes, cohort_decay_factor). Source: CA_OH_L2_VALIDATION.md §C."`

## T7 — Paper-safety status table (Supplementary)

A new table recommended for the supplement to make the quarantine self-documenting.

| Region | Initial-state | Trajectory params | Consumption tables | Derived metrics | Status |
| --- | :---: | :---: | :---: | :---: | :---: |
| California | paper-safe | paper-safe | paper-safe | paper-safe | **paper-safe** |
| Ohio | paper-safe | paper-safe | paper-safe | paper-safe | **paper-safe** |
| U.S. Average | paper-safe (midpoint) | not paper-safe (independent assumptions) | **not paper-safe (anomaly)** | **not paper-safe** | **QUARANTINED** |

Footnote: `"Quarantine rationale: audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md."`

---

## Summary action list (for the human editor)

1. Keep Table T1 with a U.S. Average footnote about the quarantine on derived metrics.
2. Remove the U.S. Average row from T2 and T3 entirely.
3. Replace any pre-revision scenario-milestone table (T5-equivalent) with the two-row CA/OH version above.
4. Insert T6 (band-widening) in Results or Supplementary.
5. Insert T7 (paper-safety status) in Supplementary.
6. Ensure every remaining manuscript table that mentions U.S. Average either (a) removes the row, or (b) uses `QUARANTINED` with a footnote reference to `US_AVERAGE_SOURCE_TRACE.md`.

## Forbidden content

- U.S. Average derived metric cells (energy, emissions, peak, turning, boundary, cumulative) anywhere in the manuscript.
- Numeric Ohio turning year. Must always render as "Not reached in horizon".
- Post-saturation narrow-band values as evidence of confidence.
- Three-region ATS energy or emissions bar / line tables.
