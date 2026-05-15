# FRONTEND_VALIDATION_PHASE2.md

Validation of the step-05B dashboard and figure-export alignment. Every claim below is cross-checked from the live code paths at the end of the step.

---

## A. Boundary consistency — backend / v3 / v4

Live check after all step-05B edits:

| region | `footprint_model.compute_interpretation_boundary` | v3 `dashboard_core.compute_interpretation_boundary` | v4 `core.interpretation_boundary` |
| --- | ---: | ---: | ---: |
| California | 2030 | 2030 | 2030 |
| Ohio | 2031 | 2031 | 2031 |

All three codepaths import the same constants and the same `compute_interpretation_boundary` function from `footprint_model.py`. v3 and v4 expose thin wrappers that only adapt the return-key shape. No local redefinition is possible without touching `footprint_model.py`.

## B. Saturation consistency

Sidecar metadata loaded via `load_saturation_metadata(region, 'baseline')` on both v3 and v4:

| region | field | v3 first_saturation_year | v4 first_saturation_year | reason |
| --- | --- | ---: | ---: | --- |
| California | Clean Energy Fraction | 2040 | 2040 | band_collapsed_to_zero |
| Ohio | Clean Energy Fraction | 2075 | 2075 | band_collapsed_to_zero |
| US Average | Clean Energy Fraction | None | None | no_saturation_detected |

- CA Clean Energy Fraction marker renders at 2040 with text "Saturation 2040 (cap artefact)".
- OH Clean Energy Fraction marker renders at 2075 with the same phrasing.
- CA EV Fraction: sidecar does not flag; the v4 Scenario Explorer adds a **manual arrowed annotation** when the deterministic p50 reaches 1.0 within the horizon, so the late-horizon cap is not silently read as confidence.
- OH EV Fraction: sidecar returns `no_saturation_detected`; no marker drawn. This is correct — OH BEV share does not saturate within 2024 – 2092.

## C. Turning-year consistency

Computed on the refreshed deterministic CSVs (`--mc 0`):

| region | peak_year | turning_year | render |
| --- | ---: | ---: | --- |
| California | 2036 | 2046 | `"Modelled turning year (50 % of peak): 2046"` |
| Ohio | 2076 | NaN | `"Modelled turning year (50 % of peak): Not reached in horizon"` |

Ohio turning year is never rendered blank, never `0`, never `None` literal, never as a numeric year. Verified by reading the metric-card and chart-annotation code in v4 `03_Turning_Points.py` and v4 `00_Scenario_Explorer.py`.

## D. Overlay honesty under slider motion

- v4 `00_Scenario_Explorer.py` suppresses the uncertainty overlay and displays `st.warning(...)` with explicit reason whenever `controls_match(cv, baseline_cv)` is False. The warning text names the fix ("reset controls to baseline or run a fresh MC ensemble for this scenario").
- v3 `00_Scenario_Explorer.py` suppresses the overlay via the pre-existing `default_quantiles_match` gate; step-04E also added `st.warning(...)` for the specific "sliders moved" case.
- No path in either dashboard draws a precomputed baseline band on top of a non-baseline live line.

## E. U.S. Average restriction

Grep for the banner wording across the two active apps:

- `v4_streamlit_app/core.py` defines `REGION_PAPER_SAFETY["us_average"]["paper_safe"] = False` with a pointer to `US_AVERAGE_SOURCE_TRACE.md`.
- `v4_streamlit_app/pages/00_Scenario_Explorer.py`, `02_State_Results.py`, `03_Turning_Points.py`, `04_Uncertainty_Analysis.py` all render an `st.error` banner when the selected region is U.S. Average.
- `v4_streamlit_app/pages/04_Uncertainty_Analysis.py` support matrix shows the region-level Paper-safe column: `QUARANTINED` for us_average, `Yes` for the others.
- `v3_streamlit_app/pages/00_Scenario_Explorer.py` and `03_State_Results.py` render the same U.S. Average quarantine banner.

U.S. Average remains runnable as an exploratory scenario; it is never silently presented as paper-safe.

## F. Paper-figure export — smoke test

```
python scripts/build_paper_figures.py
```

Produces:

```
[california] ATS Total Power (kWh) → ATS_Total_Power_kWh_annual_energy.pdf
[california] ATS Emissions (kg CO2) → ATS_Emissions_kg_CO2_annual_emissions.pdf
[california] Clean Energy Fraction → Clean_Energy_Fraction_clean_energy_share.pdf
[california] EV Fraction → EV_Fraction_bev_share.pdf
[ohio] ATS Total Power (kWh) → ATS_Total_Power_kWh_annual_energy.pdf
[ohio] ATS Emissions (kg CO2) → ATS_Emissions_kg_CO2_annual_emissions.pdf
[ohio] Clean Energy Fraction → Clean_Energy_Fraction_clean_energy_share.pdf
[ohio] EV Fraction → EV_Fraction_bev_share.pdf
Wrote 8 figures. Captions in: reports/paper_support/captions
Note: U.S. Average is intentionally excluded (paper-quarantined).
```

Each caption opens with a clause naming the region, interpretation boundary, and saturation year when applicable; the Ohio emissions caption automatically includes the horizon-edge clause (`"Horizon-edge note: peak lies within the last 20 years of the 2024–2092 simulation horizon; interpret as a within-horizon extremum, not an asymptote."`). Confirmed by opening the generated `ohio__annual_emissions.txt` file.

