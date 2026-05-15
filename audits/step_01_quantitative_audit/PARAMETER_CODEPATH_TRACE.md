# PARAMETER_CODEPATH_TRACE.md

Trace of the live execution path for every parameter family that affects quantitative output. Read this alongside `PARAMETER_AUDIT_CURRENT.csv`. All line numbers refer to the current working tree.

Pipeline stages used in this document:

```
[S1] config load (JSON)
[S2] policy deep-merge
[S3] MC sampling (sample_config)
[S4] runtime-control override (dashboards only)
[S5] TransportModel.__init__
[S6] TransportModel.run_simulation loop
[S7] post-processing (compute_scalar_metrics / compute_quantile_summary / compute_turning_metrics)
[S8] CSV write
[S9] dashboard read (load_quantiles / load_quantile_frame)
[S10] dashboard display (charts, metrics cards, tables)
```

## 1. Horizon, base year, and target-reach divisor

| Param | Path |
| --- | --- |
| `--years` CLI default (`68`) | S1 via argparse (footprint_model.py:767) → S5/S6 (`range(years+1)` at L573) |
| `BASE_YEAR = 2024` (v4 core.py:58) | Dashboard metadata only. Not actually consumed by footprint_model.py. |
| Year assignment inside sim | Hard-coded `year = 2024 + t` at footprint_model.py:574, also at L656. **Not** read from BASE_YEAR. |
| `51` target-reach divisor | Hard-coded at footprint_model.py:468 and :477 inside `_update_quantities`. Also appears as a print-trigger at :633. No link to BASE_YEAR or horizon. |
| v3 `DEFAULT_HORIZON_YEARS = 68` | Dashboard only (dashboard_core.py:240), feeds the `years` slider (00_Scenario_Explorer.py:158). |
| v4 `DEFAULT_HORIZON = 68` | Dashboard only (core.py:59), same role. Also used to build `comp_years` in v4 02_State_Results.py:70 as `BASE_YEAR + DEFAULT_HORIZON` (→ 2092 literal). |

**Live path**: `years` slider → S4 `cached_run(signature, years)` → `run_transport_simulation(cfg, years)` → S5/S6. The simulation produces `years + 1` annual rows.

## 2. Policy deep-merge

- S1: `load_base_config(region)` reads `configs/{region}.json` verbatim.
- S2: `load_runtime_config(region, policy)` in both v3 (L278) and v4 (L184) does `deep_merge(base, base['policy_scenarios'][policy])`.
- Keys merged: `growth_rates.ev`, `growth_rates.clean_energy`, `growth_rates.efficiency_doubling` (only these three; baseline override is empty `{}`).
- Keys **NEVER** merged by any committed policy: `initial_data.*`, `emission_factors.*`, `consumption_rates.*`, `growth_rates.cav`, `growth_rates.sti`, `growth_rates.total_car_increase`, `growth_rates.retire_year`, `data_uncertainty.*`, `model_variants.*`.
- CLI: `main()` in footprint_model.py L801 performs the same `_deep_merge(scenario_config, policy_patch)`.

## 3. Monte Carlo sampling path (footprint_model.py only)

CLI path:
1. `args.mc` and seed read (L769–770).
2. `has_inline_dist = has_distribution_spec(scenario_config)` (L793).
3. **`use_sampling = bool(data_uncertainty) or has_inline_dist or args.mc > 0`** (L794). Because every committed config has a `data_uncertainty` block, `use_sampling` is always True.
4. `mc_runs = max(args.mc if args.mc>0 else 1, 1)` (L790–791).
5. Inside the per-run loop (L807–810): `rng = default_rng(seed + run_id)`, then `sampled = sample_config(policy_config, rng)`.
6. `sample_config` (L205–226):
   - Deep-copies input.
   - Calls `_apply_data_uncertainty` on `initial_data` (skipping the `ev_share`/`ev_fraction` keys — L193).
   - Then **separately** samples `data_uncertainty.initial_data.ev_share`, converts with `total_ev = int(round(total_cars * ev_share))` (L217–220).
   - Calls `_apply_data_uncertainty` on each of `growth_rates`, `consumption_rates`, `emission_factors` (L222–224). For `consumption_rates` and `e_clean`, the committed configs provide no spec under those keys → those values pass through unchanged.
   - Calls `resolve_distributions(sampled, rng, skip_keys={'data_uncertainty'})` to convert any remaining inline specs anywhere.
