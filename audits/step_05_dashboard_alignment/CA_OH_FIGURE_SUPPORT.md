# CA_OH_FIGURE_SUPPORT.md

Plotting requirements for California and Ohio paper figures after the L2 redesign. U.S. Average plots must be suppressed in any paper-facing figure (see `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`). Figure implementation is deferred — this document is the specification that the next figure-implementation stage must satisfy.

---

## 1. Scope

Paper-facing figures cover two families, both for CA and OH only:

- **Annual trajectory panels**: ATS Total Energy / year, ATS Emissions / year, ECAV Power, ICECAV Power, STI Power, EV Fraction, Clean Energy Fraction.
- **Scalar summary figures**: peak year, turning year, cumulative energy / emissions over selected windows.

Data sources:

- Quantile bands: `results/{region}__policy-baseline__model-fixed_table_quantiles.csv` (MC 200, seed 42).
- Deterministic median line (fast-path alternative): `results/{region}_results.csv` (`--mc 0`).
- Saturation sidecar: `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json`.
- Interpretation-boundary year: `compute_interpretation_boundary(qf)` from `footprint_model.py` → CA = 2030, OH = 2031 at current state.

## 2. Required visual elements (every annual-trajectory panel)

1. **Median line** — p50 from the quantile CSV (solid line, consistent colour per region).
2. **p05–p95 uncertainty band** — shaded region, same hue as the median line at ~20–30 % opacity.
3. **Interpretation-boundary vertical marker** — dashed vertical line at the boundary year with label `"Interpretation boundary"`.
4. **Post-boundary shaded region** — light grey / hatched overlay spanning `(boundary_year, horizon_end)` with label `"Scenario envelope — bounded exploratory trajectory"`.
5. **Saturation-collapse annotation** — if the field has a non-null `first_saturation_year` in the sidecar:
   - Vertical dotted marker at the saturation year.
   - Text box anchored in the post-saturation region reading `"Band collapse = cap artefact, not predictability"`.
6. **Peak / turning markers** (emissions panel only):
   - Circle at `(peak_year, peak_emissions_p50)`, label `"Modelled peak {year}"`.
   - Dashed horizontal line at `0.5 × peak_emissions_p50` with intersection at turning_year if available, otherwise text `"Turning year not reached within horizon"`.
7. **Horizon-edge caveat** if `peak_year` ≥ `horizon_end − 5` (Ohio case): inset text `"Peak at horizon edge; interpret as within-horizon extremum."`.

## 3. Required caption skeleton

```
{Region} {metric} trajectory under the baseline scenario. Solid line: p50 median;
shaded band: p05–p95 Monte-Carlo range (N = 200 samples). The interpretation
boundary at {boundary_year} marks where the p05–p95 width exceeds 150 % of the
median; values before this year are quantitatively interpretable, values from
this year onward should be read as a scenario envelope rather than point
projections. {Saturation clause if applicable: The shaded band collapses to
zero width after {saturation_year} because the modelled value saturates at its
1.0 cap under every sampled draw; the narrow post-saturation band is a cap
artefact, not a predictability claim.} {Horizon-edge clause if applicable:
Ohio's modelled peak lies within the last decade of the 2024–2092 horizon;
treat as a within-horizon extremum, not an asymptote.}
```

## 4. Figure-level rules

| rule | applies to |
| --- | --- |
| No paper figure may show U.S. Average alongside CA and OH. | all figures |
| Every annual-trajectory figure must include the interpretation-boundary marker. | all annual panels |
| Every figure whose variable appears in the saturation sidecar with a non-null year must carry the saturation annotation. | `Clean Energy Fraction`, `EV Fraction` (CA), ATS / STI / ECAV / ICECAV only if later sidecar flags them. |
| Peak / turning markers are shown on emissions panels but labelled "modelled" not "predicted". | `ATS Emissions` panels |
| Turning year = NaN must render as text `"Not reached in horizon"` — never as a blank line or 0. | Ohio baseline |
| Axis units follow `DISPLAY_LABELS` in the v4 dashboard (`kWh/yr`, `kg CO₂/yr`, etc.), with auto-scale to GWh / MWh / Mt / kt as documented in `v4_streamlit_app/core.py:scale`. | all |
| X-axis: calendar year. Do NOT show t = 0..68. | all |
| Colour palette must stay consistent per region across every figure. | all |
| Band opacity between 0.2 and 0.3. Boundary marker and saturation marker must be distinguishable by line style (dashed vs dotted). | all |

## 5. Dashboard alignment (deferred implementation)

The v4 `pages/00_Scenario_Explorer.py` already draws median + p05–p95 band + interpretation-boundary marker when sliders match the baseline. The missing pieces to add (deferred to the next figure-implementation stage):

- Post-boundary shaded region overlay (currently only a vertical line is drawn).
- Saturation-collapse annotation sourced from the sidecar JSON.
- Peak/turning markers with "modelled" wording.
- Horizon-edge text inset when applicable.

Files that would be touched (for later, not now):

- `v4_streamlit_app/pages/00_Scenario_Explorer.py` — add sidecar load + saturation annotation logic.
- `v4_streamlit_app/pages/03_Turning_Points.py` — add horizon-edge caveat text.
- `v4_streamlit_app/pages/04_Uncertainty_Analysis.py` — add post-boundary shaded region.
- `v4_streamlit_app/core.py` — add `load_saturation_metadata(region, policy)` helper that reads the sidecar JSON. No new backend logic; just a file-loader.

## 6. Paper-figure build script (recommended, not yet implemented)

Recommend creating `scripts/build_paper_figures.py` under the repo root for a later stage. Contract:

```
python scripts/build_paper_figures.py --regions california ohio --outdir reports/paper_support/figures/
```

Reads:

- `results/{region}__policy-baseline__model-fixed_table_quantiles.csv`
- `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json`
- `results/{region}_results.csv`

Writes per-region per-metric PNG + PDF under `reports/paper_support/figures/{region}/{metric}_{panel}.{pdf,png}`, applies the rules in §2–§4, emits caption `.txt` sidecars that follow the skeleton in §3.

No figure has been generated by this script yet; the next stage is expected to implement it using this specification.

## 7. Scalar summary table (recommended figure alternative)

When trajectory figures are not appropriate, use a summary table:

| column | CA baseline | OH baseline |
| --- | :---: | :---: |
| Modelled peak year | 2036 | 2076 (horizon edge) |
| Modelled turning year (50 % of peak) | 2046 | not reached in horizon |
| Interpretation boundary year | 2030 | 2031 |
| Clean-energy-fraction saturation year | 2040 | ~2075 |
| BEV-share saturation year | ~2075 | not in horizon |

Any appearance of "U.S. Average" in such a table must be flagged as `QUARANTINED` per `US_AVERAGE_SOURCE_TRACE.md`.

## 8. What figure changes are now required (summary for the next implementation stage)

1. **Post-boundary shading**: currently only a vertical line marks the boundary; add a hatched region from boundary year → horizon end.
2. **Saturation overlay**: load the new sidecar JSON and render dotted markers + text insets on saturating variables.
3. **Horizon-edge marker**: add explicit inset on Ohio emissions panels.
4. **Label hygiene**: change every "Peak emissions YYYY" and "Turning year YYYY" label to "Modelled peak year YYYY" and "Modelled turning year YYYY".
5. **Region-suppression**: paper-facing figures must not include U.S. Average; add a region allow-list.
6. **Caption automation**: generate caption `.txt` sidecars alongside figure PDFs so the methods / results writer can paste them verbatim.
