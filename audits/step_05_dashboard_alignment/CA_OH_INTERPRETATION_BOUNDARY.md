# CA_OH_INTERPRETATION_BOUNDARY.md

Formalizes the interpretation-boundary definition for California and Ohio after the CA/OH L2 uncertainty redesign. U.S. Average is excluded because its `consumption_rates` cells remain quarantined; see `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`.

---

## 1. Source-of-truth definition (code level)

Single backend definition, imported by v3 and v4 dashboards:

```python
# footprint_model.py
INTERP_BOUNDARY_THRESHOLD = 1.5
INTERP_BOUNDARY_START_YEAR = 2027
INTERP_BOUNDARY_METRIC = "ATS Emissions (kg CO2)"
TURNING_YEAR_DECLINE_RATIO = 0.5
```

```python
def compute_interpretation_boundary(quantile_df, metric_base=INTERP_BOUNDARY_METRIC,
                                    threshold=INTERP_BOUNDARY_THRESHOLD,
                                    start_year=INTERP_BOUNDARY_START_YEAR):
    """First year >= start_year where (p95 - p05) / |p50| >= threshold.
    Before that year: quantitative scenario estimate with uncertainty band.
    At/after that year: scenario envelope / bounded exploratory trajectory."""
```

- **Metric**: `ATS Emissions (kg CO2)` (annual, region- and policy-specific).
- **Threshold**: `(p95 − p05) / |p50| ≥ 1.5`. Reviewer-relevant in that it marks when the between-scenario spread exceeds 150 % of the central trajectory, making point projections meaningless.
- **Start year**: 2027. Skips the first three horizon years where small baseline values inflate relative ratios and produce spurious early crossings.
- **Back-end canonical**, imported (not redefined) by both dashboards.

## 2. Boundary years before vs after the CA/OH L2 redesign

Bands widened 9–28 % as a result of adding ECAV/STI per-level × per-subsystem scale factors, `cohort_decay_factor` uncertainty, and Dirichlet priors on `cav_levels` / `sti_levels`. The interpretation boundary moved earlier accordingly.

| region | boundary (step 02, pre-L2) | boundary (step 04E, post-L2) | Δ |
| --- | ---: | ---: | ---: |
| California | 2033 | **2030** | −3 years |
| Ohio | 2035 | **2031** | −4 years |

These are from `compute_interpretation_boundary` on the refreshed `results/{region}__policy-baseline__model-fixed_table_quantiles.csv` files (MC 200, seed 42).

### 2.1 Why California moved 2033 → 2030

Three factors contributed:

1. **ECAV / STI scale factors added.** 12 new lognormal priors per region on per-level × per-subsystem multipliers. Sigmas of 0.15–0.35 translate to a ~20–50 % standard-deviation on the multiplicative factor. Because sensing and communication do NOT receive the cohort-efficiency scaling (the efficiency decay is applied to `computing` only), the extra multiplicative uncertainty on sensing and communication accumulates into the `ATS Emissions` trajectory without being damped out by Moore's-law compute scaling.
2. **Level-mix Dirichlet on `cav_levels` and `sti_levels`.** Replacing the frozen `[0.5, 0.333, 0.167]` with a Dirichlet(concentration=10, mean=[0.5, 0.333, 0.167]) admits per-level mix shifts of ±5–10 %. L5-heavy draws drive emissions up; L3-heavy draws drive them down. This is a genuine sampling variance that was previously suppressed.
3. **`cohort_decay_factor` migrated from 0.7 hard-coded to triangular(0.5, 0.7, 0.9).** Affects the initial-cohort age weighting and therefore the year-0 to year-11 power curves.

Cumulatively, the early-horizon band widens enough that the 1.5 threshold is crossed in 2030 rather than 2033.

### 2.2 Why Ohio moved 2035 → 2031

Same three mechanisms as California. Ohio's pre-L2 bands were narrower than CA's in absolute terms (Ohio has lower initial BEV share and a less dynamic grid), so the same relative widening pushed the crossing year earlier in Ohio (4-year shift) than in California (3-year shift). The direction is consistent; the magnitude is an artefact of Ohio starting closer to the threshold.

## 3. Quantitative claims that remain paper-safe before the boundary

Before the boundary year, the p50 trajectory is a quantitative scenario estimate and the p05–p95 band is a quantitative uncertainty range. Safe claims in this window:

