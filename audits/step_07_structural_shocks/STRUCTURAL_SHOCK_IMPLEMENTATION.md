# STRUCTURAL_SHOCK_IMPLEMENTATION.md

Minimal-viable implementation of the structural-shock family for California and Ohio. All backend changes applied in one pass; no dashboard changes; no manuscript changes.

---

## 1. Files created

- `scenarios/shocks/grid_stall.json`
- `scenarios/shocks/ev_slowdown.json`
- `scenarios/shocks/hardware_supply_shock.json`
- `scenarios/shocks/policy_freeze.json`
- `scenarios/shocks/geopolitical_disruption.json`
- `scenarios/shocks/README.md`

Plus the empty directory `results/shocks/` (populated on first shock run).

## 2. Files modified

**`footprint_model.py`** — three logical additions, all guarded so baseline behaviour is byte-identical:

1. **`TransportModel.__init__`**: new optional `shock_schedule` kwarg. When supplied, instance attributes `self.shock_schedule`, `self.shock_active_years`, `self._f_clean_running`, `self._ev_frac_running` are used to drive a piecewise growth path.
2. **`TransportModel._SHOCK_ATTR_MAP`**: class-level mapping from shock-registry config paths (e.g. `growth_rates.clean_energy`) to `TransportModel` attributes (e.g. `clean_growth_rate`).
3. **`TransportModel._apply_shock_for_year(year)`** + guarded blocks in `_ev_fraction` and `_update_quantities`: when a shock is active, per-year overrides are applied at the start of each simulated year and `f_clean_t` / `ev_frac_t` follow a piecewise cumulative product instead of the constant-rate exponential.
4. **`shock_active` column**: only emitted when `self.shock_schedule` is non-None, so baseline CSV stays at 45 columns.

Module-level helpers:

- `load_shock_registry(shock_name)` — reads and validates `scenarios/shocks/{shock_name}.json`; rejects registries whose `paper_safe_regions` mention `us_average`.
- `build_shock_schedule(shock, severity, onset_year, duration_years, base_year, baseline_cfg)` — pre-expands a severity spec into a per-year dict of attribute overrides, with restore entries at the post-window year for temporary perturbations.
- `run_shock_simulation(region, shock_name, severity, onset_year, duration_years, ...)` — orchestrates a single deterministic shock trajectory; writes outputs per `STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md`.

**CLI additions** (also in `footprint_model.py`):

- `--shock {name|all}` — select a single shock registry or iterate every registry.
- `--severity {mild|moderate|severe}` — defaults to registry's `default_severity`.
- `--onset-year {int}` — defaults to registry's `default_onset_year`.
- `--duration-years {int}` — defaults to registry's `default_duration_years`.
- `--allow-quarantined` — permit shock runs on non-paper-safe regions; outputs land under `results/shocks/quarantined/` with `__QUARANTINED` filename suffix.

When `--shock` is absent, `main()` behaves exactly as it did before this stage.

## 3. Operation semantics

For each perturbation `{"op": ..., "value": ..., "factor": ..., "offset": ...}`:

| op | effect at `onset_year` | effect at `onset_year + duration_years` |
| --- | --- | --- |
| `set_during_window` | attr := value | attr := baseline_value |
| `multiply_during_window` | attr := baseline_value × factor | attr := baseline_value |
| `set_permanent` | attr := value | (no restore) |
| `multiply_permanent` | attr := baseline_value × factor | (no restore) |
| `offset_permanent` | attr := baseline_value + offset | (no restore) |

`target_year` perturbations are mapped to the internal attribute `_target_year_shock`, which `_apply_shock_for_year` translates into a fresh `target_ramp_years = target_year - base_year` for all subsequent year iterations.

## 4. Baseline invariance

- `TransportModel(..., shock_schedule=None)` is the default path and touches no shock attribute beyond assigning `self.shock_schedule = None` and seeding the running accumulators (which are never read in baseline mode because `if self.shock_schedule:` guards the only code paths that consult them).
- `_ev_fraction` and `_update_quantities` each carry a single `if self.shock_schedule:` branch; the baseline path is unchanged.
- The `shock_active` column is emitted only when `self.shock_schedule` is non-None, so baseline CSVs retain the 45-column schema.

Empirical check: refreshing `results/california_results.csv` with `python footprint_model.py --scenarios california --years 68 --policy baseline --mc 0` twice in a row produces bit-identical output (MD5 `f67d6ca3f33f4c2cdf05b9a4f66ace99`). The same hash holds across the shock-backend additions versus a pre-shock snapshot taken in the same session.

## 5. Five-shock × two-region smoke run

`python footprint_model.py --scenarios california ohio --shock all --mc 0` produces 10 result CSVs + 10 provenance JSONs under `results/shocks/`:

