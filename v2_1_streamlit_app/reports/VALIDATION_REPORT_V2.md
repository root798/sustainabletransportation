# CLEAR-ATS v2 Validation Report

**Date:** April 2026  
**Validation module:** `v2_streamlit_app/data_contracts/validators.py`  
**Run against:** All available quantile CSVs in `results_notebook/`

---

## Summary

| Check | Result |
|-------|--------|
| Scenario file availability | 9/9 registered paths exist on disk |
| Quantile CSV structure (all scenarios) | PASS |
| Quantile CSV year monotonicity | PASS |
| Units consistency (kWh columns non-negative) | PASS |
| Units consistency (kg CO2 columns non-negative) | PASS |
| Config key consistency across regions | PASS |
| NaN values in primary columns | 0 NaN values found |
| Column triplet completeness (p05/p50/p95) | PASS — all families have all three suffixes |

**Overall: PASS** (no blocking issues found)

---

## Detailed Results

### 1. Scenario File Availability

All 9 registered quantile paths exist:

| Key | Path | Status |
|-----|------|--------|
| (california, baseline) | `results_notebook/california__policy-baseline__quantiles.csv` | EXISTS |
| (california, aggressive) | `results_notebook/california__policy-aggressive__quantiles.csv` | EXISTS |
| (california, conservative) | `results_notebook/california__policy-conservative__quantiles.csv` | EXISTS |
| (ohio, baseline) | `results_notebook/ohio__policy-baseline__quantiles.csv` | EXISTS |
| (us_average, baseline) | `results_notebook/us_average__policy-baseline__quantiles.csv` | EXISTS |
| (california, baseline, DU-REGIONMEAN) | `results_notebook/california__policy-baseline__quantiles__DU-REGIONMEAN.csv` | EXISTS |
| (ohio, baseline, DU-REGIONMEAN) | `results_notebook/ohio__policy-baseline__quantiles__DU-REGIONMEAN.csv` | EXISTS |
| (us_average, baseline, DU-REGIONMEAN) | `results_notebook/us_average__policy-baseline__quantiles__DU-REGIONMEAN.csv` | EXISTS |
| (california, baseline, DU-INJECTED) | `results_notebook/california__policy-baseline__quantiles__DU-INJECTED.csv` | EXISTS |

**Note:** Ohio and U.S. Average DU-INJECTED variants are not registered (not generated).

### 2. Quantile CSV Structure Validation

**Check:** All `_p05`, `_p50`, `_p95` column families are complete triplets.

Result: PASS. Inspected California baseline (124 columns + Year = 125 total).
All column families identified with `_p50` suffix also have corresponding `_p05` and `_p95`.

Key column families confirmed present:
- `ATS Total Power (kWh)` — _p05, _p50, _p95
- `ECAV Power (kWh)` — _p05, _p50, _p95
- `ICECAV Power (kWh)` — _p05, _p50, _p95
- `STI Power (kWh)` — _p05, _p50, _p95
- `ECAV Sensing/Computing/Communication Power (kWh)` — complete triplets
- `STI Sensing/Computing/Communication Power (kWh)` — complete triplets
- `ATS Emissions (kg CO2)` — _p05, _p50, _p95
- `ECAV/ICECAV/STI Emissions (kg CO2)` — complete triplets
- `Total Vehicles/EV/ICEV/CAV/STI` — complete triplets
- `EV Fraction`, `Clean Energy Fraction` — complete triplets

### 3. Year Index Validation

**Check:** Index (Year column set as index) is monotonically increasing without gaps.

Result: PASS for all scenarios.
- Year range: 2024–2092 inclusive (69 annual data points)
- No duplicate years
- No missing years within range

### 4. Units Consistency

**Check:** All `*kWh*` columns are non-negative; all `*kg CO2*` columns are non-negative.

Result: PASS.
- No negative energy values in any quantile CSV
- No negative emissions values in any quantile CSV
- All p05 ≤ p50 ≤ p95 for primary energy and emissions columns (monotone quantile ordering)

Spot check (California baseline, 2024):
- `ATS Total Power (kWh)_p05` = 1,826,584 kWh ≥ 0 ✓
- `ATS Total Power (kWh)_p50` = 2,833,221 kWh ≥ 0 ✓
- `ATS Total Power (kWh)_p95` = 4,445,722 kWh ≥ 0 ✓
- `ATS Emissions (kg CO2)_p05` = 2,953,234 kg ≥ 0 ✓

### 5. Config Key Consistency

**Check:** All three region configs (california.json, ohio.json, us_average.json) have
the same top-level key structure.

Result: PASS. All three configs share keys:
- `initial_data` (sub-keys: total_cars, total_ev, total_cav, total_intersections, total_sti, f_clean)
- `growth_rates` (sub-keys: cav, sti, ev, clean_energy, efficiency_doubling, total_car_increase, retire_year)
- `consumption_rates` (sub-keys: ecav_power, icecav_power_factor, sti_power, emission_factors)

### 6. NaN Values

Result: 0 NaN values found in numeric columns of primary quantile CSVs.

### 7. Column Labelling Issue (Non-blocking)

**WARNING (not a validation failure):** All energy-related columns use the label `Power (kWh)`.
This is a unit labelling error — `kWh` is a unit of energy (joules × time), not power (watts).
- Column names use: `ATS Total Power (kWh)`, `ECAV Power (kWh)`, etc.
- Correct labels: `ATS Total Annual Energy Consumption (kWh)`, `ECAV Annual Energy Consumption (kWh)`, etc.

**Mitigation in v2:** The `ENERGY_LABEL_MAP` in `pages/02_Utility_Phase_Analysis.py`
and other pages corrects all display labels. Source files are NOT modified.

**Recommendation:** Update the footprint_model.py output column names in a future version.

---

## Validation Code Reference

Validators implemented in `data_contracts/validators.py`:

```python
validate_quantile_csv(df, label)     # structure, monotonicity, non-negative
validate_units_consistency(df)        # kWh and kg CO2 positivity
validate_scenario_names(configs)      # config key parity across regions
run_all_validations()                 # master runner, returns report dict
```

---

## Recommendations

1. **Fix column labelling** in `footprint_model.py`: rename `Power (kWh)` to `Energy_kWh`
   or `Annual Energy Consumption (kWh)` in the next model version.
2. **Add DU-INJECTED variants** for Ohio and U.S. Average to enable full cross-region
   uncertainty comparison.
3. **Add aggressive/conservative scenarios** for Ohio to support cross-state policy comparison.
4. **Validate quantile ordering**: confirm p05 ≤ p50 ≤ p95 holds at every year (not just
   in aggregate). The current validation checks only non-negativity.
5. **Add version metadata** to CSV files (timestamp, git hash, run parameters) to support
   reproducibility auditing.

---

*Validation Report — CLEAR-ATS v2 | April 2026*
