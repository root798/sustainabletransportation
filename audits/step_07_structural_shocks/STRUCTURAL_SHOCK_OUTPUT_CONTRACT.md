# STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md

Output-path and filename contract for structural-shock runs. Must be followed by every CLI / helper that executes a shock so that shock outputs are never mixed with baseline Monte-Carlo artefacts.

---

## 1. Root folder

All shock outputs go under:

```
results/shocks/
```

**Never** write a shock result to `results/` root. **Never** write a shock result under `results_notebook/` (legacy-notebook space).

## 2. Filename convention

For a single deterministic shock run:

```
results/shocks/{region}__{shock_name}__{severity}__onset-{YYYY}__duration-{NN}_results.csv
```

For an optional shock-specific MC ensemble:

```
results/shocks/{region}__{shock_name}__{severity}__onset-{YYYY}__duration-{NN}_mc_runs.csv
results/shocks/{region}__{shock_name}__{severity}__onset-{YYYY}__duration-{NN}_quantiles.csv
results/shocks/{region}__{shock_name}__{severity}__onset-{YYYY}__duration-{NN}_metrics.csv
results/shocks/{region}__{shock_name}__{severity}__onset-{YYYY}__duration-{NN}_metrics_quantiles.csv
results/shocks/{region}__{shock_name}__{severity}__onset-{YYYY}__duration-{NN}_quantiles_metadata.json
```

Example:

```
results/shocks/california__grid_stall__moderate__onset-2030__duration-15_results.csv
```

Fields:
- `{region}` — lowercase region identifier from the scenarios/ tree (`california` or `ohio`; `us_average` is rejected by the CLI).
- `{shock_name}` — matches the `name` field inside the shock registry JSON.
- `{severity}` — one of `mild`, `moderate`, `severe` (or whatever severity keys the registry defines).
- `{YYYY}` — four-digit calendar onset year.
- `{NN}` — zero-padded two-digit duration in years (left-padded if ≥ 10).

## 3. Column contract

Shock result CSVs carry **exactly the same columns** as baseline `results/{region}_results.csv` (49 columns for deterministic single-run; `+ run_id` column for MC ensemble; `_p05/_p50/_p95` suffixes for quantile CSV). This lets any downstream consumer that already knows how to read baseline outputs reuse its code path.

Additional column added by the shock runner:
- `shock_active` (integer 0 / 1) — 1 during `[onset_year, onset_year + duration_years)`, 0 outside. This lets figures shade the active-window visually without re-deriving the window from the filename.

## 4. Provenance sidecar

For every shock run, write:

```
results/shocks/{region}__{shock_name}__{severity}__onset-{YYYY}__duration-{NN}_provenance.json
```

Contents:

```json
{
  "region": "california",
  "shock_name": "grid_stall",
  "severity": "moderate",
  "onset_year": 2030,
  "duration_years": 15,
  "base_year": 2024,
  "target_year": 2075,
  "registry_file": "scenarios/shocks/grid_stall.json",
  "baseline_scenario_file": "scenarios/california/scenario.json",
  "perturbations_applied": {
    "growth_rates.clean_energy": {"op": "set_during_window", "value": 0.0}
  },
  "mc_samples": 1,
  "seed": 42,
  "footprint_model_git_describe": "optional — fill if available",
  "timestamp_iso": "2026-...-..."
}
```

## 5. What the baseline pipeline must NOT do

- Must not write to `results/shocks/`.
- Must not read from `results/shocks/` when assembling baseline quantile CSVs.
- Must not include shock-trajectory samples in any `results/{region}__policy-baseline__model-fixed_table_*.csv`.

## 6. What the shock pipeline must NOT do

- Must not overwrite any baseline file in `results/` root.
- Must not produce a shock run for `us_average` that lands in any paper-facing subdirectory. If `us_average` is requested, the CLI either (a) rejects with an explicit error, or (b) produces the run under `results/shocks/quarantined/` with the suffix `__QUARANTINED` appended to the filename.
- Must not silently merge shock samples into `results/{region}__policy-baseline__model-fixed_table_mc_runs.csv`.

## 7. Paper-support figure-export contract

`scripts/build_paper_figures.py` is baseline-only and must not consume anything from `results/shocks/`. A future `scripts/build_shock_figures.py` will consume shock outputs and emit to:

```
reports/paper_support/figures/shocks/{region}/{shock_name}_{severity}__onset-{YYYY}__duration-{NN}.pdf
reports/paper_support/figures/shocks/{region}/{shock_name}_{severity}__onset-{YYYY}__duration-{NN}.png
reports/paper_support/captions/shocks/{region}__{shock_name}_{severity}__onset-{YYYY}__duration-{NN}.txt
```

Same caption-generation contract as baseline figures: each caption explicitly labels the shock (name, severity, onset, duration) and comparison to the baseline p50 median.

## 8. Dashboard read contract (future)

A future `v4_streamlit_app/pages/05_Structural_Shocks.py` will read:

- `scenarios/shocks/*.json` — shock registry (to populate drop-downs).
- `results/shocks/*_results.csv` — shock deterministic trajectories.
- `results/shocks/*_quantiles.csv` — shock-specific quantile bands (if available; treat as optional).
- `results/shocks/*_provenance.json` — to display shock parameters alongside the chart.

The dashboard must render the shock trajectory on top of the baseline p50 median with a distinctive line style (e.g., dash-dot) and must NOT place the shock trajectory inside the baseline p05–p95 band shading.

## 9. Registry index

`scenarios/shocks/README.md` is the human-readable index. It lists every shock, its narrative, default parameters, severities, and paper scope. The index is hand-maintained; no automatic generator.

## 10. Versioning

- Shock result files carry the onset year and duration in the filename; changing either requires a new file, not a rewrite.
- Shock registry JSONs are version-controlled alongside the rest of the repository.
- Regenerating a shock with the same inputs must produce bit-identical output (same seed, same baseline scenario state).
