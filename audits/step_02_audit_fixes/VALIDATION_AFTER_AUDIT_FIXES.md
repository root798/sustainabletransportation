# VALIDATION_AFTER_AUDIT_FIXES.md

Evidence that each audit fix is working end-to-end. All commands are runnable from the repo root. Measurements are from 2026-04-12.

---

## A. Deterministic reproducibility

**Test**: run the same deterministic command twice, compare output hashes.

```bash
python footprint_model.py --scenarios california --years 68 --policy baseline --mc 0
md5 results/california_results.csv
# run again
python footprint_model.py --scenarios california --years 68 --policy baseline --mc 0
md5 results/california_results.csv
```

**Result**:
```
A: b24df781eb296583428d6e95ecfd6933
B: b24df781eb296583428d6e95ecfd6933
```

Identical. Under the new `use_sampling = args.mc > 0` rule, `--mc 0` produces a bit-reproducible deterministic run from the baseline config. This closes audit item F1 ("`--mc 0` is not actually deterministic"). The CLI also prints an informative note for each scenario:

```
[california] --mc 0 requested: running nominal deterministic configuration
             (data_uncertainty present but not sampled).
```

## B. Sampled-mode reproducibility and integrity

**Test**: same MC command twice with fixed seed, compare quantile-CSV hashes.

```bash
python footprint_model.py --scenarios california --years 68 --policy baseline --mc 50 --seed 42
md5 results/california__policy-baseline__model-fixed_table_quantiles.csv
# run again
python footprint_model.py --scenarios california --years 68 --policy baseline --mc 50 --seed 42
md5 results/california__policy-baseline__model-fixed_table_quantiles.csv
```

**Result**:
```
A: 327a98ce244977f763d0435a74749c7e
B: 327a98ce244977f763d0435a74749c7e
```

Identical. MC with a fixed seed is still reproducible after all changes. Full ensemble run (`--mc 200 --scenarios california ohio us_average`) completed without error and produced all four artefacts per region (`*_mc_runs.csv`, `*_quantiles.csv`, `*_metrics.csv`, `*_metrics_quantiles.csv`).

A pre-existing crash in `compute_metrics_quantiles` (triggered when non-numeric columns reach `np.quantile`) was fixed as part of the turning-year unification — it now coerces each column via `pd.to_numeric(errors='coerce')` and skips all-NaN columns.

## C. Turning-year consistency across backend, v3, v4

**Test**: compute the turning year for the California baseline from three independent codepaths.

```python
from footprint_model import compute_scalar_metrics
import dashboard_core as v3
import core as v4

df = pd.read_csv("results/california_results.csv")
print(compute_scalar_metrics(df)["turning_year"])   # backend
print(v3.compute_turning_metrics(df)["turning_year"])
print(v4.compute_turning_metrics(df)["turning_year"])
```

**Result**:
```
backend peak_year : 2036 turning_year: 2046.0
v3      peak_year : 2036 turning_year: 2046
v4      peak_year : 2036 turning_year: 2046
```

All three agree on peak (2036) and turning (2046). This closes audit item A2 ("two coexisting turning-year definitions"). The backend helper now also emits `turning_year_rule = "50_percent_of_peak"` as a tag in `compute_scalar_metrics`.

## D. Interpretation-boundary consistency across backend, v3, v4

**Test**: compute the interpretation boundary for the California baseline quantile CSV from three codepaths.

```python
from footprint_model import compute_interpretation_boundary, INTERP_BOUNDARY_START_YEAR
qf = pd.read_csv("results/california__policy-baseline__model-fixed_table_quantiles.csv").set_index("Year")
print(compute_interpretation_boundary(qf)["boundary_year"])
print(v3.compute_interpretation_boundary(qf)["boundary_year"])
print(v4.interpretation_boundary(qf)["year"])
```

**Result**:
```
backend boundary: 2043 threshold: 1.5 start: 2027
v3      boundary: 2043
v4      boundary: 2043

v3 INTERPRETATION_BOUNDARY_START_YEAR = 2027
v4 INTERP_START_YEAR                  = 2027
backend INTERP_BOUNDARY_START_YEAR    = 2027
```

All three agree on 2043. Start-year constants are unified at 2027. This closes audit item A1 ("interpretation-boundary start year differs v3 vs v4").

## E. U.S. Average anomaly status

Not automatically resolved. The US-avg consumption anomaly remains in `configs/us_average.json` verbatim — no silent numerical patch was applied.

