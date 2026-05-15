# SCENARIO_FILE_CONVENTION.md

Formal convention for how each region's scenario data is stored and loaded.

## One canonical file per region

```
scenarios/{region}/scenario.json
```

`{region}` is the lowercase region identifier used throughout the codebase (`california`, `ohio`, `us_average`). Additional regions must use the same pattern.

Each region folder also contains:

```
scenarios/{region}/README.md
```

This README documents provenance, headline values, active uncertainty distributions, known L2 gaps, editing notes, and paper-safety status for the region.

## File format

JSON, pretty-printed, UTF-8. Keep 4-space indentation for human readability. One object at top level with these required sections:

- `initial_data`
- `growth_rates`
- `consumption_rates`
- `emission_factors`
- `policy_scenarios`
- `model_variants`
- `data_uncertainty`

The `scenarios/README.md` top-level file describes what each section holds.

## Editing rules

1. Numeric edits go in `scenarios/{region}/scenario.json` and nowhere else.
2. Update the matching `scenarios/{region}/README.md` when an edit changes a headline value or a provenance statement.
3. The `configs/{region}.json` copies are **legacy fallbacks**. Do not maintain them by hand. If an edit is critical and a downstream tool still reads from `configs/`, either (a) copy `scenarios/{region}/scenario.json` over `configs/{region}.json` after the edit, or (b) retire the tool.
4. Do not split sections across files. The whole scenario lives in one JSON.
5. Do not add new top-level sections without adding a matching entry in `scenarios/README.md` and in this convention document.

## Uncertainty-spec placement

Every uncertainty distribution lives under `data_uncertainty.<section>.<key>` inside the same JSON. The structure of `data_uncertainty` mirrors the other sections key-for-key. Example:

```json
"initial_data": { "f_clean": 0.656, ... },
"data_uncertainty": {
  "initial_data": {
    "f_clean": { "dist": "beta", "mean": 0.656, "kappa": 80 }
  }
}
```

### Semantic annotations

When a key's semantic role is not obvious from its name, attach a `"semantic"` string to the spec. Current approved values:

- `"2075_target_fraction"` — for `data_uncertainty.growth_rates.cav` and `.sti` (keys that are mis-named "growth rates" but are actually target fractions).
- `"annual_growth_exponent"` — for `data_uncertainty.growth_rates.ev`, `.clean_energy`, `.total_car_increase`.

Add new semantic tags in this list before introducing them.

### Distribution families supported

Sampled by `footprint_model._sample_distribution`:

| Family | Parameters required |
| --- | --- |
| `"normal"` | `mean`, `sd` (optional `min`, `max` for truncation). |
| `"lognormal"` | `mean` + `sigma` *or* `cv`; or `median` + `sigma`. |
| `"triangular"` | `low`, `mode`, `high`. |
| `"beta"` | `mean` + `kappa`; *or* `alpha` + `beta`; *or* `mean` + `sd`. |
| `"uniform"` | `low`, `high`. |
| `"choice"` / `"discrete"` | `values`, optional `probs`/`weights`. |
| `"dirichlet"` | `alpha` (list). **NOT YET SUPPORTED for list-valued config slots.** Deferred. |

Integer sampling: add `"integer": true` to the spec to coerce to `int(round(...))`.

## Policy overrides

Lives under `policy_scenarios.{policy_name}`. The object is a deep-merge patch applied on top of the base scenario. Baseline policy MUST be present as an empty object:

```json
"policy_scenarios": {
  "baseline": {},
  "aggressive": { "growth_rates": { "ev": 0.2, "clean_energy": 0.1, "efficiency_doubling": 2.0 } },
  "conservative": { "growth_rates": { "ev": 0.05, "clean_energy": 0.02, "efficiency_doubling": 6.0 } }
}
```

Only keys that actually change appear in the patch. Do not pre-fill a patch with unchanged values.

## Load path (code contract)

```
load_base_config(region):
  1. If scenarios/{region}/scenario.json exists, return its parsed content.
  2. Else if configs/{region}.json exists, return its parsed content.
  3. Else raise.
```

Implementations in:

- `footprint_model.load_config`
- `v3_streamlit_app/dashboard_core.load_base_config`
- `v4_streamlit_app/core.load_base_config`

All three follow the same canonical → legacy order.

## Adding a new region

1. Create `scenarios/{new_region}/scenario.json` following the sections above.
2. Create `scenarios/{new_region}/README.md` with provenance, headline values, distributions, and paper-safety status.
3. Update `scenarios/README.md` index.
4. Update v3 `dashboard_core.REGION_ORDER` and `REGION_LABELS` and `REGION_NOTES`.
5. Update v4 `core.REGION_ORDER` and `REGION_LABELS` and `REGION_NOTES`.
6. Optional: copy the same JSON to `configs/{new_region}.json` for legacy tools. Not recommended unless required.

## Forbidden patterns

- **Do not** edit `configs/{region}.json` independently of `scenarios/{region}/scenario.json`. Pick one source of truth. The canonical path is `scenarios/`.
- **Do not** put distribution specs anywhere other than `data_uncertainty.*`. The sampler will not find them elsewhere.
- **Do not** store simulation results or computed metrics inside a scenario file.
- **Do not** hard-code scenario numbers in code. Read from the scenario file.