7. The sampled dict feeds `TransportModel(...)`.

**Crucial side-effect**: with `--mc 0` (default) and because `data_uncertainty` exists in every config, step 6 still runs **once** at `seed = 0`. The file named `{region}_results.csv` (when produced by a code path that sets `is_default=True`) is therefore committed only when `is_default = len(policy_items)==1 and len(variants)==1 and mc_runs==1 and not use_sampling`. Under current configs `use_sampling` is True, so `is_default = False` and the CLI writes to `{region}__policy-baseline__model-fixed_table_results.csv` via the prefix path (L830), **not** to `{region}_results.csv`. The existing `{region}_results.csv` files therefore originate from an earlier code state or a separate notebook run — they are not reproducible from the current CLI without removing the `data_uncertainty` block.

Dashboards do **not** call `sample_config`. They only read pre-computed MC artifacts (`*_quantiles.csv`, `*_mc_runs.csv`) and run deterministic re-simulations using the live merged config (no sampling).

## 4. Runtime-control override (dashboards)

Flow (v3 and v4 use the same shape):
1. User interacts with widgets. Each control key maps to a config path through `CONTROL_SPECS[key]["path"]`.
2. `control_values_from_config(cfg, …)` (v3:L299, v4:L194) initializes widget state.
3. `apply_control_values_to_config(base_cfg, cv)` (v3:L340) or `apply_controls(base_cfg, cv)` (v4:L210) writes back to the runtime config.
4. Special case: the `initial_ev_share` key does **not** match any real config field. Both versions branch on the *name* of the key (v3:L350, v4:L219) and compute `total_ev = round(total_cars * ev_share)`. The `path` entry `("initial_data", "total_ev_share")` is metadata only and does not correspond to an actual config key.
5. The adjusted config feeds `run_transport_simulation(cfg, years)` (v3:L373) / `run_simulation(cfg, years)` (v4:L247).

MC uncertainty data (`data_uncertainty`) is **not** re-sampled when users move sliders. Sliders change only the deterministic re-run used for chart lines and turning-point metrics; the quantile band overlay continues to come from a pre-computed CSV keyed by `(region, policy)`. If a user moves any slider away from the committed baseline values, the band and the line no longer match the same scenario — the band is stale for the new line.

## 5. TransportModel initialization (S5)

`__init__` (footprint_model.py:264–324) reads:

- `initial_data.total_cars`, `.total_intersections`, `.total_ev`, `.total_cav`, `.total_sti`, `.f_clean` — live.
- `growth_rates.cav`, `.sti`, `.ev`, `.clean_energy`, `.efficiency_doubling`, `.total_car_increase`, `.retire_year` — live (L282–288). `cav` and `sti` are semantically target fractions but stored under `growth_rates`.
- `consumption_rates.ecav_power`, `.icecav_power_factor`, `.sti_power`, `.cav_levels`, `.sti_levels` — live (L290–294).
- `emission_factors.e_clean`, `.e_fossil`, `.e_gasoline` — live (L309–311).
- `model_variants.adoption_curve` (default `"exponential"`), `.efficiency_curve` (default `"continuous"`), `.ev_t_mid` (default 20), `.ev_carrying_capacity` (default 1.0) — L299–307.
  - `ev_t_mid` and `ev_carrying_capacity` are consumed only by the logistic branch of `_ev_fraction` (L393–399). Because all three committed configs use `adoption_curve="exponential"`, these parameters are **dormant** in live runs.
