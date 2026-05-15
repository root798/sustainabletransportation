# SCENARIO_EXPLORER_SERIES_AUDIT.md

**Date:** 2026-04-14
**Page audited:** `v4_streamlit_app/pages/00_Scenario_Explorer.py`
**Validation region:** California baseline (primary); Ohio baseline (secondary).
**Mode:** Trace every visible line / band to its source.

---

## Per-object classification

| # | Chart | Object | Source classification | Column / file | Notes |
|---|---|---|---|---|---|
| 1 | Annual ATS energy | ECAV, ICECAV, STI stacked areas | Live deterministic runtime | `df["ECAV Power (kWh)"]` etc. from `run_simulation()` | `stackgroup="energy"` |
| 2 | Annual ATS energy | Dashed line labeled **"ATS total (median)"** | Live deterministic runtime | `df["ATS Total Power (kWh)"]` | **Label says "median" but plots deterministic.** S-E-01 |
| 3 | Annual ATS energy | Shaded p05–p95 band | Precomputed baseline MC quantiles | `results/{region}__policy-baseline__model-fixed_table_quantiles.csv` | 200-run MC (seed 42) |
| 4 | Annual ATS energy | Red interpretation-boundary vline + shaded vrect | MC-metadata-driven (via `interpretation_boundary(qf)`) | same quantiles CSV | Only when `is_default and policy=="baseline" and show_unc` |
| 5 | Annual ATS energy | Saturation marker | Metadata sidecar | `*_quantiles_metadata.json` | No-op unless sidecar records `first_saturation_year` for that field |
| 6 | Annual ATS emissions | ECAV, ICECAV, STI lines (NOT stacked) | Live deterministic runtime | `df["ECAV Emissions (kg CO2)"]` etc. | **Unstacked overlay; visually ambiguous w.r.t. total.** S-E-02 |
| 7 | Annual ATS emissions | Dashed line labeled **"ATS total (median)"** | Live deterministic runtime | `df["ATS Emissions (kg CO2)"]` | Same label issue (S-E-01) |
| 8 | Annual ATS emissions | Shaded p05–p95 band | Precomputed baseline MC quantiles | same CSV | |
| 9 | Annual ATS emissions | Interpretation-boundary vline | MC metadata | same | |
| 10 | Counts & infra | Total Vehicles / CAV / EV / STI lines | Live deterministic runtime | `df[...]` | |
| 11 | BEV / clean share | BEV share, low-carbon share lines | Live deterministic runtime | `df[...]` | |
| 12 | BEV / clean share | CA BEV cap annotation | Post-patch sidecar-aware wording ("central trajectory approaches cap; lower tail remains open") | sidecar | |
| 13 | Cumulative ATS energy | Single cumulative line | Running `cumsum` of live deterministic annual energy | `df["ATS Total Power (kWh)"].cumsum()` | |
| 14 | Cumulative ATS energy | Interpretation-boundary vline + vrect | MC metadata | quantiles CSV | **Boundary is an annual-width property; meaning on a monotone cumulative line is undefined.** S-E-03 |
| 15 | Cumulative ATS CO₂ | Cumulative line | Running cumsum of live deterministic annual emissions | `df[...].cumsum()` | |
| 16 | Cumulative ATS CO₂ | Interpretation-boundary vline + vrect | MC metadata | quantiles CSV | Same semantic issue as #14 (S-E-03) |
| 17 | Subsystem breakdown | 9 lines (ECAV × 3 / ICECAV × 3 / STI × 3) | Live deterministic runtime | `df[...]` | `yaxis_type` toggles to log; ICECAV lines go to exact 0 after ≈2080 and are silently dropped on log-y. S-E-04 |

---

## Direct answers to the audit questions

### Q1 — Is the ATS total on the energy chart coming from a baseline MC median while subsystems come from deterministic?

**No.** Both the stacked subsystem areas **and** the dashed "ATS total (median)" line come from the **same live deterministic `df`** (`run_simulation(runtime_cfg, years)`). The MC baseline quantiles enter the chart only as the shaded p05–p95 band. Mathematically, the dashed total = ECAV + ICECAV + STI (identity verified to 1e-6 on `results/california_results.csv`).

### Q2 — Same question for the emissions chart.

**No.** Subsystem emissions lines and the dashed total line all come from the same live deterministic `df`. The MC band is again the only MC-sourced visual.

### Q3 — Is that why ATS total can appear smaller than one or more components?

The mathematical identity `ATS ≡ ECAV + ICECAV + STI` holds for both energy and emissions on the live deterministic df (verified). So the **dashed "ATS total"** line cannot sit numerically below a deterministic component line.

**But there is a real visual ambiguity on the emissions chart.** The subsystem emission lines are **not stacked** — they overlay. The MC p05–p95 band for the **total** sits on the same y-axis. At early years the MC p05 for the total sits well **below** the deterministic ICECAV emissions line (which is typically the dominant component): e.g. CA 2030 deterministic ICECAV = 5.179 Mt CO₂/yr while MC p05 for ATS total = 2.413 Mt CO₂/yr. That is numerically correct (the MC p05 reflects low-fossil-share / low-emission-factor draws, not low ICECAV physical fleet) but presented side-by-side with an unstacked ICECAV line it looks wrong. **This is the "total appears smaller than a component" illusion the user flagged.** See SCENARIO_EXPLORER_TOTAL_COMPONENT_FIX.md for the patch.

### Q4 — Are any bands or medians plotted against non-comparable component trajectories?

**Yes.**
- The **energy** chart's p05–p95 band represents total-level MC uncertainty; the subsystem stacked area represents live deterministic components at sliders. Same y-axis. Semantically the band applies **only** to the total line, but can be misread as applying to the stack.
- The **emissions** chart has the same issue and is worse because subsystems are unstacked.
- The **dashed line is labeled "ATS total (median)"** but is actually the live deterministic trajectory, **not** the MC p50 median. This is a **label bug**: the word "(median)" must either be removed, replaced with "(live deterministic)", or the line must actually be redrawn from `qf["ATS * _p50"]`.

---

## Severity summary

| ID | Finding | Severity | Where |
|---|---|---|---|
| S-E-01 | Dashed "ATS total (median)" label misrepresents a deterministic trajectory as an MC median. | **HIGH** (misleading label) | Energy + emissions charts |
| S-E-02 | Emissions subsystem lines are unstacked; MC total band sits on same y-axis and visually appears to sit below single components. | **HIGH** (incomparable overlay) | Emissions chart |
| S-E-03 | Interpretation-boundary vline drawn on cumulative charts where the pointwise band-width definition does not apply. | **MEDIUM** (mirrors dossier S6-06) | Cumulative energy + emissions charts |
| S-E-04 | Subsystem breakdown plotted with log-y option; ICECAV series reaches exact zero after ≈2080 and Plotly silently drops those points on a log axis. | **LOW** (mirrors dossier S6-05) | Subsystem breakdown chart |
| S-E-05 | Page horizon defaults to 2092 but paper-facing interpretation window is 2024–2075; no visible paper-safe marker or post-2075 shading. | **MEDIUM** | All annual charts |
| S-E-06 | Key-years snapshot table shows **deterministic** turning / peak columns against cumulative MC emissions column without labelling source. | **LOW** | Key year snapshots table |

All six findings are addressed in Part 8 (implementation).
