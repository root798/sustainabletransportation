# PARAMETER_LEVEL_CONTROL_IMPLEMENTATION.md

**Date:** 2026-04-15
**Scope:** describe the minimum code change that realises parameter-level uncertainty control in the CLEAR-ATS v4 dashboard.
**Referenced:**
- `UNCERTAINTY_PAGE_REDESIGN.md` (UI layout)
- `PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.md` (registry)
- `PARAMETER_LEVEL_PRESET_TABLE.md` (numerical specs)
- `UNCERTAINTY_FIGURE_STYLE_GUIDE.md` (figure colours and rules)

---

## 1. Files added

| Path | Purpose |
|---|---|
| `configs/ui_parameter_presets/_registry_index.json` | registry manifest |
| `configs/ui_parameter_presets/l1_initial_state.json` | F01, F02 |
| `configs/ui_parameter_presets/l1_emission_factors.json` | F03, F04, F05 |
| `configs/ui_parameter_presets/l2_ecav_scale_factors.json` | F06–F11 |
| `configs/ui_parameter_presets/l2_sti_scale_factors.json` | F12–F17 |
| `configs/ui_parameter_presets/l2_dirichlet_mixes.json` | F18, F19 |
| `configs/ui_parameter_presets/l2_other_load.json` | F20, F21, F22 |
| `configs/ui_parameter_presets/l3_2075_targets.json` | F23, F24 |
| `configs/ui_parameter_presets/l3_growth_exponents.json` | F25, F26, F27, F28 |
| `scripts/parameter_contribution_experiment.py` | parameter-level MC |
| `v4_streamlit_app/pages/05_Uncertainty_Parameters.py` | new panel |

## 2. Files modified

- `v4_streamlit_app/core.py` — appended:
  - `UI_PARAM_PRESETS_DIR` constant
  - `load_parameter_registry()` — returns a flat list of parameter records (reads all group JSONs; preserves group/layer attribution).
  - `build_data_uncertainty_from_parameter_choices(choices, region)` — composes a full `data_uncertainty` block from a `{param_id: level}` dict; substitutes `__REGION_MEAN__`, `__REGION_KAPPA__`, `__REGION_KAPPA_X2__`.
  - `apply_parameter_choices(cfg, choices, region)` — returns a copy of `cfg` with `data_uncertainty` overwritten.
  - `parameter_default_choices()` / `parameter_paper_safe_choices()` / `parameter_exploratory_choices()` — three one-click bundles.
  - `validate_parameter_registry()` — startup sanity check: unique config_paths, default/paper_safe in allowed_levels, distribution spec present for non-fixed levels.
  - `load_parameter_contribution_experiment()` / `load_layer_contribution_experiment()` — CSV loaders for Figures B and C.
- No changes to: `footprint_model.py`, existing v4 pages, v3 pages. Existing grouped-layer preset loaders (`load_grouped_uncertainty_preset`) remain present and can still be imported by the archived page, but are not called from the new panel.

## 3. Control flow (data-uncertainty composition)

```
user toggles parameter level in session state
    │  (radio change → st.session_state["unc_p_F01"] = "medium")
    ▼
build_data_uncertainty_from_parameter_choices(choices, region)
    │  ├─ load_parameter_registry() → 28 records
    │  ├─ for each record:
    │  │     level = choices.get(param_id, record.default_level)
    │  │     if level == "fixed": skip (centre value is used from config)
    │  │     else: resolve sentinels, write to merged[config_path]
    │  └─ return merged dict
    ▼
apply_parameter_choices(runtime_cfg, choices, region)
    │  assigns merged dict to cfg["data_uncertainty"]
    ▼
footprint_model.sample_config(cfg, rng)   (unchanged backend)
    ▼
TransportModel.run_simulation(...)  (unchanged backend)
```

No backend (`footprint_model.py`) changes. The existing `_apply_data_uncertainty` recursion handles the per-parameter sampled block without modification — all sampling routes through the canonical `sample_config`.

## 4. UI state model

All state is scoped to the page via `st.session_state` keys:

- `unc_region`, `unc_policy` — region and policy selectors.
- `unc_advanced_mode` — bool; expands all layer sections.
- `unc_p_{param_id}` — one key per parameter, holding the current level choice.
- `unc_param_year` — reporting year for Figure B.

The three quick bundles (`parameter_default_choices`, `parameter_paper_safe_choices`, `parameter_exploratory_choices`) simply overwrite every `unc_p_{pid}` key; Streamlit reruns the script and each parameter radio reads from its new state.

## 5. Validation invariants on startup

`validate_parameter_registry()` runs on page load and, for each record:

1. `param_id` must be unique across all group files.
2. `config_path` must exist in the canonical scenario (reported loosely via the scenario's `data_uncertainty` shape — strict verification is at `sample_config` time).
3. `default_level` and `paper_safe_level` must be in `allowed_levels`.
4. Every non-`fixed` level in `allowed_levels` must have a distribution spec under `levels.<level>`.
5. No distribution label uses an unknown family (checked when the block is built).

Warnings are surfaced via `st.warning` at the top of the panel; they do not block loading.

## 6. Backward compatibility

- The legacy global presets (`configs/ui_presets/uncertainty_{low,medium,high}.json`) are preserved and still loadable via `load_uncertainty_preset(preset, region)`. They are not called from the new panel.
- The earlier layer-grouped presets (`configs/ui_presets/l{1,2,3}_*.json`) are preserved and still loadable via `load_grouped_uncertainty_preset(l1, l2, l3, region)`. They are still referenced by the archived `v4_streamlit_app/pages/04_Uncertainty_Panel.py` page.
- The new parameter-centric panel (`05_Uncertainty_Parameters.py`) is the production page. The `04_Uncertainty_Panel.py` page is retained for comparison; it will be archived in a follow-up cleanup PR.

## 7. Scenario Explorer parity

The old Scenario Explorer interaction spirit is preserved in two ways:

- **Parameter-level radios** give finer-grained control than the previous sliders on target fractions and growth rates.
- **Central values remain editable via Scenario Explorer.** The parameter panel never overwrites central values; it only changes the priors around them. A user who wants to change CAV target to 0.60 still does so in Scenario Explorer; the parameter panel then surrounds that 0.60 with the chosen L3 / F23 level.

## 8. Out of scope for this PR

- Live Monte Carlo recomputation per bundle click (current panel shows the committed baseline `_quantiles.csv`; a future release could add in-panel MC for small sample sizes).
- Regeneration of the committed `results/*_quantiles.csv` with the fixed energy-model call path (separate PR, tracked in `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md` Finding 5).
- US Average consumption-rate anomaly fix (dossier S2-05).
- Joint priors for F29 absolute power cells.
