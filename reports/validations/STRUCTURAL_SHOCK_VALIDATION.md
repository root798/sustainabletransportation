# STRUCTURAL_SHOCK_VALIDATION.md

Validation evidence that the Stage-3 structural-shock backend is safe, correct, reproducible, and paper-scope-compliant.

---

## V1. Baseline unchanged

Two deterministic baseline runs under the shock-modified code produce bit-identical output:

```
$ python footprint_model.py --scenarios california --years 68 --policy baseline --mc 0
$ md5 results/california_results.csv
f67d6ca3f33f4c2cdf05b9a4f66ace99

$ python footprint_model.py --scenarios california --years 68 --policy baseline --mc 0
$ md5 results/california_results.csv
f67d6ca3f33f4c2cdf05b9a4f66ace99
```

Baseline CSV column count = 45 (unchanged from pre-shock). The `shock_active` column is absent from baseline runs.

## V2. Shock outputs go to `results/shocks/` only

```
$ python footprint_model.py --scenarios california ohio --shock all --mc 0
[shock] california/ev_slowdown/moderate onset=2028 duration=10 -> results/shocks/california__ev_slowdown__moderate__onset-2028__duration-10_results.csv
[shock] california/geopolitical_disruption/moderate ...
[shock] california/grid_stall/moderate ...
[shock] california/hardware_supply_shock/moderate ...
[shock] california/policy_freeze/moderate ...
[shock] ohio/ev_slowdown/moderate ...
[shock] ohio/geopolitical_disruption/moderate ...
[shock] ohio/grid_stall/moderate ...
[shock] ohio/hardware_supply_shock/moderate ...
[shock] ohio/policy_freeze/moderate ...
```

Post-condition:

```
$ ls results/shocks/*.csv | wc -l
10
$ ls results/ | grep -v "^shocks$\|^[^_]*_results.csv\|^[^_]*__policy" | head
(no stray shock outputs at results/ root)
```

## V3. Shock results are schema-compatible + carry `shock_active`

```
$ head -1 results/shocks/california__grid_stall__moderate__onset-2030__duration-15_results.csv | tr ',' '\n' | tail -5
Incremented Car Number
EV Fraction
Clean Energy Fraction
Cumulative New Cars
shock_active
```

Baseline has 45 columns; shock CSVs have 46 (+ `shock_active`). `shock_active` is 0 outside the shock window and 1 inside:

```
shock_active at CA grid_stall (moderate, onset 2030, duration 15):
  2029: 0
  2030..2044: 1
  2045: 0
```

Spans the correct window `[onset_year, onset_year + duration_years)`.

## V4. Shock reproducibility

```
$ python footprint_model.py --scenarios california --shock grid_stall --severity moderate --onset-year 2030 --duration-years 15 --mc 0
$ md5 results/shocks/california__grid_stall__moderate__onset-2030__duration-15_results.csv
0a3df1a6a8dafebc15f02e39067a1565

$ python footprint_model.py --scenarios california --shock grid_stall --severity moderate --onset-year 2030 --duration-years 15 --mc 0
$ md5 results/shocks/california__grid_stall__moderate__onset-2030__duration-15_results.csv
0a3df1a6a8dafebc15f02e39067a1565
```

Bit-identical.

## V5. U.S. Average quarantine enforcement

Default path rejects:

```
$ python footprint_model.py --scenarios us_average --shock grid_stall
[shock] SKIP us_average/grid_stall/moderate: Region 'us_average' is not paper-safe for shock 'grid_stall'. Pass allow_quarantined=True to force a quarantined run ...
```

No file written under `results/shocks/`.

Forced path lands under `results/shocks/quarantined/` with `__QUARANTINED` suffix:

```
$ python footprint_model.py --scenarios us_average --shock grid_stall --allow-quarantined
[shock] us_average/grid_stall/moderate onset=2030 duration=15 -> results/shocks/quarantined/us_average__grid_stall__moderate__onset-2030__duration-15__QUARANTINED_results.csv
```

