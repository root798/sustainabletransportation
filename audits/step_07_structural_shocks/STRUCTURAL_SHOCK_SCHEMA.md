# STRUCTURAL_SHOCK_SCHEMA.md

JSON schema for shock registry files under `scenarios/shocks/`. One shock definition per JSON file. Region-agnostic (applies to California and Ohio — U.S. Average is explicitly excluded by the loader).

---

## 1. File layout

```
scenarios/shocks/
├── README.md
├── grid_stall.json
├── ev_slowdown.json
├── hardware_supply_shock.json
├── policy_freeze.json
└── geopolitical_disruption.json
```

Each `{shock_name}.json` holds the canonical shock specification.

## 2. Schema — required keys

```json
{
  "name": "grid_stall",
  "narrative": "Grid decarbonisation stalls due to pipeline, permitting, or fossil-plant life extensions.",
  "paper_scope": "main_text",
  "paper_safe_regions": ["california", "ohio"],
  "default_onset_year": 2030,
  "default_duration_years": 15,
  "default_severity": "moderate",
  "severities": {
    "mild": {
      "label": "Mild — growth reduced 75 %",
      "perturbations": {
        "growth_rates.clean_energy": {"op": "multiply_during_window", "factor": 0.25}
      }
    },
    "moderate": {
      "label": "Moderate — growth frozen",
      "perturbations": {
        "growth_rates.clean_energy": {"op": "set_during_window", "value": 0.0}
      }
    },
    "severe": {
      "label": "Severe — mild reversal",
      "perturbations": {
        "growth_rates.clean_energy": {"op": "set_during_window", "value": -0.01}
      }
    }
  },
  "provenance": {
    "author": "CLEAR-ATS structural shocks stage 2",
    "source_notes": "Expert-elicited; not calibrated to a specific empirical dataset.",
    "decision_file": "audits/step_07_structural_shocks/STRUCTURAL_SHOCK_FAMILY_DESIGN.md"
  }
}
```

## 3. Field-by-field reference

| key | required | type | meaning |
| --- | :---: | --- | --- |
| `name` | yes | string | File-basename-safe identifier. Must match the filename minus `.json`. |
| `narrative` | yes | string | One-sentence plain-language description. Goes into figure captions. |
| `paper_scope` | yes | enum | `main_text` or `supplementary`. Controls whether the shock appears in paper-facing figures by default. |
| `paper_safe_regions` | yes | list of strings | Regions on which this shock may produce paper-facing outputs. Must be a subset of `{"california", "ohio"}`. Extending to other regions requires an audit. |
| `default_onset_year` | yes | int | Year (calendar) at which the shock begins. Must be ≥ `BASE_YEAR` = 2024. |
| `default_duration_years` | yes | int | Duration of the shock window in years. Must be ≥ 1. |
| `default_severity` | yes | string | One of the keys in `severities`. |
| `severities` | yes | object | Map from severity name (`"mild"` / `"moderate"` / `"severe"`) to a severity spec. |
| `provenance` | recommended | object | Free-form metadata. At minimum: `author`, `source_notes`, `decision_file`. |

### 3.1 Severity spec

```json
{
  "label": "Moderate — growth frozen",
  "perturbations": {
    "<config_path>": { "op": "<operation>", "value?": ..., "factor?": ... }
  }
}
```

- `<config_path>`: a dot-delimited path into the baseline scenario config (e.g., `growth_rates.clean_energy`, `consumption_rates.icecav_power_factor`, `consumption_rates.ecav_scale_factors.sensing`).
- `op`: the perturbation operation. Supported operations:
  - `set_during_window` — set the parameter to `value` during the shock window; restore the baseline value after.
  - `multiply_during_window` — multiply the baseline value by `factor` during the shock window; restore after.
  - `set_permanent` — set the parameter to `value` starting at onset and keep it for the remainder of the horizon (no restoration).
  - `multiply_permanent` — multiply at onset and keep permanently.
  - `offset_permanent` — add `offset` at onset and keep permanently (e.g., for `target_year` shifts).

### 3.2 Composite perturbations

A severity may perturb multiple parameters; each entry in `perturbations` is independent. Example from `geopolitical_disruption.json:severe`:

```json
"perturbations": {
  "growth_rates.ev":            {"op": "set_during_window",     "value": 0.0},
  "growth_rates.clean_energy":  {"op": "set_during_window",     "value": 0.0},
  "growth_rates.efficiency_doubling": {"op": "set_during_window", "value": 10.0},
  "growth_rates.total_car_increase":  {"op": "multiply_during_window", "factor": 1.5},
  "emission_factors.e_gasoline":{"op": "multiply_during_window", "factor": 1.1}
}
```

### 3.3 Permanent-shift shocks (e.g., `policy_freeze`)

```json
"perturbations": {
  "growth_rates.cav": {"op": "multiply_permanent", "factor": 0.5},
  "growth_rates.sti": {"op": "multiply_permanent", "factor": 0.5},
  "model_variants.target_year": {"op": "offset_permanent", "offset": 5}
}
```

For `model_variants.target_year`, the offset shifts the 2075 target year to 2080, which slows the CAV/STI ramp in `_update_quantities`.

## 4. Loading and validation rules

- Loader must check `name` against the filename.
- `paper_safe_regions` must be a subset of `{"california", "ohio"}`. If U.S. Average is somehow listed, the loader must reject the shock with an explicit error.
- `default_onset_year` must be in `[BASE_YEAR, BASE_YEAR + DEFAULT_HORIZON - 1]`.
- `default_onset_year + default_duration_years` must be ≤ `BASE_YEAR + DEFAULT_HORIZON`. Overrunning the horizon is allowed only if explicitly noted in `provenance.source_notes`.
- Every `config_path` must resolve in the baseline scenario (loader walks the path and errors if any segment is missing).
- Each `op` must match one of the supported operations above.

## 5. Registry metadata for the paper

A derived registry index lives at `scenarios/shocks/README.md` (to be created at Stage 3) listing every shock with its narrative, default onset / duration, severities, and paper scope.

## 6. Backwards compatibility rules

- Adding a new shock file does NOT affect any baseline output.
- Modifying an existing shock file DOES affect any downstream shock output; regenerate `results/shocks/...` after any edit.
- Removing a shock file removes the associated shock results; the registry README must be updated in the same commit.
- The schema version is implicit (no `version` field) in the first release; a `schema_version` field will be added if the schema changes incompatibly.
