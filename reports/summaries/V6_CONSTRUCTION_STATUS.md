# V6_CONSTRUCTION_STATUS — what was built and what changed

**v6 path**: `v6_streamlit_app/`  (separate from `v5_streamlit_app/` and from the earlier `v6_reconstructed/` and `v6_uncertainty_rearchitecture/` experiments)
**Inheritance**: copy of `v5_streamlit_app/`; calculations and palette unchanged.
**Date opened**: 2026-04-19

---

## A. Architectural changes from v5 to v6

### A.1 Terminology overlay (Change 1)

`v6_streamlit_app/configs/parameter_labels.json` extended with a `metadata` block keyed by F-number. Each entry adds:

- `short_label`
- `f_number`
- `uncertainty_class` ∈ { `aleatoric`, `epistemic` }
- `layer` ∈ { `L1`, `L2`, `L3`, `L1-OT`, `L2-OT` }
- `why_class` (one-sentence honest justification)

Classifications applied (per spec):

- **Aleatoric (bounded; does not compound):** F01, F02 (L1 measured initial state); F03, F04, F05 (L1 emission factors); F09, F10, F11, F15, F16, F17 (L2 vendor / equipment); F18, F19, F20, F21, F22 (L2 load model + fleet).
- **Epistemic (compounds):** F23, F24, F25, F26 (L3 long-horizon — *fixed within each policy scenario in v6*); F27, F28 (L3 hardware / fleet structure); F29, F30, F31 (v6 introductions).

Surfaced in:
- `pages/06_Factor_Legend.py` full glossary
- `sidebar_legend.py` always-visible compact panel on every page
- `pages/00_Scenario_Explorer.py` new caption near the top
- F-number inline legend below figures on pages 03 / 04 / 05

The v5 `labels` and `hidden_reason` blocks are preserved unchanged.

### A.2 Scenario envelope redesign (Change 2)

`v6_streamlit_app/configs/policy_scenarios.json` defines six discrete policy paths:

| ID | Region | F23 cav | F24 sti | F25 BEV growth | F26 LC-elec growth |
| --- | --- | --- | --- | --- | --- |
| ca-committed | CA | 0.45 | 0.50 | 0.07 | 0.05 |
| ca-aggressive | CA | 0.65 | 0.70 | 0.10 | 0.07 |
| ca-delayed | CA | 0.30 | 0.30 | 0.04 | 0.03 |
| oh-status-quo | OH | 0.25 | 0.25 | 0.03 | 0.02 |
| oh-ira-accelerated | OH | 0.40 | 0.35 | 0.06 | 0.04 |
| oh-stalled | OH | 0.15 | 0.15 | 0.01 | 0.01 |

`scenario_definitions.apply_scenario(base_cfg, scenario_id)` writes the `fixed_overrides` and *strips the matching distribution specs from* `data_uncertainty.growth_rates` so `sample_config` cannot later resample them.

Within each scenario the simulator samples:
- All L1+L2 aleatoric priors (F01-F22) under their existing `data_uncertainty` specs.
- F27 hardware doubling time (Triangular(1.5, 2.8, 5.0) yr).
- F31 fleet growth epistemic envelope (truncated normal around F28 default).
- v6 introductions F29 / F30 are sampled into the per-run extras file but NOT yet wired into the simulator equations (documented open item).

The Scenario Explorer page (00) gains a v6 expander in the sidebar that snaps F23-F27 sliders to a chosen policy scenario's targets via session-state writes. v5 slider widgets remain editable; the picker is additive.

### A.3 Three new epistemic parameters (Change 3)

| F | Distribution | Where it lives | Wired? |
| --- | --- | --- | --- |
| **F29** Gasoline price trajectory | Triangular(0.7, 1.0, 1.4) multiplier on EIA AEO 2024 | per-run extras CSV; Sobol design | **No** — recorded but not yet feeding the simulator equations. |
| **F30** Deployment lag | Triangular(1.0, 2.5, 5.0) years | per-run extras CSV; Sobol design | **No** — recorded but not yet feeding the simulator equations. |
| **F31** Fleet growth envelope | Truncated normal(0.002, 0.002, [-0.005, +0.008]) | overrides `growth_rates.total_car_increase` per run | **Yes** — wired. |
| **F27** Hardware doubling | Triangular(1.5, 2.8, 5.0) yr | overrides `growth_rates.efficiency_doubling` per run | Yes (existing). |

