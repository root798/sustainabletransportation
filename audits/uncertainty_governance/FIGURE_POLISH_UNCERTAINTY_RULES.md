# FIGURE_POLISH_UNCERTAINTY_RULES.md

**Date:** 2026-04-15
**Scope:** every publication-facing figure in CLEAR-ATS that shows an uncertainty band.

---

## 1. Figure-level rules

1. **Uncertainty must be scoped to the total.** Subsystem decomposition and MC bands must not share a single axis unless the band is explicitly drawn per-subsystem. On the dashboard and in paper-support figures, the MC band always labels the **ATS total**, and filled component areas always label the **live deterministic decomposition**.
2. **Lines vs fills.** On any chart that mixes stacked-area decomposition with a total-level uncertainty band, the stacked traces must have `line.width = 0`. The only visible LINES are genuine total-level objects (deterministic median, MC p50, and the band polygon). This is the post-patch convention from `SCENARIO_EXPLORER_STACK_SEMANTICS.md`.
3. **Uncertainty bands are visually secondary.** Central trajectories are bold and foregrounded; bands use muted alpha ($\le 0.3$) or a grey polygon. Band edges should not use high-saturation colour. On `refstyle` plots, $\alpha = 1.0$ on a light grey ($0.85$) fill is used because it is the reference style.
4. **No stacked-zero on log-y.** When any subsystem reaches exact zero (late-horizon ICECAV), force linear y-axis and surface a short caption. Applies to all subsystem-level charts.
5. **Explicit x-range.** `fig.update_xaxes(range=[xmin, xmax], autorange=False)` on every chart. Auto-range must never be enabled on a chart containing shape-attached annotations (vline / vrect labels).
6. **Every chart declares its source.** Either in the caption below the chart, or in the hover template, the chart must name whether a line is "live deterministic", "MC p50 (baseline only)", or "MC p05–p95 (total)". No silent mixing.

## 2. Legend / annotation rules

1. Legend entries must match the drawn semantics. Stacked fills carry "(share of total)" suffix. Total-level lines carry their source explicitly.
2. Legend unit suffixes must not contradict the y-axis unit. Use `_legend_label()` helper to strip the hard-coded unit parenthetical from legend entries; the y-axis carries the active auto-scaled unit.
3. Annotation anchors are chosen to avoid collisions: 2075 paper-safe marker at `top right`, saturation markers at `bottom right`, cumulative-chart boundary reference (if used) at `top left`.
4. Horizontal legends sit below the plot with `y = -0.28`, `bottom margin = 140 px` (subsystem breakdown: `180 px` for 9 entries). Vertical legends are reserved for pages where horizontal space is tight and the chart is a one-off.

## 3. Uncertainty-only figures (paper-support `refstyle`)

When a figure is intended as a paper-support uncertainty plot only (no subsystem decomposition), the allowed elements are:

- central trajectory (deterministic or MC p50, clearly labelled);
- p05–p95 band;
- optional error whiskers at each year for clarity;
- ratio overlay (dotted, single channel);
- milestone vlines at 2045 and 2075;
- title in the "Annual ATS Energy Consumption and Emissions Prediction for {region} ({y0}-{y1})" format.

Do NOT add on these figures:
- subsystem stacking;
- interpretation-boundary vline;
- scenario-envelope post-boundary vrect;
- saturation markers (those belong to dashboard pages, not paper-support figures);
- dashboard explanatory captions;
- MC/deterministic dual lines (pick one).

This keeps paper-support figures minimal and publication-clean.

## 4. Unit consistency

- Energy series stored in kWh/yr; display via `scale(..., "energy")` which now divides by `1e9` for TWh, `1e6` for GWh, `1e3` for MWh (dossier unit-label fix).
- Emissions series stored in kg CO$_2$/yr; display via `scale(..., "emissions")` which divides by `1e9` for Mt, `1e6` for kt.
- Kilo-tons vs kilotons: use "kilo tons CO$_2$" in the legacy `refstyle` label to match the reference figure; use "kt CO$_2$" in dashboard auto-scale unit. Captions should state one or the other, never both in the same figure.
- Fractions (`EV Fraction`, `Clean Energy Fraction`) are drawn on a pinned $[0, 1.05]$ y-axis.

## 5. Uncertainty across presets

- Any exported figure generated under **LOW** or **MEDIUM** may be used in paper-facing material if the preset is named explicitly in the caption or the provenance sidecar.
- Any figure generated under **HIGH** must carry a visible "exploratory" label on the chart surface (watermark annotation or suffixed title).
- A preset's name must appear in the exported filename: `{region}__{policy}__{preset}__....{pdf,png}`. The `refstyle` builder currently emits without the preset suffix because it uses MEDIUM; any follow-up regeneration under LOW / HIGH must use the suffixed filename.

## 6. Checks performed during figure export

- y-axis label auto-scaled to correct unit (post unit-fix);
- x-axis pinned via `update_xaxes(range=..., autorange=False)`;
- legend has ≤ one entry per drawn object and no stale labels;
- every annotation anchor is within $[xmin, xmax]$ and does not touch another annotation's bounding box;
- bands drawn before lines (zorder < line zorder);
- filled stack traces have `line.width = 0`;
- chart caption names the data source and the preset (for uncertainty plots).
