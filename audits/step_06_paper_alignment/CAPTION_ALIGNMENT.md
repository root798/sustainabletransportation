# CAPTION_ALIGNMENT.md

Publication-safe captions for every paper figure (California and Ohio only). These are copied verbatim from the machine-generated caption files under `reports/paper_support/captions/`, then edited only for style (not for numeric claims). **Do not reword boundary years, peak years, turning years, or saturation years** — those are bound to the current backend state and regenerated automatically.

**Peak-year and turning-year attribution convention** (see `METHODS_ALIGNMENT.md §M12`): every peak / turning figure in these captions is sourced from the **deterministic central trajectory** (`footprint_model.py --mc 0`), not from the MC p50 median. The MC p50 trajectory values (CA peak 2038, OH peak 2077) differ by one to two years and appear only in the supplementary MC metrics table. Ohio's MC conditional turning (p50 = 2081 across 87/200 runs, achieved_fraction 0.435) is documented in `METHODS_ALIGNMENT.md §M13` and in the metrics-quantiles CSV; it is **not** used in figure captions.

**Saturation caveat gating** (see `METHODS_ALIGNMENT.md §M5` and sidecar `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json`): the cap-artefact caveat is applied **only** for fields where the sidecar records `reason = band_collapsed_to_zero`. For California BEV share (sidecar: `no_saturation_detected`; max_width 0.869) the caveat is **not** applied; the caption instead notes that the central trajectory approaches the 1.0 cap while the lower tail of the ensemble remains open.

**Paper-safe MC scope** (see `METHODS_ALIGNMENT.md §M14`): every band shown in these captions is sourced from baseline policy MC (200 samples, seed 42). Aggressive and conservative policies are not paper-safe as MC ensembles under the current implementation and are never cited in main-text caption bands.

U.S. Average is not listed. If any legacy U.S. Average caption appears in the manuscript draft, delete it; see `TABLE_SANITIZATION.md` for parallel treatment of tables.

---

## Fig. 1 — California ATS trajectory

### (a) Annual ATS energy demand — California
> California ATS Total Power (kWh) trajectory under the baseline scenario. Solid line: p50 median; shaded band: p05–p95 Monte-Carlo range (N = 200 samples, seed 42). The interpretation boundary at **2030** marks where the p05–p95 width exceeds 150 % of the median; values before this year are quantitatively interpretable, values from this year onward should be read as a scenario envelope rather than point projections.

### (b) Annual ATS CO₂ emissions — California
> California ATS Emissions (kg CO₂) trajectory under the baseline scenario. Solid line: p50 median; shaded band: p05–p95 Monte-Carlo range (N = 200 samples, seed 42). The interpretation boundary at **2030** marks where the p05–p95 width exceeds 150 % of the median; values before this year are quantitatively interpretable, values from this year onward should be read as a scenario envelope rather than point projections. **Modelled peak year 2036; modelled turning year (50 % of median peak) 2046.**

---

## Fig. 2 — Ohio ATS trajectory

### (a) Annual ATS energy demand — Ohio
> Ohio ATS Total Power (kWh) trajectory under the baseline scenario. Solid line: p50 median; shaded band: p05–p95 Monte-Carlo range (N = 200 samples, seed 42). The interpretation boundary at **2031** marks where the p05–p95 width exceeds 150 % of the median; values before this year are quantitatively interpretable, values from this year onward should be read as a scenario envelope rather than point projections. *Horizon-edge note*: the modelled Ohio peak lies within the last 20 years of the 2024–2092 simulation horizon; interpret as a within-horizon extremum, not an asymptote.

### (b) Annual ATS CO₂ emissions — Ohio
> Ohio ATS Emissions (kg CO₂) trajectory under the baseline scenario. Solid line: p50 median; shaded band: p05–p95 Monte-Carlo range (N = 200 samples, seed 42). The interpretation boundary at **2031** marks where the p05–p95 width exceeds 150 % of the median; values before this year are quantitatively interpretable, values from this year onward should be read as a scenario envelope rather than point projections. **Modelled peak year 2076; modelled turning year not reached within horizon.** *Horizon-edge note*: the modelled Ohio peak lies within the last 20 years of the 2024–2092 simulation horizon; interpret as a within-horizon extremum, not an asymptote.

---

## Fig. 3 — Low-carbon electricity and BEV share trajectories (2 × 2)

### (a) California low-carbon electricity share
> California Clean Energy Fraction trajectory under the baseline scenario. Solid line: p50 median; shaded band: p05–p95 Monte-Carlo range (N = 200 samples, seed 42). The interpretation boundary at **2030** marks where the p05–p95 width exceeds 150 % of the median; values before this year are quantitatively interpretable, values from this year onward should be read as a scenario envelope rather than point projections. **The shaded band collapses to zero width after 2040 because the modelled value saturates at its 1.0 cap under every sampled draw; the narrow post-saturation band is a cap artefact, not a predictability claim.**