- **California, 2024 – 2029** inclusive:
  - Peak emissions year (2036) is outside this window and therefore not claimed *from* this window; see §5.
  - "Annual ATS energy demand grows from ~3.7 MWh/yr in 2024 to X kWh/yr in 2029 under the baseline scenario" — OK as a p50 with ±(p05, p95) band.
  - "Low-carbon electricity share rises from 0.66 toward its saturation cap by 2030" — OK.
  - Cumulative energy between 2024 and 2029 — OK as sum of annual p50 with reporting of the per-year band.
- **Ohio, 2024 – 2030** inclusive:
  - "Annual ATS energy demand grows from ~X to ~Y in 2030" — OK.
  - "Low-carbon electricity share grows from 0.247 toward ~0.35 by 2030" — OK.
  - Cumulative energy between 2024 and 2030 — OK.

General rule for this window: cite p50 values with explicit p05–p95 bands, make no point-estimate claim without the band, do not extrapolate a narrow band as evidence of confidence beyond the boundary year.

## 4. How post-boundary years must be described

From the boundary year through 2092 (the default horizon) the band width exceeds 1.5 × the median. Point-estimate language is unsafe. Required reframing:

- **Do NOT write**: "By 2050 California's annual ATS emissions are X Mt CO₂."
- **DO write**: "By 2050 California's annual ATS emissions fall within the scenario envelope [p05, p95] ≈ [A, B] Mt CO₂ conditional on the baseline scenario assumptions. This range is a bounded exploratory trajectory rather than a point projection."
- **Do NOT write**: "The low-carbon electricity share reaches X in 2050."
- **DO write**: "Under the baseline scenario assumptions, the modelled low-carbon electricity share saturates at its 1.0 cap near 2040 for California. Post-saturation band narrowing is a cap artefact, not a confidence statement." (See `CA_OH_SATURATION_EVIDENCE.md` for detail.)
- **Do NOT write**: "California achieves emissions peak in 2036 and halves by 2046."
- **DO write**: "Under the baseline scenario, the median emissions trajectory reaches its peak near 2036 and returns to half-peak near 2046. Both years sit beyond the interpretation boundary and should be read as scenario-envelope milestones rather than quantitative predictions." (See §5 for the peak/turning language treatment.)

Canonical wording pair for methods section:

> "We label the scenario as **quantitatively interpretable** before the interpretation boundary (California: 2030; Ohio: 2031 under the baseline scenario at the L2 uncertainty level used in this paper), and as a **scenario envelope** from the boundary year onward. Within the envelope the p05–p95 range spans more than 150 % of the median, so point-estimate language is not supported."

Canonical wording pair for results section when showing a post-boundary value:

> "At 2050 the California ATS-emissions envelope is [A, B] Mt CO₂/yr under the baseline scenario. The boundary year (2030) marks the earliest point at which envelope width exceeds 150 % of the median; values reported from 2030 onward are scenario-conditioned ranges, not point projections."

## 5. Peak and turning years — post-boundary quantities

Both metrics fall beyond the interpretation boundary for CA and OH. They remain **internally consistent** (the 50 %-of-peak rule is defined from the p50 trajectory and the numerical values are reproducible across all codepaths), but they are **derived from a median trajectory whose surrounding envelope is wide**. Acceptable language:

- "**Modelled peak year** under the baseline scenario: California 2036, Ohio 2076 (Ohio peak sits at the horizon edge; see `CA_OH_SATURATION_EVIDENCE.md §Horizon-edge note`)."
- "**Modelled turning year** (the year at which median emissions fall to 50 % of median peak): California 2046. Ohio does not reach the turning threshold within the 2024 – 2092 horizon."

Do not write "California's emissions peak in 2036" without the "modelled under the baseline scenario" caveat, and do not quote a single year as a prediction. Ohio's turning year must be reported as "not reached in horizon", never as a numeric year.

## 6. Version anchoring

- Backend definition: `footprint_model.py`, commit touching step 04E (post-L2).
- Quantile CSVs used: `results/california__policy-baseline__model-fixed_table_quantiles.csv` and `results/ohio__policy-baseline__model-fixed_table_quantiles.csv`, produced by MC 200 @ seed 42.
- Metadata sidecars: `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json`.
- If any of the above regenerates, re-run `compute_interpretation_boundary` and update every figure + caption tied to the boundary year. The boundary year is a computed quantity, not a manuscript constant.

## 7. Cross-codepath consistency

Live validation at the end of step 04E:

| region | backend | v3 dashboard | v4 dashboard |
| --- | ---: | ---: | ---: |
| California | 2030 | 2030 | 2030 |
| Ohio | 2031 | 2031 | 2031 |

All three codepaths use `compute_interpretation_boundary` imported from `footprint_model.py`. Any future divergence is a regression and must fail CI.
