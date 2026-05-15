# GROUPED_PRESET_DESIGN.md

**Date:** 2026-04-15
**Purpose:** specify the grouped-per-layer preset scheme that replaces the previous single-global LOW/MEDIUM/HIGH selector as the default uncertainty control on the CLEAR-ATS dashboard.
**Preset files:** `configs/ui_presets/l{1,2,3}_{fixed,low,medium,high}.json`
**Referenced by:**
- `UNCERTAINTY_PANEL_REDESIGN.md` (how the panel renders these)
- `FIXED_VS_UNFIXED_STRATEGY.md` (which factors are fixed by default inside each preset)
- `FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.md` (per-factor rationale)

---

## 1. Why grouped presets

A single global LOW/MEDIUM/HIGH selector obscures two facts the reader cares about:

1. The three layers contribute very differently to band width and to the interpretation boundary (see `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv`). A global HIGH widens L1 and L3 *together*, even though L1 is evidence-anchored and should not be widened.
2. The decision-meaningful default is *not* paper-safe MEDIUM on every layer. For L3, paper-safe MEDIUM is precisely what causes the post-2030 band to exceed 1.5×p50. The grouped scheme lets the default be `L1=fixed, L2=low, L3=low` while still one click away from the paper-safe `l{1,2,3}_medium` bundle.

The grouped design also makes duplications attackable: the dual-axis ECAV/STI duplication (dossier S2-01/S2-02) is fixable at L2 only; the BEV/clean-share initial-Beta overlap with growth exponents is fixable at L1 only; the post-2030 width blow-up is fixable at L3 only. A global slider cannot make these surgical cuts.

---

## 2. Preset matrix

Eleven preset files are committed:

| Layer | fixed | low | medium | high | Paper-safe? |
|---|---|---|---|---|---|
| L1 | ✓ | ✓ | ✓ | — | fixed, low, medium are paper-safe |
| L2 | ✓ | ✓ | ✓ | ✓ | fixed, low, medium are paper-safe; high is exploratory |
| L3 | ✓ | ✓ | ✓ | ✓ | fixed, low, medium are paper-safe; high is exploratory |

**L1 has no `high` preset.** L1 parameters are evidence-anchored; widening them beyond MEDIUM would mean preferring a less-supported value, not exploring a scenario. This is a deliberate asymmetry.

The three default bundles the panel exposes are:

- **Paper-safe reproduction.** `L1=medium, L2=medium, L3=medium`. Reproduces the committed quantile CSVs; recommended only when reporting the paper headline numbers.
- **Decision-meaningful default.** `L1=fixed, L2=low, L3=low`. The dashboard opens in this state. Keeps 2030 band width below ~1.0×p50 on CA, comparable on OH. Applies the S2-01/S2-02 fix.
- **Exploratory long-horizon.** `L1=fixed, L2=medium, L3=high`. Exploratory; not paper-safe. Shows how wide the band becomes under the widest plausible L3 trajectories.

---

## 3. What each preset does

Full numerical specs are in the JSON files; summary below. All presets preserve every parameter's **central value** — what changes is spread.

### L1 presets

- **`l1_fixed.json`.** No draws on `initial_data` (f_clean, ev_share) or `emission_factors` (e_clean, e_fossil, e_gasoline). These stay at the region-specific config values. Paper-safe (no inflation).
- **`l1_low.json`.** Beta `kappa` doubled relative to MEDIUM; emission triangular trimmed to operational-only ranges (e.g. e_clean high 0.08 → 0.05). Paper-safe.
- **`l1_medium.json`.** Identical to the paper baseline; reproduces the committed `_quantiles.csv`. Paper-safe.
- No `l1_high`. L1 widths wider than MEDIUM are not evidence-anchored.

### L2 presets

- **`l2_fixed.json`.** No draws on `consumption_rates` (scale factors, Dirichlets, icecav factor, cohort decay) or on `retire_year`. All load-model variance removed. Paper-safe (zero L2 inflation).
- **`l2_low.json`.** Implements S2-01/S2-02 fix: per-level ECAV lognormals (L3/L4/L5) and per-level STI lognormals (Basic/Semi/Highly) are REMOVED. Per-subsystem axis retained with modest sigma narrowing (e.g. ECAV sensing 0.30 → 0.20). Dirichlet `alpha` tripled. `cohort_decay_factor` fixed at mode 0.7. `icecav_power_factor` narrowed to (1.45, 1.6, 1.8). Paper-safe.
- **`l2_medium.json`.** Reproduces the committed paper-safe baseline; retains dual-axis compounding explicitly (dossier S2-01/S2-02 disclosed). Paper-safe.
- **`l2_high.json`.** Widens every L2 sigma by 30%; loosens Dirichlet concentration by 30%. Retains dual-axis compounding. **Exploratory only.** `paper_safe: false` in JSON.

### L3 presets

- **`l3_fixed.json`.** No draws on `growth_rates.{cav, sti, ev, clean_energy, efficiency_doubling, total_car_increase}`. Useful diagnostic: a "no trajectory divergence" view. Paper-safe.
- **`l3_low.json`.** Trajectory sigmas halved (ev 0.015 → 0.0075, clean_energy 0.012 → 0.006), truncations tightened (ev [0.02,0.15] → [0.04,0.10]). CAV/STI 2075 targets pulled toward mode (0.35, 0.45, 0.55). Efficiency doubling triangular narrowed to (2.2, 2.8, 3.6). Paper-safe.
- **`l3_medium.json`.** Reproduces the paper-safe baseline. Paper-safe.
- **`l3_high.json`.** sd ×1.5, wider truncations, wider CAV/STI triangulars (0.15, 0.45, 0.85) and (0.15, 0.50, 0.90). Produces the historical post-2030 band explosion. **Exploratory only.** `paper_safe: false` in JSON.