- `efficiency_model` constructor arg (default `"smooth"`, L272) and `retrofit_share` arg (default 0.0, L273). Both are consumed only by the `partial_retrofit` branch in `_calculate_power` (L502, L524). The CLI passes `variant.get('efficiency_model','smooth')` (L812) and `variant.get('retrofit_share',0.0)` (L813). Because no committed variant sets these keys, they are **dormant**.
- `_initialize_cohorts` (L326–374) uses the magic `decay_factor = 0.7` at L334 to weight cohort age distribution. Not in config.

## 6. run_simulation loop — parameter use by stage

### 6.1 `_update_car_population` (L402–455)
Consumes: `total_cars`, `total_car_increase_rate` (compounded: `total_cars * (1+r)^t` at L411), `retire_year` (via `year_to_retire = t - retire_year`), `ev_frac` (via `_ev_fraction(t)`).

Bug trace: `self.cumulative_new_cars` is initialized at `self.n_cav` (L318). At t=0 the code returns `cumulative_new_cars_t = self.n_cav`. So the "Cumulative New Cars" CSV column at Year 2024 equals the initial CAV count, not 0.

### 6.2 `_ev_fraction(t)` (L390–400)
- `adoption_curve == 'linear'`: `ev_frac + ev_growth_rate * t`, clamped to [0,1].
- `adoption_curve == 'logistic'`: uses `ev_t_mid`, `ev_carrying_capacity`, `ev_frac`, `ev_growth_rate`.
- Default/`exponential`: `ev_frac * (1 + ev_growth_rate)^t`, capped at 1.0.

Numerical note: for CA at `ev_growth=0.07, ev_frac=0.041` the cap (1.0) is hit near t ≈ 47 → year 2071. The "growth rate" behaves as an exponential to saturation, not as a logistic fit.

### 6.3 `_update_quantities` (L457–487)
- `initial_cav_frac = n_cav / total_cars` (L466). Uses initial values.
- **Hard-coded `min(t/51, 1.0)` at L468 and L477** — these set the linear interpolation rate from initial to target (`growth_rates.cav`, `growth_rates.sti`). Comments at L465/L474 say "Reach 95%" and "Reach 50%" — **stale**; actual targets are region/config-specific (CA=0.45/0.5, OH=0.45/0.5, US avg=0.24/0.03). The comment at L467 says "(0.95 from config)" and L476 says "(0.5 from config)" — both stale.
- `f_clean_t = min(f_clean * (1 + clean_growth)^t, 1.0)` (L485). Exponential with hard 1.0 cap. For CA (0.656, 0.05), saturates at ~t=17 → year 2041.

### 6.4 `_calculate_power` (L489–541)
- Iterates `t_add` cohorts from `t - retire_year + 1` to `t`.
- For each cohort: reads `yearly_additions[t_add]['cav']`, computes `eff_factor = cohort_efficiencies[t_add]` (set at cohort add-time in L448).
- Applies `partial_retrofit` correction only if `efficiency_model == 'partial_retrofit'` **and** `retrofit_share > 0` (L502–505). Neither condition is met under committed configs.
- Power tables consumed per level: `ecav_power[L]`, `sti_power[L]`, with level-mix weights `cav_levels[i]`, `sti_levels[i]`.
- `icecav_power_factor` multiplied on I-series (sensing, computing, communication) at L516–518.
- Efficiency factor `eff_factor` multiplied **only** on the `computing` subcomponent, for all three of ECAV/ICECAV/STI (L515, L518, L535). Sensing and communication do not scale with the cohort efficiency factor.
- `MAX_REASONABLE_POWER = 1e15` clip at L537–539 — silent, undocumented, never reached under current magnitudes.