F29 and F30 are paper-grade stubs: their priors and metadata exist in v6, the Sobol harness samples them, the bundle generator records each draw, but the simulator equations have not yet been rewritten to consume them. `pages/06_Factor_Legend.py` and `pages/03_Sobol_Sensitivity.py` both flag this honestly.

### A.4 Cross-parameter correlation (Change 4 — out of scope for this build)

Not enabled in v6 because F25 and F26 are now scenario-fixed (correlation between fixed scalars is meaningless). The v5.1 copula plumbing in `footprint_model.sample_config(trajectory_copula=...)` remains unchanged for v5 use.

---

## B. New visualization pages

### B.1 Page 03 — Sobol Sensitivity Analysis

- Backend: `sobol_analysis.py`. SALib Saltelli + Sobol if `SALib` is installed; random-forest importance fallback otherwise. Detection at module load.
- Demo run cached at `v6_streamlit_app/cache/sobol__california__ca-committed__annual_emissions_2050__N64.pkl`.
- Reads from N base size of 32 / 64 / 128 / 256 / 512 / 1024 / 2048; total simulator calls scale as N × (D + 2) where D ≈ 25.
- Top driver in the demo (CA-Committed / annual 2050 emissions, N=64): **F27 Hardware doubling time** with S_T = 0.78. F25 / F26 correctly absent (policy-fixed). Runtime: 7.9 s.
- Visualizations: horizontal top-12 bar chart with class colour, first-order vs interaction stacked bar (top 8), second-order S_ij heatmap (top 8).
- Inline F-number legend populated programmatically below each figure.

### B.2 Page 04 — Distribution Overlay

- Reads `results/<region>__policy-<sid>__v6_metrics.csv` produced by `scripts/build_v6_bundles.py`.
- Histogram-density overlay + violin per scenario + pairwise probability table.
- Targets supported: annual emissions at 2030 / 2035 / 2045 / 2050 / 2055 / 2075, cumulative to 2050 / full horizon, peak emissions, peak year, turning year.

### B.3 Page 05 — Avoided vs Residual

- Reads v6 quantile bundles at the chosen comparison year.
- Stacked subsystem bar (ECAV / STI × sensing / computing / communication) per scenario PLUS narrow companion bar showing residual + avoided vs reference.
- Companion plots: cumulative avoided over time; subsystem decomposition stacked area; key metrics table (cumulative avoided, fraction of reference baseline avoided).

### B.4 Page 06 — Factor Legend

- Full glossary from `parameter_labels.json::metadata`.
- Filters by class and layer; toggle to show v5-hidden parameters.
- Counts table by class × layer.
- Layer colour mapping (kept identical to v5 NATURE_LAYER).

---

## C. Six v6 committed bundles

Generated by `scripts/build_v6_bundles.py --n-runs 80 --seed 42`. Outputs:

| Scenario | runs CSV | quantiles CSV | metrics CSV | extras CSV |
| --- | --- | --- | --- | --- |
| ca-committed | `california__policy-committed__v6_mc_runs.csv` | `..._v6_quantiles.csv` | `..._v6_metrics.csv` | `..._v6_extras.csv` |
| ca-aggressive | `california__policy-aggressive__v6_mc_runs.csv` | … | … | … |
| ca-delayed | `california__policy-delayed__v6_mc_runs.csv` | … | … | … |
| oh-status-quo | `ohio__policy-status-quo__v6_mc_runs.csv` | … | … | … |
| oh-ira-accelerated | `ohio__policy-ira-accelerated__v6_mc_runs.csv` | … | … | … |
| oh-stalled | `ohio__policy-stalled__v6_mc_runs.csv` | … | … | … |

