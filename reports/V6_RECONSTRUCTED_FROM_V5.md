# V6_RECONSTRUCTED_FROM_V5 — migration note

**Date opened**: 2026-04-19
**v6 path**: `v6_reconstructed/`
**Inheritance source**: `v5_streamlit_app/` (untouched and fully recoverable)
**Replaces**: nothing. v3, v4, v5, and the heavy-rearchitecture v6 (`v6_uncertainty_rearchitecture/`) are all preserved on disk.

This is a **light-touch scientific upgrade**, not a redesign.

---

## A. What is inherited from v5 (bit-exact)

Every file below in `v6_reconstructed/` is byte-identical to its v5 counterpart at the time of forking. The byte-identity check is part of `V6_RECONSTRUCTED_VALIDATION.md §1`.

| v5 file | v6_reconstructed copy | Same bytes? |
| --- | --- | --- |
| `v5_streamlit_app/core.py` | `v6_reconstructed/core.py` | yes |
| `v5_streamlit_app/figure_style.py` | `v6_reconstructed/figure_style.py` | yes |
| `v5_streamlit_app/one_time_data.py` | `v6_reconstructed/one_time_data.py` | yes |
| `v5_streamlit_app/requirements.txt` | `v6_reconstructed/requirements.txt` | yes |
| `v5_streamlit_app/configs/` (all files) | `v6_reconstructed/configs/` | yes |
| `v5_streamlit_app/pages/01_One_Time_Energy.py` | `v6_reconstructed/pages/01_One_Time_Energy.py` | yes |
| `v5_streamlit_app/pages/02_System_Boundary.py` | `v6_reconstructed/pages/02_System_Boundary.py` | yes |

The deterministic `footprint_model.py` simulator and the canonical `scenarios/<region>/scenario.json` files are read from the repo root, exactly as v5 does — no fork.

## B. What was lightly modified (text only)

Two files in `v6_reconstructed/` differ from their v5 counterparts. Both diffs are documentation-only — no calculation, no plot logic, no palette change.

### B.1 `streamlit_app.py` (landing page)

- Title bumped from "v5" to "v6 (light-touch upgrade of v5)".
- "Pages" table extended with five new rows for the v6-added pages.
- Added one short stanza ("v6 design in brief") explaining what was inherited and what was added.

No layout, navigation, or interactive logic changed.

### B.2 `pages/00_Scenario_Explorer.py` (Scenario Explorer)

A single seven-line `st.caption(...)` block added between the existing `st.info(...)` ("This page visualises the **utility phase only**...") and the existing `with st.expander(...)` ("Scope note — read this first"). Content:

> *v6 note · The L1 / L2 layers in Block 4 are within-scenario residual / aleatoric-style variability; L3 is the pathway / epistemic layer that drives long-horizon divergence. Calculations are unchanged from v5; the new vocabulary is documented on the **Uncertainty Definitions** page.*

That is the only change to any inherited page. Verified by `diff` (see validation report §2).

## C. What is newly added in v6_reconstructed

Five new pages live under `v6_reconstructed/pages/`. Numbered 03-07 so the existing v5 pages keep their position in the sidebar.

| File | Purpose | Source data |
| --- | --- | --- |
| `03_Uncertainty_Definitions.py` | Compact taxonomy table mapping L1 / L2 / L3 to epistemic / aleatoric vocabulary; per-layer interpretation block; layer-colour mapping (kept identical to v5). | None — pure documentation. |
| `04_Uncertainty_Architecture.py` | Three-stage schematic (Stage 1 deterministic → Stage 2 propagation → Stage 3 driver / interpretation) drawn in v5 colour language. | None — schematic. |
| `05_Benchmark_Year_Distributions.py` | Violins + density overlay at named milestone years (2035 / 2045 / 2055 / 2075). Region selector. | `results/<region>__policy-baseline__bundle-default_mc_runs.csv` (existing committed bundle). |
| `06_Key_Epistemic_Drivers.py` | Contribution ranking (all layers + L3 sub-ranking + layer summary). Method labelled honestly as `width_over_median`, not Sobol. | `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv` and `LAYER_CONTRIBUTION_EXPERIMENT.csv` (existing audit data). |
| `07_Mitigate_Long_Horizon_Uncertainty.py` | Reviewer-defensibility page: five rules for reading large L3 spread + absolute-vs-relative band-width comparison + deterministic vs envelope companion. | `results/<region>__policy-baseline__bundle-default_quantiles.csv` and `results/<region>_results.csv`. |

All five pages reuse `figure_style.NATURE_CATEGORICAL`, `NATURE_LAYER`, and `plotly_layout_defaults()`. None of them invoke the simulator. None of them mutate any v5 file or any results / scenario / config file.

## D. What was intentionally not changed

- v5 calculations (`core.py`, `one_time_data.py`, all of `footprint_model.py`).
- v5 colour palettes and figure-style helpers.
- v5 page layout, card style, narrative flow, control widgets, and chart arrangement on the existing pages (00 / 01 / 02).
- v5 scenario JSON files under `scenarios/`.
- v5 committed quantile bundles under `results/`.
- v5 uncertainty terminology in code and audit reports — only the dashboard wording on the new pages and the one short caption on the Scenario Explorer use the improved vocabulary.
- v5 uncertainty radio design, Block 4 reset behaviour, band caching, signature hashing.
- The five `scenarios/shocks/*.json` discrete shock files.
- The heavy-rearchitecture v6 directory (`v6_uncertainty_rearchitecture/`) is preserved on disk for reference but is **not imported** by `v6_reconstructed/`.

## E. How to launch v6_reconstructed

```bash
streamlit run v6_reconstructed/streamlit_app.py
```

Uses the same `requirements.txt` as v5. No new pip dependencies.

## F. Comparison: v6_reconstructed vs the heavy-rearchitecture v6

| Concern | `v6_reconstructed/` | `v6_uncertainty_rearchitecture/` |
| --- | --- | --- |
| Source code base | v5_streamlit_app, copied verbatim. | New code from scratch. |
| Calculations changed? | No. | New nested-MC engine wrapping `TransportModel`. |
| Visual language | Identical to v5. | New tabbed dashboard, different navigation. |
| Number of pages added | 5 (additive). | 8 (parallel dashboard). |
| Risk to the v5 paper-facing story | Effectively zero. | Higher: any wording change in the heavy v6 might contradict v5 captions. |
| When to use | Default. Use as the dashboard handed to reviewers. | Reference / methods-development sandbox. |

## G. Migration path forward

Suggested next steps (none required to ship v6_reconstructed):

1. Promote a paper-facing figure from page 05 (benchmark-year distributions) into the SI.
2. Promote a paper-facing figure from page 06 (driver ranking) into the SI.
3. If the manuscript editor requests a Sobol decomposition, port the Sobol code from `v6_uncertainty_rearchitecture/surrogate.py` into a stand-alone CLI script that writes a CSV consumed by page 06. No dashboard rewrite required.

## H. Linked v6 reports

- `reports/UNCERTAINTY_NAMING_AND_INTERPRETATION_V6.md` — naming-decision rationale and L1 / L2 / L3 mapping.
- `reports/V6_RECONSTRUCTED_VALIDATION.md` — the byte-diff and inheritance evidence.
- `reports/UNCERTAINTY_SOURCES_TABLE_V6.md` — compact uncertainty-source table inspired by the Puerto Rico paper's Table 1.
- `reports/UNCERTAINTY_SOURCES_TABLE_V6.csv` — same content in CSV.