### 6.5 `_calculate_emissions` (L543–569)
Grid blend `blend = f_clean * e_clean + (1 - f_clean) * e_fossil` applied to ECAV and STI (all three subcomponents). ICECAV always multiplied by `e_gasoline` regardless of grid. Aggregates: `cav_emission = e_emission + i_emission`; `ats_emission = cav_emission + s_emission`.

### 6.6 Columns written per year (L584–631)
Names used downstream: `ATS Total Power (kWh)`, `ATS Emissions (kg CO2)`, `ECAV/ICECAV/STI Power (kWh)`, nine subsystem power columns, nine subsystem emission columns, `Total Vehicles`, `Total EV`, `Total ICEV`, `Total CAV`, `Total ECAV`, `Total ICECAV`, `Total Infra`, `Total STI`, `Incremented Car Number`, `EV Fraction`, `Clean Energy Fraction`, `Cumulative New Cars`.

Note the column names still say "Power (kWh)" even though the quantities are annual energies — only the dashboard `DISPLAY_LABEL_MAP` remaps strings at presentation time.

## 7. Post-processing (S7)

### 7.1 `compute_scalar_metrics` (footprint_model.py:678–695)
- `peak_year = argmax(values)`.
- `turning_year = _compute_turning_point(years, values, consecutive_years=5)` — returns first year where **five consecutive subsequent values** are all lower than the previous (L669–675). This is a **different** turning definition from the one used by the dashboards.

### 7.2 `compute_turning_metrics` (v3 dashboard_core.py:529–547 and v4 core.py:395–411)
- `peak_year = argmax(emissions)`.
- `turning_year = first year after peak with emission ≤ 0.5 × peak`.

**Two coexisting definitions** of turning year in the repo: the CSV-side `compute_scalar_metrics` (5-consecutive-drop rule) and the dashboard-side `compute_turning_metrics` (50%-of-peak rule). Numbers in `metrics.csv` are not the same quantity as the "Turning year" displayed in the UI.

### 7.3 `compute_quantile_summary` (footprint_model.py:698–712)
- Stacks all MC runs per column, takes `np.quantile(stacked, [0.05, 0.5, 0.95], axis=0)`.
- Writes `{col}_p05`, `{col}_p50`, `{col}_p95`.

## 8. CSV writes (S8)

- Deterministic per-region file: `results/{region}_results.csv` — written when `is_default=True` in `last_model.save_to_csv(...)` (L858). **Never written by the current CLI** when `data_uncertainty` is present (see §3).
- Prefixed per-scenario file: `results/{region}__policy-{policy}__model-{model}_results.csv` — written when `is_default=True` and prefix not default (L858 path, or when MC ensemble count=1 with the current always-sampling logic).
- MC stacked runs: `results/{region}__policy-{policy}__model-{model}_mc_runs.csv` (L844–845).
- Quantile summary: `..._quantiles.csv` (L847–849).
- Metrics per run: `..._metrics.csv` (L850–852).
- Metrics quantiles: `..._metrics_quantiles.csv` (L853–855).
- Yearly-additions table: `results/yearly_additions_{region}_results.csv` (save_to_csv L653–666). Year field computed as `2024 + year_added`, which produces pre-2024 rows for the initial-cohort negative indices (age = 0..retire_year-1).

## 9. Dashboard read (S9) and display (S10)

- `load_quantile_frame(region, policy, …)` (v3:L598) and `load_quantiles(region, policy)` (v4:L332) both read `results/{region}__policy-{policy}__model-fixed_table_quantiles.csv` and index by `Year`.
- `mc_sample_count(region, policy)` reads the `run_id` column of `..._mc_runs.csv`.
- **Slider moves do not invalidate the quantile overlay** (see §4). The overlay always reflects the committed baseline config, not the live-adjusted slider state.
- `interpretation_boundary(...)`:
  - v3 uses `start_year = INTERPRETATION_BOUNDARY_START_YEAR = 2026` and `threshold = 1.5`.
  - v4 uses `start = INTERP_START_YEAR = 2027` and `threshold = 1.5`.
  - Both compare `(p95-p05)/|p50|` against the threshold.

