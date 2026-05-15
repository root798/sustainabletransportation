# Reference-style figures — generation note

**Date:** 2026-04-15
**Script:** `scripts/build_refstyle_figures.py`
**Outputs (this folder):**
- `california_2025_2075_refstyle.pdf` + `.png`
- `ohio_2025_2075_refstyle.pdf` + `.png`

---

## Scope

These reproduce the legacy `plot_refstyle_fixed` figure style
(`CLEAR_ATS_uncertainty_notebook.ipynb`, cell
"PLOT FIX — make uncertainty band visible under twinx") but:

- horizon restricted to **2025–2075** (legacy was 2025–2085);
- data sourced from the **current validated baseline** quantile CSVs
  under `results/` (legacy used `results_notebook/` outputs generated
  with an older MC pipeline);
- U.S. Average is not regenerated (paper-safety quarantine).

No policy-conditional MC; baseline only. No U.S. Average.

## Exact inputs

| Region | Quantile CSV used |
|---|---|
| California | `results/california__policy-baseline__model-fixed_table_quantiles.csv` |
| Ohio | `results/ohio__policy-baseline__model-fixed_table_quantiles.csv` |

200 MC runs, seed 42, committed by
`python footprint_model.py --scenarios california ohio --policy baseline --mc 200 --seed 42`.

## Exact columns read

- `Year`
- `ATS Total Power (kWh)_p05`, `_p50`, `_p95`
- `ATS Emissions (kg CO2)_p05`, `_p50`, `_p95`

No other columns are read. No derived series are recomputed on the fly
except for the left-axis ratio overlay (documented below).

## Unit conversions

- Energy: `kWh → TWh` via `value / 1e9` (1 TWh = 10⁹ kWh).
- Emissions: `kg CO₂ → kilo tons CO₂` via `value / 1e6` (1 kt = 10⁶ kg).

Both conversions are identical to the legacy function.

## How the uncertainty range is drawn

For each year in 2025–2075:

1. A grey fill (`color="0.85"`) is drawn on the **left (energy) axis**
   between `ATS Total Power_p05` and `ATS Total Power_p95` after the
   kWh→TWh conversion. `alpha=1.0`, `linewidth=0`.
2. Vertical error bars (`ecolor="0.55"`, `elinewidth=0.9`, `capsize=2.0`,
   `capthick=0.9`) span `[p50 − p05, p95 − p50]` at each integer year on
   the same left axis.
3. On the **right (emissions) axis**, a light red fill at `alpha=0.08`
   spans the emissions `p05`–`p95`, plus red-toned error bars at
   `alpha=0.55` on the emissions median at each year.
4. The right axis `patch.set_visible(False)` so it does not hide the
   left-axis grey band; its `zorder` is raised above `ax1` to keep
   emissions artefacts above energy artefacts where they overlap.

This reproduces the legacy "grey shaded range + grey vertical whiskers
on energy, red whiskers on emissions" visual. The shaded regions are
real p05–p95 quantiles from the current validated MC ensemble; no
symmetric-error approximation is used.

## How the ratio line is drawn

`ratio_raw = p50(ATS Emissions, kg) / p50(ATS Total Power, kWh)` in
units of **kg CO₂ per kWh**. It is rescaled onto the left (energy) axis
purely for visual overlay: `ratio_scaled = ratio_raw × (max(energy p50) / max(ratio_raw))`.
Drawn dotted, `linewidth=2.0`, colour `#006000`. This is the same
rescale used in the legacy function.

## Legend, title, milestones, x-axis

- Legend: top-centre, horizontal, `ncol=4`, frameless, `bbox_to_anchor=(0.5, 1.02)`.
  Order: `Total Power` → `Total Emissions` → `Emissions/Power Ratio` → `Uncertainty Range`.
- Title: `"Annual ATS Energy Consumption and Emissions Prediction for {region} ({y_min}-{y_max})"`.
- Milestone dashed vlines at **2045** and **2075** (both visible in the
  2025–2075 window; 2075 lands at the right edge).
- X-axis ticks every 2 years (odd years), rotated 45°.

## Style constants (verbatim from legacy)

```
POWER_COLOR = "#486878"   # slate blue-grey
EMISS_COLOR = "#8B0000"   # dark red
RATIO_COLOR = "#006000"   # dark green, dotted
UNC_FILL    = "0.85"      # light grey band
UNC_EDGE    = "0.55"      # darker grey whiskers
figsize     = (11.2, 3.4)
font.family = "Arial"
pdf.fonttype / ps.fonttype = 42   # editable text in PDF
```

## Small unavoidable visual deviations from the old reference

1. **Horizon length.** Legacy figure spanned 60 years (2025–2085); this
   revision spans 50 years (2025–2075). Every artefact (lines, band,
   milestones) is correctly clipped to the shorter window; no legacy
   values outside 2025–2075 are shown.
2. **Absolute MC band width.** The current validated MC ensemble
   (post-L2 uncertainty architecture, 200 runs at seed 42) produces
   wider p05–p95 bands than the legacy `DU-REGIONMEAN` variant visible
   in the reference PDF, because additional Layer-2 priors (per-level
   × per-subsystem scale factors, Dirichlet level mixes,
   cohort-decay prior) are now sampled. This is a **data** change, not
   a **style** change.
3. **Median levels.** p50 lines use the current validated MC median;
   they are numerically close to — but not identical to — the legacy
   DU-REGIONMEAN medians. Same reason as above.

The aesthetic style (colours, line weights, legend placement, tick
style, title format, axis structure, twin-axis ratio overlay, whisker
style, milestone markers, font) is a direct copy of the legacy
function. Nothing about the styling was modernised.

## Reproducibility

```
python scripts/build_refstyle_figures.py
```

Reads the two quantile CSVs listed above and writes the four files in
this folder. No other files are touched.
