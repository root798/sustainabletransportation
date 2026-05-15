# PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.md

**Date:** 2026-04-15
**Supersedes as the primary user abstraction:** the grouped-per-layer preset scheme (`GROUPED_PRESET_DESIGN.md`). Layer groupings are retained **only as explanatory grouping and contribution summary**; they are no longer the main control.
**Machine-readable companion:** `PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.csv`
**Linked documents:**
- `DEFAULT_FIXED_PARAMETER_JUSTIFICATION.md` — why each parameter is fixed or not
- `PARAMETER_LEVEL_PRESET_TABLE.md` — per-parameter level specifications
- `PARAMETER_CONTRIBUTION_EXPERIMENT.md` / `.csv` — empirical evidence
- `LAYER_CONTRIBUTION_EXPERIMENT.md` / `.csv` — conceptual layer summary
- `UNCERTAINTY_PAGE_REDESIGN.md` — the panel spec consuming this registry
- `configs/ui_parameter_presets/*.json` — registry JSON files

---

## 1. Why parameter-level instead of layer-level

The previous release used grouped presets `(L1, L2, L3) ∈ {fixed, low, medium, high}` — seven controllable states per layer plus three layers. That design lumps physically different parameters onto one knob per layer. Concretely:

- Inside L2, `icecav_power_factor` (F20) is tight and physical; `cohort_decay_factor` (F21) is irrelevant after 2036; the per-level ECAV axis (F06–F08) duplicates the per-subsystem axis (F09–F11). Folding these onto one "L2 low / medium / high" selector forces the reader to accept all three decisions at once.
- Inside L3, `growth_rates.cav` (F23) is a scenario target and `growth_rates.ev` (F25) is a compounding exponent. They serve different rhetorical purposes; a single L3 preset cannot separate them.
- Inside L1, `initial_data.f_clean` (F01) is a tight measurement and `emission_factors.e_clean` (F03) is a methodological choice. They should be controllable independently.

Parameter-level control lets each factor have its own fixed/low/medium/high vocabulary. The L1/L2/L3 grouping remains on the panel as a *visual* organiser (expandable sections) and as a *contribution summary* (Figure C), but not as the user's primary control.

## 2. Parameter registry

Every ordinary-Monte-Carlo parameter in the CLEAR-ATS pipeline is enumerated in `PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.csv`, plus the five structural-shock families and the underconstrained F29 (missing-abs-power-cells). The CSV has 18 columns per row:

| Column | Meaning |
|---|---|
| `param_id` | `F01` … `F28`, `F29_missing_abs_power_cells`, `SHK01`–`SHK05`. |
| `config_path` | dotted path into `scenarios/{region}/scenario.json`. |
| `layer` | conceptual group only: L1, L2, L3, SHOCK. |
| `physical_meaning` | one-line plain-English description. |
| `current_distribution` | current prior family. |
| `current_parameterization_CA_OH` | hyper-parameters committed in the scenario files. |
| `can_be_fixed` | whether fixing the parameter at its central value is scientifically defensible. |
| `must_remain_uncertain` | whether fixing would be misleading. |
| `low_spec` / `medium_spec` / `high_spec` | per-level distribution specs. Cells `n/a` where the level is not offered. |
| `allow_high` | whether HIGH is allowed at all. |
| `duplicates_effect_with` | other `param_id`s whose variance overlaps. |
| `affects` | one of `level`, `width`, `turning_year`, `interp_boundary`, `long_horizon`, `early_horizon_only`. Multiple tags are `;`-separated. |
| `default_level` | the level chosen by the decision-meaningful default bundle. |
| `paper_safe_level` | the level chosen by the paper-safe-reproduction bundle. |
| `rationale_for_decision` | one-line justification. |
| `decision_value` | coarse class: `fixed_default`, `free_default_low`, `hidden_internal_only`, `structural_shock_only`. |

## 3. Level vocabulary per parameter (summary)

Not every parameter has all four levels. The allowed-set is scientifically determined:

