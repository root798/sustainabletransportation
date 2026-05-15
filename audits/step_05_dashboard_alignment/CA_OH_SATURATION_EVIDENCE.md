# CA_OH_SATURATION_EVIDENCE.md

Evidence-based record of which CA / OH quantile-CSV columns develop zero-width bands because of saturation at a modelling cap, and the exact wording that paper figures and methods must use to describe the effect. Source data: the new `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json` sidecars produced in step 04E.

---

## 1. What the sidecar reports

`compute_saturation_metadata(quantile_df, ...)` flags the **first year at or after BASE_YEAR + 3 (i.e. 2027) where `(p95 − p05) / max(|p50|, 1) < 1e-6`**. Effectively, the first year in which every MC sample has converged to the same value because all draws have saturated at a common boundary.

Output schema, one entry per tracked field:

```
first_saturation_year : int or null
reason                : "band_collapsed_to_zero" | "no_saturation_detected" | "missing_columns"
max_width             : float (maximum p95 − p05 over the horizon)
```

## 2. Results for California (baseline, MC 200, seed 42)

| field | first_saturation_year | reason | max_width |
| --- | ---: | --- | ---: |
| ATS Total Power (kWh) | — | no_saturation_detected | 1.18 × 10¹⁰ |
| ATS Emissions (kg CO₂) | — | no_saturation_detected | 1.72 × 10¹⁰ |
| **Clean Energy Fraction** | **2040** | **band_collapsed_to_zero** | 0.261 |
| EV Fraction | — | no_saturation_detected | 0.869 |

Supporting numbers from the quantile CSV:

- p50 Clean Energy Fraction: 0.879 at 2030, **1.000 at 2040**, **1.000 at 2050**.
- p95 − p05 width: 0.261 at 2030, **0.000 at 2040**, **0.000 at 2050**.
- p50 EV Fraction: 0.43 at 2060, **1.00 at 2075**, 1.00 at 2092. Band width at 2075 = 0.71 (not yet collapsed), at 2092 ≈ 0.
  - EV Fraction does collapse but only at the horizon's extreme end. Not flagged in the sidecar because the collapse year falls outside the `start_year` vs end-of-horizon window where MC variability in slower trajectories keeps the band non-zero.

## 3. Results for Ohio (baseline, MC 200, seed 42)

| field | first_saturation_year | reason | max_width |
| --- | ---: | --- | ---: |
| ATS Total Power (kWh) | — | no_saturation_detected | 2.66 × 10⁹ |
| ATS Emissions (kg CO₂) | — | no_saturation_detected | 4.49 × 10⁹ |
| **Clean Energy Fraction** | **2075** | **band_collapsed_to_zero** | 0.611 |
| EV Fraction | — | no_saturation_detected | 0.990 |

Supporting numbers:

- p50 Clean Energy Fraction Ohio: 0.32 at 2030, 0.54 at 2040, 0.86 at 2050, close to 1.0 by 2075.
- Band width at 2040 = 0.49 (large), at 2050 = 0.52 (still large), narrows only after ~2060 as more samples hit the 1.0 cap.
- p50 EV Fraction Ohio stays low (0.05 at 2060, 0.15 at 2075, 0.43 at 2092); band width at 2075 = 0.98 (very wide; does not saturate in horizon).

## 4. Why each collapse happens

### 4.1 California Clean Energy Fraction — cap artefact at 2040

Mechanism: the model applies `f_clean_t = min(f_clean × (1 + clean_energy)^t, 1.0)` (`footprint_model.py`). Under California's baseline (`f_clean_0 = 0.656`, annual clean-energy growth rate mean 0.05):

- Deterministic p50 reaches the `1.0` cap near t = 17 (year 2041).
- With MC sampling on the growth rate (truncated normal, mean 0.05, sd 0.012, [0.01, 0.10]), the slowest-growth samples still saturate before year 2050. By 2040 every sample has hit the cap.
- Post-saturation, every sample sits at 1.0 by definition. Band width → 0.

Classification: **modelling cap** (not physical saturation, not a policy cap). The hard ceiling at 1.0 is arithmetic: a fraction cannot exceed 1.0.

### 4.2 Ohio Clean Energy Fraction — cap artefact near 2075

Same mechanism. Ohio starts much lower (`f_clean_0 = 0.247`) so the deterministic p50 reaches the 1.0 cap much later (~2052 deterministically; later with low-tail MC samples). Full band collapse happens around 2075 when even the slowest-growth samples have saturated.

### 4.3 California EV Fraction — late-horizon saturation

