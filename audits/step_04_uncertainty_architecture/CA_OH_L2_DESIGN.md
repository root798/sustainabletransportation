# CA_OH_L2_DESIGN.md

Final L2 uncertainty structure for California and Ohio. Compares four candidate designs and recommends one. This is the spec that will be implemented in the next step.

**U.S. Average is explicitly not included in this design.** Its `consumption_rates` block is quarantined.

---

## A. Design candidates — comparison

Dimensions compared:

- **realism** — does it preserve within-level and within-subsystem correlations that exist in the underlying hardware?
- **editability** — can a human author set the priors credibly from one sitting with a spreadsheet?
- **correlation handling** — how does the design manage dependencies between cells?
- **file readability** — how many lines of JSON spec per region, how mnemonically clear?
- **computational simplicity** — minimal extra code in the sampler / TransportModel?

### A.1 Per-cell independent lognormal

18 independent distributions per region (9 ecav + 9 sti).

| dimension | assessment |
| --- | --- |
| realism | **poor** — L4 CAV sensing and L4 computing could drift in opposite directions; that is unphysical. |
| editability | **poor** — 18 × 2 regions = 36 priors to elicit. |
| correlation | **none** — every cell independent. |
| file readability | **poor** — large spec block (~72 lines per region). |
| computational simplicity | **good** — sampler already handles nested specs. |

**Reject.** Realism and editability are unacceptable for a defensible paper.

### A.2 Per-level multiplier only

3 multiplicative lognormal factors per table (ecav L3/L4/L5 and sti Basic/Semi/Highly) → 6 priors per region.

Effective cell = base × level_factor.

| dimension | assessment |
| --- | --- |
| realism | **moderate** — preserves within-level correlation (an expensive L4 stays expensive across all three subsystems). |
| editability | **good** — 6 priors per region. |
| correlation | **captures level ↔ subsystem within a level**; **loses cross-level-within-subsystem** (sensing hardware improvement would not propagate across levels). |
| file readability | **good**. |
| computational simplicity | **good** — one multiplication per cell at model init. |

**Acceptable but not ideal.** Loses one natural correlation dimension.

### A.3 Per-subsystem multiplier only

3 multiplicative factors (sensing / computing / communication) per table → 6 priors per region.

Effective cell = base × subsystem_factor.

| dimension | assessment |
| --- | --- |
| realism | **moderate** — captures "sensor tech uncertainty separate from computing tech uncertainty". |
| editability | **good** — 6 priors per region. |
| correlation | **captures cross-level-within-subsystem**; **loses within-level correlation** (L4 sensing and L4 computing drift independently). |
| file readability | **good**. |
| computational simplicity | **good**. |

**Acceptable but not ideal.** Mirror of A.2 — captures the other correlation dimension only.

### A.4 Hierarchical: per-level × per-subsystem

6 multiplicative factors per table (3 level + 3 subsystem) → 12 priors per region per table, 24 per region total.

Effective cell `(level, subsystem)` = `base × level_factor[level] × subsystem_factor[subsystem]`.

| dimension | assessment |
| --- | --- |
| realism | **good** — both correlation dimensions preserved. An expensive L4 stays expensive across subsystems, AND sensing moves together across levels. |
| editability | **good** — 12 priors per region, organized as 2 groups of 6, each mnemonic. |
| correlation | **captures both dimensions**. Independent cell noise within a (level, subsystem) cell is NOT expressed — this is a simplification (we do not believe the cell-specific residual is large relative to level × subsystem uncertainty). |
| file readability | **good** — compact, hierarchical. |
| computational simplicity | **good** — two multiplications per cell at model init. |

**Select.** Best realism / editability ratio.

---

## B. Final recommended structure (A.4, hierarchical)

### B.1 Schema additions to `scenarios/{region}/scenario.json` (CA and OH)

Two new keys in `consumption_rates` (deterministic defaults = 1.0, so `--mc 0` runs are byte-identical to before):

```json
"consumption_rates": {
    "ecav_power": { ... existing ... },
    "icecav_power_factor": 1.6,
    "sti_power": { ... existing ... },
    "cav_levels": [0.5, 0.333, 0.167],
    "sti_levels": [0.5, 0.333, 0.167],
    "cohort_decay_factor": 0.7,
    "ecav_scale_factors": {
        "L3": 1.0, "L4": 1.0, "L5": 1.0,
        "sensing": 1.0, "computing": 1.0, "communication": 1.0
    },
    "sti_scale_factors": {
        "Basic": 1.0, "Semi": 1.0, "Highly": 1.0,
        "sensing": 1.0, "computing": 1.0, "communication": 1.0
    }
}
```

Corresponding `data_uncertainty.consumption_rates` block:

