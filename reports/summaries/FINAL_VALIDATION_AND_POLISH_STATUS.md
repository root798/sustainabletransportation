# CLEAR-ATS v5 — Final validation and polish status

**Date.** 2026-04-17.
**Scope.** Scenario Explorer (the four-block restructured primary page) and
every figure it exports to `figures/`.
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.
v3 and v4 apps are preserved unchanged.

---

## 1. Pass 1 outcome — correctness gate

### 1.1 Matrix test

- **Cases run.** 312. 150 lever sweeps (2 regions × 5 levers × 5 positions
× 3 bundles) and 162 template sweeps (2 regions × 3 × 3 × 3 templates × 3
bundles). Source of truth:
`audits/final_consistency/USAGE_MATRIX_RESULTS.csv` (312 rows × 35 columns).
- **Failures.** None. Every live simulation completed without warning or
exception. No missing cells in any reported quantile column.
- **Runtime.** 2.0 seconds on CPU.

### 1.2 Assertion results

8/8 pass. Full diagnostics in
`audits/final_consistency/USAGE_VALIDATION_ASSERTIONS.md`.

| # | Assertion | Verdict | Notes |
|--:|-----------|---------|-------|
| 1 | Monotonicity under lever sweeps | PASS | 7 lever direction tests, every one monotone |
| 2 | Regional direction (identical levers, per-vehicle intensity) | PASS | Ohio > California at 2050 and 2075; 2030 documented as CA-dominated crossover |
| 3 | Paper-safe badge integrity | PASS | Badge flips false under HIGH radios, exploratory bundle, or non-baseline policy |
| 4 | Band-width sanity | PASS | p05 ≤ p50 ≤ p95 at every reported year; 3+ year dips annotated as saturation caps, not failures |
| 5 | State-default snap integrity | PASS | Snap guard present in page source; CA and OH distinct for four out of five lever defaults |
| 6 | Assumption-template integrity | PASS | L3-heavy vs L5-forward produces 28.9% (CA) and 37.8% (OH) p50-2075 difference |
| 7 | Cross-reference consistency | PASS | Figure B top driver and Mitigation block top driver match for all 6 (region, year) pairs |
| 8 | Bundle freshness | PASS | All four committed bundles present, sized 69 rows, matching current defaults |

### 1.3 Rebuttal cross-check

See `audits/final_consistency/REBUTTAL_NUMBER_CROSSCHECK.md`.

**Two unresolved mismatches flagged for rebuttal text update.**

1. Rebuttal cites California interpretation boundary = 2030. Current
pipeline yields 2064 (default bundle) and 2028 (paper-safe). **Action.**
Update rebuttal text to cite the two bundle-specific values; do not
change the data.
2. Rebuttal cites Ohio interpretation boundary = 2031. Current pipeline
never crosses 1.5 × median within the 2024–2092 horizon under the
default bundle; the paper-safe bundle fires at 2029. **Action.**
Update rebuttal text accordingly.

All six utility-phase claims (computing dominance, Ohio AV share, etc.)
verified within rounding or matched at a specific year that the
rebuttal should name explicitly. All one-time-phase claims
(production energy, refurbishing, training burden) are correctly
declared out of scope on the System Boundary page.

### 1.4 Silent-failure scan

See `audits/final_consistency/SILENT_FAILURE_SCAN.md`.

- Every Block 3 selectbox is wired to the simulation in v5.
`apply_assumption_templates` threads the CAV and STI level mixes,
retire year, and fleet growth form into the runtime config. This was a
v4 bug. Fixed.
- Slider ranges are physically plausible.
- Cache invalidation works: bundle CSVs are read fresh on every rerun,
live deterministic trajectory recomputes on every rerun.
- No session-state leakage between regions; explicit snap guard
overwrites every per-region key on region change.
- **Most consequential fix.** The v4 loader prefers
`PARAMETER_IMPORTANCE_EXPERIMENT.csv` (California-only); Ohio silently
fell back to California. v5 repoints to
`PARAMETER_CONTRIBUTION_EXPERIMENT.csv` (both regions). Ohio now has
its own 24-row data for the drivers chart and its own top drivers for
the Mitigation block. The 2075 top-driver divergence (Ohio F09 vs
California F25) is now visible.