### (b) Ohio low-carbon electricity share
> Ohio Clean Energy Fraction trajectory under the baseline scenario. Solid line: p50 median; shaded band: p05–p95 Monte-Carlo range (N = 200 samples, seed 42). The interpretation boundary at **2031** marks where the p05–p95 width exceeds 150 % of the median; values before this year are quantitatively interpretable, values from this year onward should be read as a scenario envelope rather than point projections. **The shaded band collapses to zero width after 2075 because the modelled value saturates at its 1.0 cap under every sampled draw; the narrow post-saturation band is a cap artefact, not a predictability claim.** *Horizon-edge note*: peak lies within the last 20 years of the 2024–2092 simulation horizon; interpret as a within-horizon extremum, not an asymptote.

### (c) California BEV share of modeled stock
> California EV Fraction trajectory under the baseline scenario. Solid line: p50 median; shaded band: p05–p95 Monte-Carlo range (N = 200 samples, seed 42). The interpretation boundary at **2030** marks where the p05–p95 width exceeds 150 % of the median; values before this year are quantitatively interpretable, values from this year onward should be read as a scenario envelope rather than point projections. *Late-horizon caveat*: the **p50 central trajectory approaches the 1.0 modelling cap near the horizon edge, while the lower tail of the MC ensemble remains open** (sidecar `reason = no_saturation_detected`; max band width 0.869 across the horizon). The cap-artefact caveat used for the low-carbon electricity share panels (a, b) is **not** applied here.

### (d) Ohio BEV share of modeled stock
> Ohio EV Fraction trajectory under the baseline scenario. Solid line: p50 median; shaded band: p05–p95 Monte-Carlo range (N = 200 samples, seed 42). The interpretation boundary at **2031** marks where the p05–p95 width exceeds 150 % of the median; values before this year are quantitatively interpretable, values from this year onward should be read as a scenario envelope rather than point projections. Ohio's modelled BEV share does not saturate within the 2024–2092 horizon.

---

## Supplementary caption — band-widening validation (to be paired with Supplementary Fig. S1)

> **Pre-L2 vs post-L2 pointwise band widths, California and Ohio baseline, MC 200 at seed 42.** Relative band width (`post / pre`) at three horizon years for ATS Total Power, ATS Emissions, STI Power, and ECAV Power. Post-L2 bands are 9 – 28 % wider across every metric × year sampled. The Layer-2 additions (per-level × per-subsystem ECAV/STI scale factors, Dirichlet level mixes, cohort-decay prior) account for the widening; no change to the p50 median.

## Supplementary caption — U.S. Average quarantine notice (to be pasted into Supplementary Methods)

> **U.S. Average is not a paper-safe region.** The `consumption_rates` sensing and communication cells for U.S. Average diverge by factors of 10 – 30 × from the matching California and Ohio cells under an unresolved source-table mismatch. The corrupted load tables propagate into ATS energy, emissions, peak year, turning year, and interpretation-boundary outputs; none of those derived metrics are cited in the main text or shown in figures. A full per-cell forensic trace is provided in `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`.

---

## Style rules for the copy-in pass

1. Numeric claims in the captions above are **bound to the backend**. Do not paraphrase "2030" or "2040" — the boundary year and saturation year are read from the current Monte-Carlo ensemble and will drift if the ensemble is regenerated. Re-run `scripts/build_paper_figures.py` after any regeneration and re-copy.
2. Remove any pre-revision phrase such as "Peak emissions in YYYY" (without the "modelled" qualifier), "Ohio halves by YYYY" (replace with "not reached within horizon"), or "forecast" (replace with "modelled trajectory").
3. If the journal style requires figure numbers inside the caption, prepend `**Fig. 1.**` / `**Fig. 2a.**` etc. as appropriate.
4. If a panel is re-sized for a two-column layout, re-export from `scripts/build_paper_figures.py` with an explicit `matplotlib` `figsize` override — do not crop the PDF, which would lose the embedded annotation text.

## Do-not-rewrite list (preserved verbatim from the backend)

- "The interpretation boundary at 2030 …" (California)
- "The interpretation boundary at 2031 …" (Ohio)
- "Modelled peak year 2036" (California)
- "Modelled peak year 2076" (Ohio)
- "Modelled turning year (50 % of median peak) 2046" (California)
- "Modelled turning year not reached within horizon" (Ohio)
- "The shaded band collapses to zero width after 2040 … cap artefact, not a predictability claim" (California Clean — sidecar: band_collapsed_to_zero at 2040)
- "The shaded band collapses to zero width after 2075 …" (Ohio Clean — sidecar: band_collapsed_to_zero near 2075)
- "The p50 central trajectory approaches the 1.0 modelling cap near the horizon edge, while the lower tail of the MC ensemble remains open" (California BEV — sidecar: no_saturation_detected)
- "Horizon-edge note: peak lies within the last 20 years of the 2024–2092 simulation horizon …"

Every one of these clauses is emitted by the figure-builder script and must be preserved.