```json
"consumption_rates": {
    "icecav_power_factor": { ... existing ... },
    "cohort_decay_factor": {"dist": "triangular", "low": 0.5, "mode": 0.7, "high": 0.9},
    "ecav_scale_factors": {
        "L3": {"dist": "lognormal", "mean": 1.0, "sigma": 0.15},
        "L4": {"dist": "lognormal", "mean": 1.0, "sigma": 0.20},
        "L5": {"dist": "lognormal", "mean": 1.0, "sigma": 0.25},
        "sensing": {"dist": "lognormal", "mean": 1.0, "sigma": 0.30},
        "computing": {"dist": "lognormal", "mean": 1.0, "sigma": 0.20},
        "communication": {"dist": "lognormal", "mean": 1.0, "sigma": 0.35}
    },
    "sti_scale_factors": {
        "Basic": {"dist": "lognormal", "mean": 1.0, "sigma": 0.20},
        "Semi":  {"dist": "lognormal", "mean": 1.0, "sigma": 0.25},
        "Highly": {"dist": "lognormal", "mean": 1.0, "sigma": 0.30},
        "sensing": {"dist": "lognormal", "mean": 1.0, "sigma": 0.35},
        "computing": {"dist": "lognormal", "mean": 1.0, "sigma": 0.25},
        "communication": {"dist": "lognormal", "mean": 1.0, "sigma": 0.35}
    },
    "cav_levels": {"dist": "dirichlet", "alpha": [5.0, 3.33, 1.67]},
    "sti_levels": {"dist": "dirichlet", "alpha": [5.0, 3.33, 1.67]}
}
```

Sigma justifications:

- Level factors grow with automation level (L3 more measured, L5 more speculative).
- Subsystem factors larger on sensing / communication (engineering references vary more) than computing (well-benchmarked SoCs).
- STI level / subsystem factors slightly wider than ECAV because infrastructure hardware has less standardization than automotive hardware.

Dirichlet concentration = 10 (alpha sum = 10), mean preserved at `[0.5, 0.333, 0.167]`. Produces draws that stay close to the prior mean but admit ±5–10% per-level variation.

### B.2 Backend implementation sketch

`TransportModel.__init__`:

1. Read `consumption_rates.ecav_scale_factors` and `sti_scale_factors`, default to identity (1.0) if absent.
2. Read `consumption_rates.cohort_decay_factor`, default to 0.7 if absent.
3. After loading `ecav_power` / `sti_power` tables, multiply each cell by `level_factor × subsystem_factor`.
4. Pass `cohort_decay_factor` to `_initialize_cohorts`.

`sample_config`:

- No change to sampling logic. Existing `_apply_data_uncertainty` handles the new nested dicts automatically.
- Existing `_is_distribution_spec` recognises the Dirichlet block on `cav_levels` / `sti_levels` list-valued targets — no sampler extension needed. Verified by code inspection of `_sample_distribution` line 148 (`dirichlet` case returns `rng.dirichlet(alpha).tolist()`).

Saturation metadata sidecar (new):

- New helper in `footprint_model.py`: `compute_saturation_metadata(quantile_df, fields=['ATS Total Power (kWh)', 'ATS Emissions (kg CO2)', 'Clean Energy Fraction', 'EV Fraction'])`.
- For each field, find the first year ≥ `BASE_YEAR + 3` where `p95 - p05 < 1e-6 × max(|p50|, 1)` (effectively zero width). Returns a dict keyed by field.
- Written alongside each quantile CSV as `{prefix}_quantiles_metadata.json`.

### B.3 Backward compatibility

- `--mc 0` deterministic run unchanged: all factors default to 1.0, `cohort_decay_factor` default = 0.7. Deterministic CSV MD5 stable.
- Scenarios that do not include the new keys (e.g., US Average in this stage, or any future scenario authored before this design ships) inherit the defaults. No schema-level enforcement.
- Existing `data_uncertainty.consumption_rates.icecav_power_factor` untouched — the new factors sit alongside.

### B.4 Things deliberately NOT in this design

- Per-cell independent residual lognormal (would extend A.4 to a full 3-level hierarchy). Deferred; current evidence does not justify the extra parameters.
- Cross-region correlation (would couple CA and OH scale draws). Deferred; independent sampling is a conservative default.
- Efficiency-applied-to-computing-only sampled as a continuous parameter. Deferred; this is a structural-scenario choice.
- Adoption-curve / efficiency-curve / efficiency-model / energy-model structural alternatives. Deferred.
- Any U.S. Average change. Quarantined.

---

## C. Justification summary

| Criterion | A.1 per-cell | A.2 per-level | A.3 per-subsystem | **A.4 hierarchical (selected)** |
| --- | :---: | :---: | :---: | :---: |
| realism | ✗ | ◑ | ◑ | ✓ |
| editability | ✗ | ✓ | ✓ | ✓ |
| correlation handling | ✗ | ◑ | ◑ | ✓ |
| file readability | ✗ | ✓ | ✓ | ✓ |
| computational simplicity | ✓ | ✓ | ✓ | ✓ |
| priors per region | 18 | 6 | 6 | 12 |
| compatible with existing sampler | ✓ | ✓ | ✓ | ✓ |

A.4 is strictly dominant on realism and correlation-handling, loses nothing on editability or readability vs A.2 / A.3, and doubles the prior count from 6 to 12 (still trivial to author). Selected.

## D. Implementation boundary

Allowed in this stage:

- `footprint_model.py` — additions only (no signature breaks).
- `scenarios/california/scenario.json` and `scenarios/ohio/scenario.json` — additions only.
- New backend output helper for saturation metadata.

Not allowed:

- `scenarios/us_average/scenario.json` — quarantined.
- Dashboard UI changes.
- Manuscript edits.
- Schema renames (`growth_rates.cav` → `targets.cav_by_2075`).
- Column renames (`ATS Total Power (kWh)` → `ATS Annual Energy (kWh/yr)`).