## 10. Read-back dependency summary

| Value | Config → Merge → Sample → Sim → CSV → Dashboard |
| --- | --- |
| `total_cars` | yes → no → no (not in data_uncertainty) → yes (stock) → yes (`Total Vehicles`) → yes |
| `total_ev` | yes → no → **yes** (derived from `ev_share` beta) → yes (`Total EV` start) → yes → yes |
| `total_cav` | yes → no → no → yes → yes (`Total CAV` start) → yes |
| `total_sti` | yes → no → no → yes → yes (`Total STI` start) → yes |
| `f_clean` | yes → no → **yes** (beta) → yes (`Clean Energy Fraction`) → yes → yes |
| `growth_rates.cav` | yes → no → **yes** (triangular) → yes (CAV target) → propagates into `Total CAV` → yes |
| `growth_rates.sti` | yes → no → **yes** → yes (STI target) → yes → yes |
| `growth_rates.ev` | yes → **yes** (policy override) → **yes** (normal, truncated) → yes (EV fraction) → yes → yes |
| `growth_rates.clean_energy` | yes → **yes** → **yes** (normal, truncated) → yes (`Clean Energy Fraction`) → yes → yes |
| `growth_rates.efficiency_doubling` | yes → **yes** → **yes** (triangular) → yes (cohort factor) → affects `*_Computing_*` only → yes |
| `growth_rates.total_car_increase` | yes → no → **yes** (normal, truncated) → yes (fleet trajectory) → yes → yes |
| `growth_rates.retire_year` | yes → no → **no** (not uncertain) → yes (retirement logic) → yes → yes |
| `consumption_rates.ecav_power.*` | yes → no → **no** (not uncertain) → yes (power tables) → yes → yes |
| `consumption_rates.sti_power.*` | yes → no → **no** → yes → yes → yes |
| `consumption_rates.icecav_power_factor` | yes → no → **no** → yes → yes → yes |
| `consumption_rates.cav_levels` / `sti_levels` | yes → no → **no** → yes (level mix) → yes → yes |
| `emission_factors.e_clean` | yes → no → **no** (not in data_uncertainty) → yes → yes → yes |
| `emission_factors.e_fossil` | yes → no → **yes** (triangular) → yes → yes → yes |
| `emission_factors.e_gasoline` | yes → no → **yes** (triangular) → yes → yes → yes |

"yes" in **Sample** means the parameter has a spec under `data_uncertainty` that is actively applied by `_apply_data_uncertainty` during MC. "no" means it stays at its deterministic value across all MC draws.

## 11. Parameters that are defined but never reach simulation under current configs

| Parameter | Why dead |
| --- | --- |
| `model_variants.ev_t_mid` (default 20) | Requires `adoption_curve='logistic'`; configs use `'exponential'`. |
| `model_variants.ev_carrying_capacity` (default 1.0) | Same as above. |
| `efficiency_model='partial_retrofit'` / `retrofit_share > 0` | Requires non-default efficiency_model in a variant; no committed variant sets this. |
| `CONTROL_SPECS['initial_ev_share']['path'] == ('initial_data','total_ev_share')` | Config key does not exist. Apply-controls branches on key name and writes `total_ev` directly. The `path` entry is vestigial. |
| `_compute_turning_point(..., consecutive_years=5)` for dashboards | Dashboards compute their own 50%-of-peak turning year via `compute_turning_metrics`; the 5-year-decline rule only produces the scalar written to `{region}__..._metrics.csv`. |
| `reasonable_floor = 0.5**(elapsed/100)` in efficiency (L386) | Only active if `efficiency_doubling_years > 100`; current configs use 2.0–6.5. |
| `MAX_REASONABLE_POWER = 1e15` clip | Well above any plausible aggregate power value under current configs. |