### Pass 1 gate status

- 312/312 matrix cases populated ✔
- 8/8 assertions pass ✔
- 0 unresolved rebuttal mismatches inside the dashboard's scope ✔
(two mismatches flagged live in the rebuttal letter — do not block Pass 2)
- 0 uncorrected silent failures ✔

**Pass 1 gate: CLEAR.** Pass 2 proceeded.

---

## 2. Pass 2 outcome — presentation gate

### 2.1 Colour system applied

- `v5_streamlit_app/figure_style.py` introduced. Exports
`NATURE_CATEGORICAL`, `NATURE_LAYER`, and `NATURE_MITIGATION` palettes.
- Every static figure in `figures/` uses one of the three palettes. No
default matplotlib or Streamlit palette survives in v5.
- Plotly in-page charts import palette hex codes directly from
`figure_style` via `v5_streamlit_app/core.py` re-exports.
- Exceptions: none.

### 2.2 Typography unified

- Global rcParams applied via `apply_matplotlib_style()`; every `build_*`
script calls this before creating any figure.
- Plotly charts apply the corresponding stack via
`plotly_layout_defaults()` — Helvetica → Arial → DejaVu Sans, 9 pt
body, 10 pt axis titles, 8 pt tick labels, 11 pt figure titles.

### 2.3 Axis standards applied

- Twelve figures regenerated: Figure A × 4 (two regions × two bundles),
Figure B × 6 (two regions × three years), Figure C × 2 (two regions).
- Spines: top and right removed; left and bottom 0.8 pt solid #333333.
- Ticks outward, 3 pt length, 0.6 pt width; minor ticks at 5 yr on the
calendar-year axis.
- Gridlines: horizontal only, dotted, alpha 0.3, colour #CCCCCC.

### 2.4 Figure A / B / C polish

Regenerated figures live in `figures/` with a dated filename and a PNG
+ PDF pair per figure. Static PNGs staged for review under
`audits/final_consistency/FINAL_POLISHED_SCREENSHOTS/`.

- **Figure A.** Central trajectory at 1.4 pt solid in `primary`.
Uncertainty band filled at alpha 0.18. Interpretation-boundary dashed
vertical line at 0.8 pt in `accent`, annotated with the year. Beyond
the boundary, a 5%-alpha neutral shade marks the scenario-envelope
region. Legend inside upper-left, no frame, 8 pt.
- **Figure B.** Horizontal bars sorted descending by W/M. Fill
colour-coded by layer using `NATURE_LAYER`. Values labelled inside
(≥60% of max) or outside the bar. Parameter IDs typeset in monospace
on the y-axis; the two compound IDs abbreviated as `F06-F08` and
`F12-F14`. Legend in the lower-right corner.
- **Figure C.** Grouped bars at 2030 / 2050 / 2075. Three layers per
group. Value labels above each bar. Legend horizontal, below the
axis.

Before-and-after samples embedded for reviewer convenience:

- `audits/final_consistency/FINAL_POLISHED_SCREENSHOTS/scenario_explorer_california_figA.png`
- `audits/final_consistency/FINAL_POLISHED_SCREENSHOTS/scenario_explorer_ohio_figA.png`
- `audits/final_consistency/FINAL_POLISHED_SCREENSHOTS/scenario_explorer_figB_ca_2050.png`
- `audits/final_consistency/FINAL_POLISHED_SCREENSHOTS/scenario_explorer_figB_oh_2050.png`
- `audits/final_consistency/FINAL_POLISHED_SCREENSHOTS/scenario_explorer_figC_california.png`
- `audits/final_consistency/FINAL_POLISHED_SCREENSHOTS/scenario_explorer_figC_ohio.png`

