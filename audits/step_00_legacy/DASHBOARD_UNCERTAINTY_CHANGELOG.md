# Dashboard Uncertainty Changelog

## Files Changed

### Config Files (uncertainty input definitions)
- `configs/california.json` - Added `data_uncertainty` section with distributions for initial_data, growth_rates, emission_factors
- `configs/ohio.json` - Added `data_uncertainty` section (same structure, Ohio-specific parameters)
- `configs/us_average.json` - Added `data_uncertainty` section (same structure, US Average-specific parameters)

### Generated Output Files (regenerated)
- `results/california__policy-baseline__model-fixed_table_quantiles.csv` - Now contains non-trivial p05/p50/p95 bands
- `results/california__policy-baseline__model-fixed_table_mc_runs.csv` - 200 MC run results
- `results/california__policy-baseline__model-fixed_table_metrics.csv` - Scalar metrics per run
- `results/california__policy-baseline__model-fixed_table_metrics_quantiles.csv` - Metric quantiles
- `results/ohio__policy-baseline__model-fixed_table_quantiles.csv` - Same for Ohio
- `results/ohio__policy-baseline__model-fixed_table_mc_runs.csv`
- `results/ohio__policy-baseline__model-fixed_table_metrics.csv`
- `results/ohio__policy-baseline__model-fixed_table_metrics_quantiles.csv`
- `results/us_average__policy-baseline__model-fixed_table_quantiles.csv` - Same for US Average
- `results/us_average__policy-baseline__model-fixed_table_mc_runs.csv`
- `results/us_average__policy-baseline__model-fixed_table_metrics.csv`
- `results/us_average__policy-baseline__model-fixed_table_metrics_quantiles.csv`

### Dashboard Core Logic
- `v3_streamlit_app/dashboard_core.py`
  - Added `INTERPRETATION_BOUNDARY_THRESHOLD` constant (1.5)
  - Added `INTERPRETATION_BOUNDARY_START_YEAR` constant (2026)
  - Added `compute_interpretation_boundary()` function: finds the first year where p05-p95 width exceeds 150% of the median

### Scenario Explorer Page
- `v3_streamlit_app/pages/00_Scenario_Explorer.py`
  - Added import of `compute_interpretation_boundary`
  - Computes interpretation boundary when quantile data is available
  - Added red dotted vertical line marking the interpretation boundary on both energy and emissions charts
  - Changed uncertainty band fill alpha from 0.12/0.14 to 0.18/0.20 for better visibility
  - Renamed band traces from "Default-scenario uncertainty band" to "Baseline p05-p95 scenario-conditioned range"
  - Renamed median traces to include "(median trajectory)"
  - Changed metric cards:
    - "Peak annual emissions" -> "Scenario peak emissions" with "(modeled)" suffix
    - "Turning year" -> "Scenario-conditioned turning year"
    - "Final-year ATS energy" -> "Near-term ATS energy (2030)" showing year 2030 instead of final year
    - "Final-year CAV count" -> "Near-term CAV count (2030)" showing year 2030 instead of final year
  - Updated top caption to explain the interpretation boundary concept
  - Updated uncertainty info/caption block with boundary year explanation
  - Updated bottom scientific boundary caption to distinguish near-term quantitative from far-horizon envelope interpretation

## Behavior Changes

1. **Uncertainty bands are now visible**: p05-p95 bands show meaningful spread based on Monte Carlo parameter sampling
2. **Interpretation boundary displayed**: a red dotted vertical line marks where accumulated uncertainty exceeds 150% of the median
3. **Near-term emphasis**: metric cards now show 2030 values instead of final-year values
4. **Wording shift**: all labels and captions avoid "forecast" language; far-horizon outputs described as "scenario-conditioned ranges/envelopes"
5. **Unsupported cases unchanged**: custom slider settings and non-baseline policies still correctly show no fake uncertainty
6. **Legacy notebook exclusion maintained**: notebook quantiles remain excluded from live overlays
