# Structural-Shock UI — Implementation Note

**Date:** 2026-04-14
**Page:** `v4_streamlit_app/pages/06_Structural_Shocks_Explorer.py`
**Status:** Implemented as lightweight supplementary / exploratory page.
**Paper-safety:** Not paper-safe. Not cited in any manuscript figure.

## What this page does

- Auto-discovers shock output CSVs under `results/shocks/` using the
  filename contract `{region}__{shock}__{severity}__onset-{YYYY}__duration-{NN}_results.csv`.
- Restricts the region selector to California and Ohio (U.S. Average stays
  quarantined).
- Overlays the selected shock-family trajectories against a **live, baseline
  deterministic simulation** for the same region, drawn as a dashed line with
  a vertical onset marker.
- Presents a "Shock Δ vs baseline at sampled years" table (2030, 2045, 2060,
  2075, 2092) so the reader can see the magnitude of perturbation.
- Shows provenance JSON sidecars for the on-disk shocks.

## What this page deliberately does NOT do

- It does **not** mix shock trajectories into ordinary Monte-Carlo bands.
  Shocks are discrete labelled scenarios (see METHODS_ALIGNMENT §M6); mixing
  them into the MC envelope would violate the uncertainty-construction
  assumptions of the p05–p95 pipeline.
- It does **not** regenerate mild / severe severities. Only severities
  already on disk are displayed; the user-visible `st.info` notes which
  severities are present so nothing is implied that isn't executed.
- It does **not** show U.S. Average. Any `us_average__*` shock CSV (e.g.
  anything routed to `results/shocks/quarantined/`) is filtered out.
- It does **not** affect the baseline pages. The page is a pure reader; no
  writes, no cache invalidation, no shared state beyond `st.cache_data` on
  the filename discovery helper.

## Severity availability disclosure

The page prints the set of severities present on disk (currently only
`moderate`). If mild / severe CSVs are later generated, the discovery helper
picks them up automatically without code changes. See
`SHOCK_SCOPE_HONESTY.md` for the paper-wording rule tied to this.

## hardware_supply_shock pre-generation caveat

If a user regenerates `hardware_supply_shock:severe` CSVs, the dossier
item S4-02 / BR:R1 must be fixed first (`_SHOCK_ATTR_MAP` does not cover
`consumption_rates.ecav_scale_factors.computing`). Otherwise the severe
CSV will silently under-apply the compute-scale perturbation.

## Why this page is safe to ship

- It only reads. It does not run MC. It does not write to `results/`.
- Its explicit `st.warning` banner calls out "EXPLORATORY / SUPPLEMENTARY".
- It loads shock CSVs by pattern match; if the directory is empty it shows
  an `st.error` and stops rather than raising.
- Baseline pages do not import from this page; it is purely additive.