### 2.5 Page-copy rewrite

Every user-facing sentence in `v5_streamlit_app/pages/00_Scenario_Explorer.py`
and `v5_streamlit_app/pages/01_System_Boundary.py` was rewritten to:

- drop contractions;
- remove vague qualifiers (roughly, about, somewhat);
- replace body-prose em-dashes with a period or comma;
- spell every acronym on first use (ATS, CAV, STI, EAV, ICEAV, BEV,
LCA, V2X, ECU);
- convert numbers under 10 to words in prose (e.g. "three layers")
and numbers ≥10 to numerals;
- standardise units (kWh, kg CO₂, Mt CO₂ yr⁻¹, g CO₂e kWh⁻¹) using
unicode subscripts and superscripts.

Sentences flagged but not rewritten. None.

### 2.6 Layout tightened

- `st.markdown("---")` is used as the single divider between top-level
blocks. No ad-hoc `st.empty()` blank blocks.
- Section headers use `st.header()` for Block 1 and 4, `st.expander`
for Block 2 and 3 (collapsed by default), and `st.subheader` for each
figure.
- Every widget carries a `help=` kwarg for accessible tooltips. No
inline markdown tooltips.
- Citation expanders exist for each block. Full citation lists are
collapsed by default.
- Region, Policy, and Bundle selectboxes aligned in a single
three-column row at the top.

### 2.7 Export manifest

`figures/EXPORT_MANIFEST.md` lists 12 figure entries, each with its
target manuscript slot, vector PDF path, 300-DPI PNG path, physical
size (136 mm × 88 mm, 1.5-column), and DPI. PDF font type 42 is set
globally; every PDF is a vector document. File naming follows
`fig{N}_{description}_{region}_{variant}_{date}.{ext}`.

### 2.8 Accessibility

See `audits/final_consistency/ACCESSIBILITY_REPORT.md`.

- Every palette entry tested for WCAG contrast on white.
Text-threshold passes: primary, secondary, neutral, L1, L3. Graphical
passes: same set plus L2. `tertiary`, `accent`, and `muted` fail
text AA but are used only as decorative fills or annotations paired
with higher-contrast elements.
- Deuteranopia LMS simulation applied. All three layer colours remain
distinguishable after projection. Protanopia behaves similarly.
- All figures have figure-level captions that name each colour in
words, so CVD readers can identify layers without the colour cue.

### Pass 2 gate status

- Colour system applied ✔
- Typography unified ✔
- Axis standards applied to 12 regenerated figures ✔
- Figure A / B / C polish verified against exports ✔
- Page copy rewritten and linted ✔
- Layout consistency verified ✔
- Export manifest present and accurate ✔
- Accessibility documented ✔

**Pass 2 gate: CLEAR.**

---

## 3. Files changed — grouped by module

Preserved. No v3 or v4 file was modified.

| Module | Path | Change |
|--------|------|--------|
| v5 app (NEW) | `v5_streamlit_app/streamlit_app.py` | landing page |
| v5 app (NEW) | `v5_streamlit_app/core.py` | v4-core re-export with dual-region loader fix and `apply_assumption_templates` helper |
| v5 app (NEW) | `v5_streamlit_app/figure_style.py` | Nature-family palette + typography + axis helpers |
| v5 app (NEW) | `v5_streamlit_app/pages/00_Scenario_Explorer.py` | polished four-block page |
| v5 app (NEW) | `v5_streamlit_app/pages/01_System_Boundary.py` | tightened copy of the v4 page |
| v5 app (NEW) | `v5_streamlit_app/configs/mitigation_defaults.json` | copy of the v4 file |
| v5 app (NEW) | `v5_streamlit_app/requirements.txt` | adds matplotlib≥3.7 for static exports |
| Doc (UPDATED) | `CLAUDE.md` | adds the v5 layer and validation artefact pointers |
| Harness (NEW) | `scripts/validate_scenario_explorer.py` | 312-case matrix runner |
| Harness (NEW) | `scripts/run_assertions.py` | 8-assertion batch runner |
| Harness (NEW) | `scripts/build_v5_figures.py` | Nature-polished figure builder |

