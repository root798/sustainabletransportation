# SEMANTIC_ALIGNMENT_CHANGELOG.md

Semantic alignment changes applied during the audit-fix stage, grouped by theme.

---

## 1. Source-of-truth constants (backend → dashboards)

Added to `footprint_model.py` (top of module):

```python
BASE_YEAR = 2024
TARGET_YEAR = 2075
TARGET_RAMP_YEARS = TARGET_YEAR - BASE_YEAR            # = 51

INTERP_BOUNDARY_THRESHOLD = 1.5
INTERP_BOUNDARY_START_YEAR = 2027
INTERP_BOUNDARY_METRIC = "ATS Emissions (kg CO2)"

TURNING_YEAR_DECLINE_RATIO = 0.5
```

Both `v3_streamlit_app/dashboard_core.py` and `v4_streamlit_app/core.py` now import these names directly. The previous `INTERPRETATION_BOUNDARY_START_YEAR = 2026` (v3) and `INTERP_START_YEAR = 2027` (v4) are retired in favour of the single backend constant (unified at 2027 — the v4 value, because the rationale "skip 3 years where small values inflate ratios" is sounder).

Both dashboards now compute the interpretation boundary by delegating to `footprint_model.compute_interpretation_boundary`; their local wrappers only adapt the return-key shape for backward compatibility.

## 2. Calendar semantics

- `footprint_model.py:run_simulation` no longer uses the literal `2024 + t`; it now uses `self.base_year + t`. `base_year` defaults to `BASE_YEAR` and can be overridden via `model_variants`.
- `_update_quantities` no longer hard-codes `min(t / 51, 1.0)`. It uses `self.target_ramp_years = target_year - base_year`, defaulted to 51 but derived from BASE_YEAR / TARGET_YEAR.
- `save_to_csv` now writes `self.base_year + year_added` for yearly-additions rows (previously `2024 + year`).
- The print-trigger `t == 51` is now `t == self.target_ramp_years`.

## 3. Growth-rate vs target-fraction naming

- Inside `TransportModel` the config field `growth_rates.cav` is now read into `self.cav_target_fraction`; `growth_rates.sti` is read into `self.sti_target_fraction`. The legacy attributes `cav_growth_rate` / `sti_growth_rate` no longer exist in this class.
- The JSON keys (`growth_rates.cav`, `growth_rates.sti`) have **not** been renamed — renaming them would break every committed config, CSV prefix, and policy-patch dict in the repository. Instead, the distribution specs under `data_uncertainty.growth_rates.{cav,sti}` now carry an explicit `"semantic": "2075_target_fraction"` tag, and `data_uncertainty.growth_rates.{ev,clean_energy}` carry `"semantic": "annual_growth_exponent"`.
- Comment in `_update_quantities` now states plainly: "the config key `growth_rates.cav` is semantically a 2075-target fraction, not an annual growth exponent."
- Dashboards already labeled these as "CAV target fraction by 2075" / "STI coverage target by 2075" in `CONTROL_SPECS`; this has been preserved.

## 4. Turning-year unification

Retained: **50%-of-peak** (first year after peak where `emissions ≤ 0.5 × peak`). This matches the v3 and v4 dashboards.

Retired: the 5-consecutive-declining-years rule in `_compute_turning_point`. The renamed backend helper is `_compute_turning_point_50pct`. `compute_scalar_metrics` now returns `turning_year_rule = "50_percent_of_peak"` as an explicit tag so downstream CSV readers can verify the rule in use.

## 5. Cumulative New Cars column semantics

- At t=0 the `Cumulative New Cars` column is now 0 (was `initial_data.total_cav`, e.g. 1603 for CA).
- Any downstream reader (paper tables, notebook summaries, legacy notebooks) that subtracted the initial CAV count to compensate must stop subtracting.
- This is a documented backward-compatibility break. Flagged in the final report.

## 6. `--mc 0` = true deterministic

Previously `use_sampling = bool(data_uncertainty) or has_inline_dist or args.mc > 0`. Because every committed config has `data_uncertainty`, `use_sampling` was always True and `--mc 0` silently drew one seed-0 MC sample.