```
california__ev_slowdown__moderate__onset-2028__duration-10_results.csv
california__ev_slowdown__moderate__onset-2028__duration-10_provenance.json
california__geopolitical_disruption__moderate__onset-2029__duration-12_results.csv
california__geopolitical_disruption__moderate__onset-2029__duration-12_provenance.json
california__grid_stall__moderate__onset-2030__duration-15_results.csv
california__grid_stall__moderate__onset-2030__duration-15_provenance.json
california__hardware_supply_shock__moderate__onset-2028__duration-08_results.csv
california__hardware_supply_shock__moderate__onset-2028__duration-08_provenance.json
california__policy_freeze__moderate__onset-2032__duration-43_results.csv
california__policy_freeze__moderate__onset-2032__duration-43_provenance.json
ohio__ev_slowdown__moderate__onset-2028__duration-10_results.csv
ohio__ev_slowdown__moderate__onset-2028__duration-10_provenance.json
ohio__geopolitical_disruption__moderate__onset-2029__duration-12_results.csv
ohio__geopolitical_disruption__moderate__onset-2029__duration-12_provenance.json
ohio__grid_stall__moderate__onset-2030__duration-15_results.csv
ohio__grid_stall__moderate__onset-2030__duration-15_provenance.json
ohio__hardware_supply_shock__moderate__onset-2028__duration-08_results.csv
ohio__hardware_supply_shock__moderate__onset-2028__duration-08_provenance.json
ohio__policy_freeze__moderate__onset-2032__duration-43_results.csv
ohio__policy_freeze__moderate__onset-2032__duration-43_provenance.json
```

Impact at **California 2050** (Δ relative to baseline `ATS Emissions`):

| shock | Δ emissions |
| --- | ---: |
| ev_slowdown (moderate) | **+12.1 %** |
| hardware_supply_shock (moderate) | +0.7 % |
| grid_stall (moderate) | +0.0 % at 2050 (clean already saturated; effect visible 2030–2049) |
| policy_freeze (moderate) | **−49.8 %** (fewer CAV/STI → less sensing/computing/communication) |
| geopolitical_disruption (moderate) | **+73.9 %** (compound: slower BEV, slower clean, slower efficiency, faster fleet) |

All signs match the design expectations in `STRUCTURAL_SHOCK_FAMILY_DESIGN.md §2`.

## 6. U.S. Average quarantine enforcement

```
python footprint_model.py --scenarios us_average --shock grid_stall
→  [shock] SKIP us_average/grid_stall/moderate: Region 'us_average' is not paper-safe ...
```

Force path:

```
python footprint_model.py --scenarios us_average --shock grid_stall --allow-quarantined
→  results/shocks/quarantined/us_average__grid_stall__moderate__onset-2030__duration-15__QUARANTINED_results.csv
```

Paper-facing output directory (`results/shocks/` root) receives no U.S. Average file.

## 7. Reproducibility

`python footprint_model.py --scenarios california --shock grid_stall --severity moderate --onset-year 2030 --duration-years 15 --mc 0` run twice produces bit-identical `results/shocks/california__grid_stall__moderate__onset-2030__duration-15_results.csv` (MD5 `0a3df1a6a8dafebc15f02e39067a1565`).

## 8. Deferred items

- `scripts/build_shock_figures.py` — figure builder for shock outputs. Not created this stage; will use `scripts/build_paper_figures.py` as a template.
- `v4_streamlit_app/pages/05_Structural_Shocks.py` — dashboard page for shocks. Not created this stage.
- Stochastic onset-year / duration sampling. Not created.
- Region-correlated multi-region shocks. Not created.
- MC ensemble on top of shock runs (e.g. `--shock grid_stall --mc 200` applies the shock to every MC draw). Current implementation supports single deterministic shocks only; MC + shock is not wired through `sample_config`.

## 9. Known narrow limitations

- `consumption_rates.ecav_scale_factors.computing` perturbation (used by `hardware_supply_shock:severe`) is declared in the registry but not yet implemented: the Stage 3 mapping supports only attributes on the `TransportModel` class. For `severe` the `efficiency_doubling` component still fires; the scale-factor increase is silently skipped with a warning would be appropriate but is not currently emitted. Stage 4 should either drop this perturbation from the severe spec or extend `_SHOCK_ATTR_MAP` to include it.
- `model_variants.target_year` is implemented via the `_target_year_shock` synthetic attr; the mapping recomputes `target_ramp_years` each year. This works for permanent offsets but has not been tested with `set_during_window` on `target_year` (no committed shock uses that combination).
- `shock_active` column is emitted only for shock runs — downstream consumers that union shock CSVs with baseline CSVs must handle the schema difference.
