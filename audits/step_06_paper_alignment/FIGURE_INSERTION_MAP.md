# FIGURE_INSERTION_MAP.md

Mapping from current manuscript figure slots to the CA/OH-only paper-safe figure files produced by `scripts/build_paper_figures.py`. All figures are under `reports/paper_support/figures/{region}/` as `.pdf` (preferred for submission) and `.png` (preview). Captions live under `reports/paper_support/captions/`. This mapping is the single source of truth for the figure-insertion pass — do not insert any figure not listed here.

**Scope rule**: every paper-facing figure slot is California and/or Ohio only. U.S. Average figures are explicitly not listed.

---

## Generated figures currently available

```
reports/paper_support/figures/california/
  ATS_Total_Power_kWh_annual_energy.pdf / .png
  ATS_Emissions_kg_CO2_annual_emissions.pdf / .png
  Clean_Energy_Fraction_clean_energy_share.pdf / .png
  EV_Fraction_bev_share.pdf / .png

reports/paper_support/figures/ohio/
  ATS_Total_Power_kWh_annual_energy.pdf / .png
  ATS_Emissions_kg_CO2_annual_emissions.pdf / .png
  Clean_Energy_Fraction_clean_energy_share.pdf / .png
  EV_Fraction_bev_share.pdf / .png
```

Each PDF carries: p50 median line, p05–p95 shaded band, red-dotted interpretation-boundary marker (2030 CA / 2031 OH), light-red post-boundary shading, brown-dashed saturation marker where applicable, and (emissions panels) modelled-peak marker.

## Slot mapping

| manuscript slot | suggested file(s) | panels if multi-panel | caption file |
| --- | --- | --- | --- |
| **Figure 1** — California ATS energy + emissions trajectory | `california/ATS_Total_Power_kWh_annual_energy.pdf` (top); `california/ATS_Emissions_kg_CO2_annual_emissions.pdf` (bottom) | (a) energy, (b) emissions | `california__annual_energy.txt`, `california__annual_emissions.txt` |
| **Figure 2** — Ohio ATS energy + emissions trajectory | `ohio/ATS_Total_Power_kWh_annual_energy.pdf` (top); `ohio/ATS_Emissions_kg_CO2_annual_emissions.pdf` (bottom) | (a) energy, (b) emissions | `ohio__annual_energy.txt`, `ohio__annual_emissions.txt` |
| **Figure 3** — Low-carbon electricity and BEV-share trajectories (saturation illustration) | `california/Clean_Energy_Fraction_clean_energy_share.pdf`, `ohio/Clean_Energy_Fraction_clean_energy_share.pdf`, `california/EV_Fraction_bev_share.pdf`, `ohio/EV_Fraction_bev_share.pdf` | 2 × 2 grid | `{region}__clean_energy_share.txt`, `{region}__bev_share.txt` |
| **Supplementary Figure S1** — Uncertainty-band widening comparison (pre-L2 vs post-L2) | Generate as a standalone figure during the next supplement stage using the data in `CA_OH_L2_VALIDATION.md §C` | — | — |
| **Supplementary Figure S2** — Structural shock illustration (when Stage 3 ships) | From `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_IMPLEMENTATION.md` | — | — |

## Slots to REMOVE or REPLACE in the current manuscript draft

| current slot | action |
| --- | --- |
| Any "U.S. Average ATS trajectory" figure | **REMOVE entirely** from main text and supplement. The underlying consumption tables are quarantined; see `US_AVERAGE_SOURCE_TRACE.md`. |
| Any "three-region comparison" (CA / OH / US avg) figure or panel | **REPLACE** with a two-region version (CA / OH). If the visual needs a third series for symmetry, use one of the policy variants (aggressive / conservative) instead of US avg. |
| Any pre-revision California / Ohio figure showing the interpretation boundary at 2033 / 2035 | **REPLACE** with the current files listed above (boundary now 2030 / 2031 respectively). |
| Any pre-revision figure labelled "Peak emissions YYYY" without "modelled" | **REPLACE**. All new figures use "Modelled peak year". |
| Any figure whose post-saturation narrow band is presented as a confidence statement | **REPLACE** with the current files, which carry the "cap artefact, not predictability" annotation. |

## Figure-insertion checklist (for the human editor)

For every figure slot in the manuscript:

1. Verify the file exists in `reports/paper_support/figures/{region}/`.
2. Insert the `.pdf` (vector, preferred) or `.png` (rasterized, for draft review).
3. Copy the caption text from `reports/paper_support/captions/{region}__{panel}.txt` verbatim. These captions are machine-generated from the current backend state; do not re-word the boundary year, saturation year, peak year, or turning-year clauses.
4. Prepend the figure number to the caption text (e.g. `Fig. 1: California …`).
5. Confirm that the figure's visual elements match the caption (post-boundary shading present, saturation marker present where the caption mentions one, etc.).
6. If an "old" caption mentions U.S. Average or a three-region comparison, rewrite around it — do not paste.

## Safety assertions

- **No U.S. Average figure is listed above.** If a legacy U.S. Average figure appears in the manuscript, it must be removed; see `TABLE_SANITIZATION.md` for a parallel rule on tables.
- **Every figure boundary year is backend-derived.** If the boundary year changes (e.g. after a future MC regeneration), re-run `python scripts/build_paper_figures.py` and re-import.
- **Every caption is machine-generated.** Manual edits to captions are allowed only for style, not for numeric claims — any numeric change must flow through the figure-builder.

## Related stage outputs

- Captions themselves: `audits/step_06_paper_alignment/CAPTION_ALIGNMENT.md`.
- Table parallels: `audits/step_06_paper_alignment/TABLE_SANITIZATION.md`.
- Reviewer response tied to these figures: `audits/step_06_paper_alignment/REVIEWER_RESPONSE_FINAL.md`.