New rule: `use_sampling = args.mc > 0`. When `--mc 0`, `TransportModel` is instantiated with the exact config (post deep-merge, no sampling). The CLI prints an informative note when uncertainty specs are present but not being sampled. This makes `python footprint_model.py --mc 0` reproducibly regenerate `results/{region}_results.csv` from the current code.

## 7. U.S. Average REGION_NOTES

Rewritten in both `v3_streamlit_app/dashboard_core.py` and `v4_streamlit_app/core.py` to say explicitly: distinct synthetic scenario, not midpoint; initial-state fields are midpoints, growth rates / targets / consumption rates are independent assumptions; sensing and communication consumption values diverge 10–30× from CA/OH (unresolved anomaly); U.S. Average energy and emissions figures are not paper-safe until the anomaly is traced. Detailed decision memo in `US_AVERAGE_DECISION_NOTE.md`.

## 8. Dashboard overlay honesty

- v4 `00_Scenario_Explorer.py` now explicitly **warns** when the user has moved sliders off the committed baseline and suppresses the uncertainty overlay (previously the overlay was silently not drawn; the new text tells the user why).
- v3 `00_Scenario_Explorer.py` now distinguishes "no overlay because sliders were moved" (warning) from "no overlay because no quantile CSV exists" (info).
- New helpers `baseline_controls(region, policy)` and `overlay_is_stale(cv)` added to `v4_streamlit_app/core.py` for reuse by other pages.

## 9. Comments removed or updated in `footprint_model.py`

- `# CAV: Reach 95% by 2075 (t=51)` → replaced with comment describing the linear ramp to the config-declared target at `BASE_YEAR + TARGET_RAMP_YEARS`, and noting the semantic misname.
- `# Target fraction (0.95 from config)` → removed (stale; actual targets are 0.24–0.50 depending on region).
- `# STI: Reach 50% by 2075 (t=51)` / `# Target fraction (0.5 from config)` → replaced similarly.
- Initial-cohort / cumulative-new-cars initialization now has a comment explaining why the starting value is 0, and explicitly calls out the prior off-by-`n_cav` bug.
- `# Include 2075 (t=51)` in the print-trigger is replaced with `# Include target year`.

## 10. No-op / deferred renames (documented for traceability)

- Column names in `TransportModel.results` still say "Power (kWh)" even though the quantities are annual energies. Dashboards relabel these strings at presentation time via `DISPLAY_LABEL_MAP`. A full column rename (e.g. `ATS Total Power (kWh)` → `ATS Total Annual Energy (kWh/yr)`) would touch every committed results CSV, every test, every notebook, and every data-contract validator. Deferred to a follow-up stage; noted here so the mismatch is not silent.
- Config key renames (`growth_rates.cav` → `targets.cav_by_2075`, etc.) are deferred for the same reason. Semantic `"semantic"` annotations in the uncertainty specs are the minimum-viable fix for this stage.
- Root-level notebook `footpint.ipynb` (typo in filename) left untouched — scratch artifact, not referenced anywhere.
- Legacy `v2_streamlit_app/` and `v2_1_streamlit_app/` are not updated. They remain as archived reference implementations; their REGION_NOTES and turning-year logic still say old things. Flagged in the final report as a known-stale archive.

---

## Quick cross-reference: audit item → change

| Audit item | Change |
| --- | --- |
| Two turning-year definitions | §4 — 50%-of-peak only; rule tag in scalar metrics |
| INTERP boundary diverges v3/v4 | §1 — unified via backend constants and shared function |
| `--mc 0` not deterministic | §6 — new use_sampling rule |
| US avg narrative contradiction | §7 + US_AVERAGE_DECISION_NOTE.md |
| Load-model uncertainty absent | §DISTRIBUTION_FIXES_APPLIED.md — e_clean, icecav_power_factor, retire_year added; others deferred with plan |
| `growth_rates.cav/sti` mis-named | §3 — internal rename + `"semantic"` annotation |
| Hard-coded 51 / 2024 | §2 — derived from BASE_YEAR / TARGET_YEAR |
| `cumulative_new_cars[0]` off by n_cav | §5 — fixed, backward-compat note |
| Stale overlay under slider motion | §8 — suppressed with explicit warning |
| Stale footprint_model.py comments | §9 — rewritten |