| Allowed-set | Parameters |
|---|---|
| `{fixed, medium}` | F06, F07, F08 (ECAV per-level), F12, F13, F14 (STI per-level), F21 (cohort decay) — duplicates or irrelevant-post-2036; MEDIUM is paper reproduction only. |
| `{fixed, low, medium}` | F01, F02 (initial state), F03, F04, F05 (emission factors), F09, F10, F11 (ECAV per-subsystem), F15, F16, F17 (STI per-subsystem), F18, F19 (Dirichlet mixes), F20 (icecav), F22 (retire_year), F28 (total_car_increase) — evidence-anchored; widening beyond MEDIUM is not defensible. |
| `{fixed, low, medium, high}` | F23, F24 (2075 targets), F25, F26 (growth exponents), F27 (efficiency doubling) — scenario-policy knobs; HIGH is exploratory-only. |
| `{hidden_internal_only}` | F29 (missing absolute power cells) — cannot be toggled; disclosed. |
| `{structural_shock_only}` | SHK01–SHK05 — never in ordinary MC. |

## 4. Decision-meaningful default (committed default)

The panel opens with each parameter at its `default_level` column value. Summary:

- **fixed_default** (12 parameters): F01, F02, F06, F07, F08, F12, F13, F14, F21.
- **free_default_low** (16 parameters): F03, F04, F05, F09, F10, F11, F15, F16, F17, F18, F19, F20, F22, F23, F24, F25, F26, F27, F28.
- **hidden_internal_only** (1 entry): F29 — disclosed as a known gap on the panel, never user-tunable.
- **structural_shock_only** (5 entries): SHK01–SHK05 — Structural Shocks panel only.

Note: the "fixed_default" list names *explicit* fixings. F25/F26 are on `low` by default (not fixed); the overall bundle therefore reduces band width aggressively at 2050 and 2075 without misleading the reader about trajectory uncertainty.

## 5. Paper-safe reproduction bundle

Each parameter has a `paper_safe_level` — usually MEDIUM. Selecting "Paper-safe reproduction" in the UI applies `paper_safe_level` to every parameter. This reproduces the committed `_quantiles.csv` files and is advertised in the UI with a distinct badge.

## 6. Exploratory bundle

Every parameter whose `allow_high` is `yes` supports HIGH. The exploratory bundle applies HIGH to F23, F24, F25, F26, F27 (five trajectory-policy knobs) and leaves L1 / L2 at `fixed` / `low`. This reproduces the long-horizon what-if view without widening evidence-anchored parameters.

## 7. Handling of F29 and structural shocks

- **F29 (`consumption_rates.ecav_power.*` and `sti_power.*`):** 18 absolute per-level per-subsystem power cells without a direct prior. All variance routes through the scale factors (F06–F17). The panel discloses this gap as `hidden_internal_only`; no user control. A future release with joint priors could surface this.
- **SHK01–SHK05:** the five structural shock families (grid_stall, ev_slowdown, hardware_supply_shock, policy_freeze, geopolitical_disruption). They are NEVER folded into ordinary Monte Carlo. The panel links to the Structural Shocks panel for these.

## 8. Backward compatibility with the grouped-preset release

The grouped-per-layer presets (`l1_*.json`, `l2_*.json`, `l3_*.json`) remain on disk. The new panel does not consume them by default but still exposes "quick bundles" — Paper-safe, Decision-meaningful, Exploratory — which are realised via the parameter-level `default_level` / `paper_safe_level` columns rather than the layer presets. The layer presets can still be loaded manually via the archived `v4_streamlit_app/pages/04_Uncertainty_Panel.py` file (kept for migration testing; not part of the production page list).

## 9. Invariants enforced on the registry

1. Every parameter's `default_level` and `paper_safe_level` is in its `allowed_levels`.
2. Every `fixed` level matches the scenario file's central value (up to region-specific means / kappas).
3. No parameter has `high` offered unless `allow_high=yes` and `paper_safe=false` is explicitly tagged for that level in the JSON.
4. Structural shocks are never added to ordinary MC at any level.
5. Distribution labels used in any level match `footprint_model._KNOWN_DISTRIBUTIONS`.

A validator in `v4_streamlit_app/core.py::validate_parameter_registry` checks 1–5 at panel-load time.