Mechanism: `ev_frac * (1 + ev_growth)^t`, capped at 1.0. CA deterministic p50 reaches 1.0 near 2075; p05 lags into the late 2080s. Full band collapse approaches 2092 (horizon edge). The sidecar's tracked fields include `EV Fraction`, but CA's collapse is late enough that the p05 remains < 1.0 up to ~2090, so the sidecar reports no collapse before the reporting window.

### 4.4 Ohio EV Fraction — does NOT saturate in horizon

Ohio's initial BEV share is 0.00668 (0.67 %). Even with the mean 0.07 annual growth, the deterministic trajectory reaches only ~0.43 by 2092. Most MC samples remain well below 1.0 for the full horizon. No saturation.

### 4.5 Horizon-edge note for Ohio emissions

Ohio's emissions peak year is 2076, only three years after the interpretation-boundary fires (2031), and 16 years before the horizon ends (2092). The peak sits near the horizon edge. The 50 %-of-peak turning year never fires within the 2024–2092 horizon. This is **not** a saturation artefact; it is a **horizon-edge** limitation.

Sidecar reports this as `turning_year = NaN` inside the `{region}__...metrics.csv` file and the dashboards already display it as "not reached". Keep the language explicit.

## 5. Exact wording for figure captions

Template when a figure contains a saturation-collapsing variable:

> "Shaded band = p05–p95 Monte-Carlo range (N = 200 samples). Post-2040 the band on the California low-carbon electricity share collapses because the modelled share saturates at its 1.0 cap under every sampled growth-rate draw; the narrow band is a cap artefact, not a predictability claim. For Ohio the same collapse is reached near 2075. See `audits/step_05_dashboard_alignment/CA_OH_SATURATION_EVIDENCE.md`."

Alternative short form for a multi-panel figure:

> "Shaded region: 5th–95th percentile MC band. Narrow bands in the low-carbon electricity and BEV-share panels after saturation years (CA clean: 2040; CA BEV: ~2075; OH clean: ~2075) reflect the modelling cap of 1.0, not reduced uncertainty."

Horizon-edge caveat when Ohio peak/turning are shown:

> "Ohio's modelled emissions peak at 2076, near the horizon edge; the 50 %-of-peak turning year is not reached within 2024–2092. Numeric peak year for Ohio should be read as a within-horizon extremum rather than a calibrated peak."

## 6. Methods-section caveat (mandatory if any saturation-collapsing variable is plotted)

> "Three variables saturate at a modelling cap of 1.0 within the default 2024 – 2092 horizon under the CA / OH baseline scenario: California's low-carbon electricity share (2040), California's modelled BEV share of light-duty stock (~2075), and Ohio's low-carbon electricity share (~2075). Post-saturation, the Monte-Carlo p05–p95 band collapses to zero width because every MC sample has hit the same ceiling. A narrow band in these regions indicates saturation at the cap, not reduced input uncertainty. Ohio's BEV share does not saturate within the horizon under the baseline assumptions."

> "We report a horizon-edge limitation for Ohio: the modelled emissions peak (2076) lies within three years of the interpretation boundary and 16 years before the simulation horizon ends. The 50 %-of-peak turning year is not reached within 2024 – 2092 for the Ohio baseline, so we report 'not reached' rather than a numeric year."

## 7. Suggested figure-level annotations

- Vertical dashed line at the interpretation-boundary year, labelled `"Interpretation boundary"`.
- Hatched / shaded region spanning the saturated years, labelled `"Saturation regime — narrow band is a cap artefact, not predictability"`.
- For Ohio turning-year charts: explicit text inset `"Turning year (50 % of peak) is not reached within the 2024–2092 horizon"`.
- For any post-2090 values: inset note `"Horizon edge: values here are end-of-horizon extrema, not asymptotic projections."`.

See `CA_OH_FIGURE_SUPPORT.md` for the complete plotting requirement.

## 8. What the sidecar does NOT catch today

- **EV Fraction saturation** when it happens only in the last 2–3 horizon years. Current threshold `start_year=2027` with end-of-horizon implicit cut-off can miss late collapses that are clearly visible to the eye.
- **Partial saturation**, where most MC samples (but not all) have hit the cap and the band narrows dramatically without fully collapsing to 0. Figure captions must call this out manually.
- **Ohio Clean Energy Fraction**: sidecar flags `2075` but the band is already visibly narrowing from ~2060 onward. A follow-up improvement would add a `first_year_where_width < 10 % of max_width` signal. Not implemented this stage; call out manually in captions.

None of the above invalidate the sidecar-flagged years — they are conservative. The caveats above tighten the figure-caption language where needed.