- v3 `REGION_NOTES[us_average]` and v4 `REGION_NOTES[us_average]` now warn explicitly that U.S. Average load figures are not paper-safe.
- `US_AVERAGE_DECISION_NOTE.md` documents the numerical pattern (sensing/communication inflated 10–30×, computing in-range) and candidate explanations.
- Recommended next action logged: trace consumption tables to source or regenerate as true CA/OH midpoint.

Paper-facing implication: until this is resolved, do not cite U.S. Average energy, emissions, or intensity numbers.

## F. Uncertainty-overlay honesty under slider motion

**v4 `00_Scenario_Explorer.py`**:
- When `show_unc=True` and controls match baseline and `policy=="baseline"` → overlay shown.
- When `show_unc=True` and controls differ from baseline → overlay suppressed, `st.warning(...)` displayed explaining why.
- When `show_unc=True` and `policy != "baseline"` → overlay suppressed, `st.info(...)` explaining per-policy MC ensembles have not been committed.

**v3 `00_Scenario_Explorer.py`**:
- `default_quantiles_match` gate already existed and blocked overlay when sliders moved.
- New behaviour: if the overlay is suppressed because sliders moved, an `st.warning(...)` (stronger than the previous `st.info(...)`) tells the user the precomputed band would not match the live line.
- If the overlay is suppressed because no quantile CSV exists on disk, the old `st.info(...)` message is retained.

## G. Distribution-sampling validity

Smoke-test quantile widths (`p95 − p05`) on the refreshed `california__policy-baseline__model-fixed_table_quantiles.csv` (68y, mc=200, seed=42):

| Column | max band width | min width ≥ 2030 | notes |
| --- | ---: | ---: | --- |
| ATS Total Power (kWh) | 8.93e+09 | 2.76e+09 | non-zero, wide — healthy |
| ATS Emissions (kg CO2) | 1.28e+10 | 2.03e+09 | non-zero, wide |
| ICECAV Power (kWh) | 7.98e+09 | 1.13e+09 | non-zero — validates new `icecav_power_factor` and `retire_year` distributions are sampling |
| Total ECAV | 3.01e+07 | 5.20e+04 | non-zero |
| Clean Energy Fraction | 0.266 | **0.0** post-saturation | expected — exponential trajectory caps at 1.0. Saturation artifact documented in DISTRIBUTION_PROBLEMS_REPORT §Severity 3. |

No distribution produced malformed samples. The `compute_metrics_quantiles` path correctly skips the non-numeric `turning_year_rule` tag column.

## H. Regenerated artefacts

After all fixes:

```
results/california_results.csv          — 52 KB (deterministic baseline, regenerated)
results/ohio_results.csv                — 54 KB
results/us_average_results.csv          — 52 KB
results/california__policy-baseline__model-fixed_table_quantiles.csv  — 158 KB (200 MC, seed 42)
results/california__policy-baseline__model-fixed_table_mc_runs.csv    — (200 MC rows × 69 years × 45 columns)
results/{ohio,us_average}__policy-baseline__model-fixed_table_*       — refreshed
results/yearly_additions_{region}_results.csv                         — regenerated with corrected year arithmetic
```

Note: paper figures cut from earlier CSV versions may show `Cumulative New Cars` at 2024 equal to the initial CAV count (old behaviour). Regenerated CSVs now show 0 at 2024. See §5 of `SEMANTIC_ALIGNMENT_CHANGELOG.md`.

## I. Summary — green checks

| Validation item | Status |
| --- | --- |
| Deterministic `--mc 0` reproducible | ✓ bit-identical across two runs |
| MC with fixed seed reproducible | ✓ bit-identical |
| Turning-year consistent (backend, v3, v4) | ✓ all three return 2046 (CA baseline) |
| Interpretation-boundary consistent (backend, v3, v4) | ✓ all three return 2043; start-year 2027 everywhere |
| New L2 distributions (`e_clean`, `icecav_power_factor`, `retire_year`) sampling | ✓ non-zero bands on ICECAV Power confirm |
| Slider-off-baseline overlay suppression with warning | ✓ both v3 and v4 |
| U.S. Average anomaly handled | ⚠ documented, not silently fixed; region marked non-paper-safe |
| Pre-existing `compute_metrics_quantiles` non-numeric crash | ✓ fixed |
| Saturation-artifact collapse of `Clean Energy Fraction` band | ⚠ acknowledged; deferred to UX stage |