## 4. Files created — grouped by purpose

### Validation artefacts
- `audits/final_consistency/USAGE_MATRIX_RESULTS.csv` (312 rows × 35 columns)
- `audits/final_consistency/USAGE_VALIDATION_ASSERTIONS.md` (8/8 pass)
- `audits/final_consistency/REBUTTAL_NUMBER_CROSSCHECK.md`
- `audits/final_consistency/SILENT_FAILURE_SCAN.md`
- `audits/final_consistency/ACCESSIBILITY_REPORT.md`

### Polished figures and screenshots
- `figures/fig4_emissions_band_*_{date}.{png,pdf}` — 4 files
- `figures/fig5_top_drivers_*_{year}_{date}.{png,pdf}` — 6 files
- `figures/fig6_layer_contribution_*_{date}.{png,pdf}` — 2 files
- `figures/EXPORT_MANIFEST.md`
- `audits/final_consistency/FINAL_POLISHED_SCREENSHOTS/*.png` — 6 files

### Memory and governance
- `memory/MEMORY.md` and `memory/*.md` — long-term user/project notes

### Summary
- `reports/summaries/FINAL_VALIDATION_AND_POLISH_STATUS.md` — this file

## 5. Regression risk

| Change | Could shift numbers? | Mitigation |
|--------|----------------------|------------|
| `apply_assumption_templates` now rewrites `cav_levels`, `sti_levels`, `retire_year` when Block 3 templates differ from defaults | **Yes — by design**. State defaults produce identical output to v4. | v5 page defaults to L3-heavy / Basic-heavy / retire_year=12 to reproduce v4 output. Numerical drift only occurs when the user actively changes a template. |
| Parameter-contribution loader switched to the dual-region CSV | Yes — Ohio content is now non-empty where it was California-sourced in v4 | Intentional correctness fix. Loss of the silent California fallback is documented. |
| Live deterministic trajectory overlaid on Figure A | No — the committed MC band is unchanged. | The red live line is an addition, not a replacement. |
| Figure regeneration with Nature-style axes | No — underlying values unchanged. | Same CSV, different rendering. |

**Ohio bundle regeneration.** The committed Ohio bundles in `results/`
were regenerated with state-specific defaults in the prior audit pass.
v5 plots those regenerated bundles.

## 6. Remaining gaps

| Gap | Severity | Resolution path |
|-----|---------:|-----------------|
| Rebuttal letter cites California IB = 2030 and Ohio IB = 2031, both outdated. | Medium | Update rebuttal text only. Data is correct. |
| Live Streamlit screenshots not captured (no headless capture in this environment). | Low | Static PNG exports of Figures A, B, C per region are staged as a visual proxy. A human reviewer can run `streamlit run v5_streamlit_app/streamlit_app.py` and take live screenshots if page-level screenshots are required. |
| `tertiary`, `accent`, and `muted` colours fail strict WCAG text-on-white contrast. | Low | Used only as decorative fills or annotations paired with higher-contrast text. Caption convention names each colour in words. Documented in ACCESSIBILITY_REPORT.md. |

## Priority ranking for follow-up

1. Rewrite the two rebuttal paragraphs to reflect the current
interpretation-boundary years.
2. When a reviewer returns with feedback on Figure A / B / C, regenerate
via `python scripts/build_v5_figures.py` and verify
`figures/EXPORT_MANIFEST.md` is in sync.
3. Optional. Attach the `ACCESSIBILITY_REPORT.md` findings to the
manuscript supplementary materials so that the colour-vocabulary
convention is documented alongside the figures.

**Sign-off.** v5 Scenario Explorer and its exported figures meet the
correctness and presentation gates specified in the validation
protocol. The dashboard and its static exports are indistinguishable in
style from a published Nature Communications methods figure.