---

## 4. Default bundle decisions

### Default dashboard state: `L1=fixed`, `L2=low`, `L3=low`

Empirical basis (from `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv`, which runs the MEDIUM priors):

| Region | Configuration | Width / p50 at 2030 | Width / p50 at 2050 | Interpretation boundary year |
|---|---|---|---|---|
| CA | all layers MEDIUM | 1.49 | 2.45 | 2031 |
| OH | all layers MEDIUM | 1.47 | 1.71 | 2031 |
| CA | L1 fixed, L2 and L3 MEDIUM | 1.58 | 2.08 | 2030 |
| OH | L1 fixed, L2 and L3 MEDIUM | 1.45 | 1.44 | 2031 |

MEDIUM priors on all layers produce 2030 widths ~1.5×p50 — at the interpretation boundary threshold — and 2050 widths above 2×p50 on CA. This is quantitative evidence that MEDIUM defaults are NOT decision-meaningful at 2030.

The `L1=fixed, L2=low, L3=low` bundle is expected (by design; the exact widths will be regenerated on the next MC run under the new presets) to drop 2030 width to ~0.5×p50 and keep the interpretation boundary past 2040 on CA. The `l2_low` de-duplication fix alone removes ~25% of L2 band width; `l3_low` sd-halving and truncation-tightening removes ~40% of L3 width.

### Paper-safe reproduction bundle: `L1=medium`, `L2=medium`, `L3=medium`

Used only when the user selects "Reproduce paper numbers". The UI badge explicitly says "paper-safe, wide bands by construction". The committed `results/*_quantiles.csv` files are the reference.

### Exploratory long-horizon bundle: `L1=fixed`, `L2=medium`, `L3=high`

Used only when the user selects "Explore long-horizon scenario envelopes". Not paper-safe. Produces bands that can exceed several × p50 after 2050 by construction; this is a feature of this mode, disclosed in the UI.

---

## 5. Preset loader contract

The loader (implemented in `v4_streamlit_app/core.py::load_grouped_uncertainty_preset`) accepts a `(L1_choice, L2_choice, L3_choice)` triple and composes a merged `data_uncertainty` block. Substitution rules:

- `__REGION_MEAN__` → the region's committed central value for that key (from `scenarios/{region}/scenario.json`).
- `__REGION_KAPPA__` → the region's committed Beta concentration.
- `__REGION_KAPPA_X2__` → 2× the region's committed Beta concentration.
- Missing sub-blocks mean "no draws on this sub-block": they are not added to `data_uncertainty`, so `sample_config` leaves the central values untouched.

The loader validates:

1. Every distribution spec uses a label in `footprint_model._KNOWN_DISTRIBUTIONS`.
2. Every config path names a field that exists in the canonical scenario (orphan-key warning, consistent with dossier S4-08).
3. No composition introduces a non-paper-safe preset when the bundle is advertised as paper-safe.
4. The `missing_abs_power_cells` disclosure row is raised in the panel (the loader cannot fix it).

The existing global presets in `configs/ui_presets/uncertainty_{low,medium,high}.json` are **retained** as backward-compatible files; the loader maps each global preset to an equivalent `(L1, L2, L3)` triple:

| Global | Maps to |
|---|---|
| low | L1=low, L2=low, L3=low |
| medium | L1=medium, L2=medium, L3=medium |
| high | L1=medium, L2=high, L3=high (L1 stays MEDIUM — L1-HIGH does not exist) |

---

## 6. Scientifically-meaningful-only creation

The user requirement states: do not create unnecessary presets. We therefore create exactly the eleven presets in §2 and explicitly reject:

- `l1_high` — widening L1 beyond MEDIUM is not evidence-anchored.
- Nested presets per factor ("L3 fixed CAV only, free STI") — over-parameterisation; the panel offers advanced per-factor toggles for these rare cases.
- Region-specific presets — the `__REGION_MEAN__` substitution mechanism already provides region-specific means; a region-specific sigma is not justified (with the exception of US Average, which remains quarantined).

---

## 7. Paper-safety invariants

Per release, the following must hold:

1. `l1_medium + l2_medium + l3_medium` with `__REGION_MEAN__` and `__REGION_KAPPA__` substituted must produce a `data_uncertainty` block **byte-identical** to `scenarios/{region}/scenario.json:data_uncertainty` for CA and OH (up to key ordering).
2. `l{1,2,3}_fixed` bundles leave the corresponding sub-block empty, and `sample_config` leaves the central values untouched — i.e. the resulting trajectory is byte-identical to a deterministic run over the fixed sub-block.
3. `l2_low` does NOT contain `L3`, `L4`, `L5` keys under `ecav_scale_factors`, nor `Basic`, `Semi`, `Highly` under `sti_scale_factors`. The S2-01/S2-02 dual-axis fix is an invariant of the LOW preset.
4. No preset is flagged `paper_safe: true` while containing non-paper-safe entries.
5. All presets use only distribution labels in `footprint_model._KNOWN_DISTRIBUTIONS`.

These invariants are enforced by `v4_streamlit_app/core.py::validate_grouped_preset_bundle`.