Total runtime: 4.5 s for all six bundles at 80 MC samples each. Scaling to 200 samples per bundle (paper-grade): ~12 s.

All v5 bundles in `results/` left untouched; verified via byte-identity check.

---

## D. v5 inheritance — byte-exact verification

| File | Status |
| --- | --- |
| `v5_streamlit_app/streamlit_app.py` ↔ `v6_streamlit_app/streamlit_app.py` | rewritten (landing page mentions v6) |
| `v5_streamlit_app/core.py` ↔ `v6_streamlit_app/core.py` | identical |
| `v5_streamlit_app/figure_style.py` ↔ `v6_streamlit_app/figure_style.py` | identical |
| `v5_streamlit_app/one_time_data.py` ↔ `v6_streamlit_app/one_time_data.py` | identical |
| `v5_streamlit_app/configs/parameter_labels.json` | extended (added `metadata` block; `labels` + `hidden_reason` unchanged) |
| `v5_streamlit_app/configs/mitigation_defaults.json` | identical |
| `v5_streamlit_app/pages/00_Scenario_Explorer.py` | extended (v6 sidebar legend, v6 caption, v6 policy-scenario picker; 59 line additions, no removals) |
| `v5_streamlit_app/pages/01_One_Time_Energy.py` | extended (v6 sidebar legend; ~10 line additions) |
| `v5_streamlit_app/pages/02_System_Boundary.py` | extended (v6 sidebar legend; ~10 line additions) |

`footprint_model.py` is read from the repo root unchanged.

---

## E. How to launch

```bash
streamlit run v5_streamlit_app/streamlit_app.py            # v5 (port 8501)
streamlit run v6_streamlit_app/streamlit_app.py --server.port 8502  # v6
```

---

## F. Files inventory

```
v6_streamlit_app/
├── streamlit_app.py
├── core.py                          (inherited, identical to v5)
├── figure_style.py                  (inherited, identical to v5)
├── one_time_data.py                 (inherited, identical to v5)
├── requirements.txt                 (inherited, identical to v5)
├── scenario_definitions.py          (NEW)
├── sidebar_legend.py                (NEW)
├── sobol_analysis.py                (NEW)
├── v6_run.py                        (NEW)
├── cache/                           (Sobol pickle cache; gitignore-friendly)
├── configs/
│   ├── mitigation_defaults.json     (inherited, identical to v5)
│   ├── parameter_labels.json        (extended with metadata block)
│   └── policy_scenarios.json        (NEW)
├── pages/
│   ├── 00_Scenario_Explorer.py      (extended)
│   ├── 01_One_Time_Energy.py        (extended)
│   ├── 02_System_Boundary.py        (extended)
│   ├── 03_Sobol_Sensitivity.py      (NEW)
│   ├── 04_Distribution_Overlay.py   (NEW)
│   ├── 05_Avoided_vs_Residual.py    (NEW)
│   └── 06_Factor_Legend.py          (NEW)
└── scripts/
    └── build_v6_bundles.py          (NEW)
```

---

## G. Open items

1. **F29 wiring.** Gasoline price multiplier is sampled but not yet connected to ICEV cost-benefit equations. Documented in `pages/06_Factor_Legend.py` and on Sobol page footer.
2. **F30 wiring.** Deployment lag is sampled but not yet shifting cohort efficiency curves. Documented as above.
3. **Paper-grade Sobol N=2048.** Demo runs at N=64 (~8 s). N=2048 estimated ~5 minutes; user can trigger from page 03 button.
4. **OT phase metadata.** `F-OT-01` through `F-OT-06` carry `L1-OT` / `L2-OT` layer codes for clarity; only the utility-phase F01-F31 set drives Sobol on page 03.

---

## H. Linked v6 documents

- `audits/v6/V6_VALIDATION.md` — assertion pass/fail.
- `reports/V6_REVIEWER_PREMORTEM.md` — anticipated reviewer questions + responses.