Requesting U.S. Average (e.g. `--regions us_average`) is silently filtered out by the script's `PAPER_REGIONS` guard; the exit code is non-zero if no paper-safe region survives the filter.

## G. Human verification checklist

Run `streamlit run v4_streamlit_app/streamlit_app.py` and visually check each item:

### G.1 v4 Scenario Explorer — California baseline, show uncertainty ON, all sliders at default

- [ ] Red dotted vertical line at **2030** labelled "Interpretation boundary".
- [ ] Very light red rectangle shading from 2030 to 2092 labelled "Scenario envelope (post-boundary) — bounded exploratory".
- [ ] p05–p95 band visible on energy and emissions panels.
- [ ] Fractions panel shows a brown dashed line at **2040** labelled "Saturation 2040 (cap artefact)".
- [ ] Fractions panel shows an arrowed annotation near 2075 labelled "BEV cap reached 2075 (late-horizon; band narrowing after this is a cap artefact, not predictability)".
- [ ] Metric card 1 reads "Modelled peak emissions" with delta "Modelled peak year 2036".
- [ ] Metric card 2 reads "Modelled turning year (50 % of peak)" with value **2046**.
- [ ] No red quarantine banner (California is paper-safe).
- [ ] No horizon-edge caveat (CA peak 2036 is ≥ 20 y from horizon end 2092).

### G.2 v4 Scenario Explorer — Ohio baseline

- [ ] Red dotted vertical line at **2031** labelled "Interpretation boundary".
- [ ] Post-boundary red rectangle from 2031 to 2092.
- [ ] Fractions panel shows brown dashed line at **2075** labelled "Saturation 2075 (cap artefact)".
- [ ] No BEV cap annotation (OH BEV does not saturate).
- [ ] Metric card 2 reads "Modelled turning year (50 % of peak) — Not reached in horizon".
- [ ] Visible horizon-edge caption: "Horizon-edge caveat: modelled peak year (2076) sits within 16 years of the horizon end (2092)."
- [ ] No quarantine banner.

### G.3 v4 Scenario Explorer — U.S. Average baseline

- [ ] Red `st.error` banner at top: "⚠️ U.S. Average is quarantined from paper-facing quantitative comparison. …"
- [ ] All charts still render (exploratory), but the banner is unmistakable.

### G.4 v4 Turning Points — Ohio

- [ ] "Modelled peak year" = 2076.
- [ ] "Modelled turning year (50 % of peak) — Not reached in horizon".
- [ ] Yellow warning banner: "Horizon-edge caveat …".
- [ ] In-chart annotation box (top-right) reads "50 %-of-peak turning year: **Not reached in horizon**".

### G.5 v4 Uncertainty Analysis — California

- [ ] Support matrix has a "Paper-safe" column; California row reads `Yes`; U.S. Average row reads `QUARANTINED`.
- [ ] Detail view: both panels show p05–p95 band, red dotted boundary at 2030, and red-shaded post-boundary region.
- [ ] Saturation diagnostics table below the charts lists `Clean Energy Fraction` → `2040` → `band_collapsed_to_zero`.

### G.6 v4 State Results

- [ ] Red quarantine banner at top of page referencing `US_AVERAGE_SOURCE_TRACE.md`.

### G.7 v3 Scenario Explorer — Ohio baseline

- [ ] "Modelled peak emissions" with delta "Modelled peak year 2076".
- [ ] "Modelled turning year (50 % of peak) — Not reached in horizon".
- [ ] Horizon-edge caption visible.

### G.8 v3 State Results

- [ ] Red quarantine banner.

### G.9 Paper-figure export

- [ ] `reports/paper_support/figures/california/` contains 8 files.
- [ ] `reports/paper_support/figures/ohio/` contains 8 files.
- [ ] No `us_average` directory exists.
- [ ] Each PDF visually shows: p50 line, p05–p95 shaded band, red dotted boundary marker, red-shaded post-boundary region, brown dashed saturation marker where applicable.
- [ ] Caption file `ohio__annual_emissions.txt` contains the horizon-edge clause.

## H. Remaining mismatches between UI and backend

None that affect paper-facing claims.

Minor:

- v3 fractions panel does not render saturation markers (only v4 does). Deferred to a follow-up v3 pass.
- v4 Uncertainty Analysis support matrix does not cross-check paper-safety against the actual `data_uncertainty` content of each scenario file; it uses the static `REGION_PAPER_SAFETY` dict. If a future scenario silently edits its consumption tables, the dict must be updated. Documented in §6 of `STEP_05B_DASHBOARD_IMPLEMENTATION.md`.

## I. What should be handled in the next (paper-alignment) stage

- Insert `reports/paper_support/figures/{region}/*.pdf` + the matching `reports/paper_support/captions/*.txt` into the manuscript.
- Restrict every results table that currently lists U.S. Average to CA + OH, or mark `QUARANTINED`.
- Update methods-section text per the checklist in `audits/step_05_dashboard_alignment/CA_OH_REVIEWER_RESPONSE_SUPPORT.md §5`.
- Run the auto-review or equivalent against the updated manuscript.
- Resolve the U.S. Average consumption-rate anomaly (see `US_AVERAGE_SOURCE_TRACE.md §5`). This is out of scope for the dashboard stage; it is a data-sourcing task.