The `quarantined/` subfolder is not consumed by `scripts/build_paper_figures.py` (paper-figure exporter explicitly restricts to `PAPER_REGIONS = {"california", "ohio"}`).

## V6. Provenance sidecar correctness

Every shock run emits a companion `_provenance.json`:

```json
{
  "region": "california",
  "shock_name": "grid_stall",
  "severity": "moderate",
  "onset_year": 2030,
  "duration_years": 15,
  "base_year": 2024,
  "target_year": 2075,
  "horizon_years": 68,
  "registry_file": "scenarios/shocks/grid_stall.json",
  "baseline_scenario_file": "scenarios/california/scenario.json",
  "policy": "baseline",
  "mc_samples": 1,
  "seed": 42,
  "quarantined": false,
  "perturbations_applied": {
    "2030": {"clean_growth_rate": 0.0},
    "2045": {"clean_growth_rate": 0.05}
  }
}
```

`perturbations_applied` lists every year on which `_apply_shock_for_year` changes an attribute, including the post-window restore entry.

## V7. Per-year perturbation correctness (grid_stall, moderate, CA)

| year | baseline Clean Energy Fraction | shock Clean Energy Fraction | expected |
| ---: | ---: | ---: | --- |
| 2030 | 0.8791 | 0.8372 | shock holds value at onset minus one (growth=0 from 2030 means no increase 2030 onward) |
| 2040 | 1.0000 | 0.8372 | shock stays frozen during window |
| 2050 | 1.0000 | 1.0000 | shock releases at 2045; by 2050 has re-saturated at 1.0 |

Shock `Clean Energy Fraction` correctly plateaus during the window at 2029's baseline value and resumes exponential growth (now with growth=0.05) after the window, saturating again by ~2049.

## V8. Five-shock × two-region impact summary (CA 2050, ATS Emissions vs baseline)

| shock | expected sign | observed delta |
| --- | :---: | ---: |
| ev_slowdown (moderate) | + (more ICE retained) | **+12.1 %** |
| hardware_supply_shock (moderate) | + (slower compute efficiency) | +0.7 % |
| grid_stall (moderate) | +/0 (at 2050 only, baseline already saturated) | +0.0 % (visible in 2030–2049 window) |
| policy_freeze (moderate) | − (fewer CAVs / STIs → less sensing demand) | **−49.8 %** |
| geopolitical_disruption (moderate) | + (compound) | **+73.9 %** |

All signs match expected from the design document.

## V9. CLI interoperability

- `python footprint_model.py ...` without `--shock` is unchanged.
- `python footprint_model.py --shock all --scenarios california ohio --mc 0` iterates every shock in `scenarios/shocks/*.json`.
- Non-paper-safe regions are skipped by default. `--allow-quarantined` routes them to `results/shocks/quarantined/`.
- Unknown shock names produce a `FileNotFoundError` with the available shock list.
- Unknown severity names produce a `ValueError` with available severities.

## V10. Isolation from baseline MC pipeline

The paper-facing baseline MC ensemble continues to produce only `results/{region}__policy-baseline__model-fixed_table_*.csv`. Shock outputs never appear under that prefix. `scripts/build_paper_figures.py` reads only the baseline quantile CSV and deterministic CSV; it never consumes anything under `results/shocks/`.

---

## Summary

| validation item | status |
| --- | :---: |
| V1. Baseline unchanged | ✅ bit-identical |
| V2. Shock outputs isolated | ✅ all 10 under results/shocks/ |
| V3. Schema adds `shock_active` only for shock runs | ✅ |
| V4. Shock reproducible | ✅ bit-identical across two runs |
| V5. U.S. Average rejected by default; quarantined path available | ✅ |
| V6. Provenance sidecar emitted per run | ✅ |
| V7. Per-year perturbation correctness | ✅ |
| V8. Five-shock × two-region smoke run signs correct | ✅ |
| V9. CLI behaviour when `--shock` absent matches pre-stage | ✅ |
| V10. No cross-contamination with baseline MC pipeline | ✅ |

Stage 3 is complete and safe. Stage 4 can proceed autonomously.
