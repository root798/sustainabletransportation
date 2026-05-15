# Structural Shock Scope — Honesty Note

**Date:** 2026-04-14
**Scope:** CA + OH paper-safe; severities actually executed on disk.

## What is on disk

Only **moderate severity** is executed for any shock family. See
`ls results/shocks/`: every CSV carries `__moderate__` in its filename, for
both California and Ohio, across all five shock families:

- grid_stall (CA + OH)
- ev_slowdown (CA + OH)
- hardware_supply_shock (CA + OH)
- policy_freeze (CA + OH)
- geopolitical_disruption (CA + OH)

Mild and severe CSVs **do not exist** on disk for any family. Running shock
analysis at those severities would require a deliberate regeneration pass
(and, for `hardware_supply_shock:severe`, a backend patch to
`_SHOCK_ATTR_MAP` — see dossier S4-02 / BR:R1).

## Paper-safe wording rules

- Say: "**moderate severity** of each shock family was executed."
- Do **not** say: "three severities explored" or "mild / moderate / severe all tested"
  unless mild + severe CSVs are regenerated and committed.
- The registry JSONs under `scenarios/shocks/` do define three severity tiers
  per family; that is a **design** fact, not an **execution** fact. The
  registry is forward-looking; only moderate is implemented in results.
- Caption language in any shock figure must name the severity explicitly
  ("moderate severity") rather than leaving it implicit.

## hardware_supply_shock:severe patch prerequisite

If mild or severe CSVs are generated for `hardware_supply_shock`, the
backend `_SHOCK_ATTR_MAP` in `footprint_model.py` must first cover
`consumption_rates.ecav_scale_factors.computing`. Currently the severe
case's compute-scale perturbation is silently skipped; only the efficiency
doubling component fires. Fix before regeneration. (Dossier S4-02.)

## geopolitical_disruption sentinel consistency

The `efficiency_doubling = 10.0` used by `geopolitical_disruption:severe`
and the `efficiency_doubling = 10000.0` used by `hardware_supply_shock:severe`
both encode "effectively frozen" in the current implementation, but the
inconsistency itself is a reviewer-bait issue. If the severe tier is
generated, unify the sentinel in `STRUCTURAL_SHOCK_SCHEMA.md` first.

## Dashboard treatment

The optional `v4_streamlit_app/pages/06_Structural_Shocks_Explorer.py`
supplementary page reads only the moderate-severity CSVs currently on disk.
It is clearly labelled **exploratory / supplementary**, is restricted to
California and Ohio (U.S. Average remains quarantined), and compares shock
trajectories against the deterministic baseline only — shocks are never
mixed into baseline Monte-Carlo uncertainty bands.

## Manuscript / support-file wording patch

Any phrase of the form "three severities were explored" in manuscript
drafts, rebuttal drafts, or paper-support text must be rewritten as
"the moderate severity of each shock family was executed; mild and severe
remain design-stage only." Searchable check: `grep -R "three severities" reports/ audits/`.
