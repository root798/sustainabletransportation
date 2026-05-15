# STAGE_2_COMPLETION_REPORT.md

Stage 2 (Structural-shock family design) — complete. All four design documents are written. Stage 3 can proceed autonomously.

## Files created

| file | purpose |
| --- | --- |
| `STRUCTURAL_SHOCK_FAMILY_DESIGN.md` | Five shock families (grid stall, EV slowdown, hardware supply shock, policy freeze, geopolitical disruption), their narratives, onset / duration / severity levels, perturbed parameters, expected effects, and paper scope. |
| `STRUCTURAL_SHOCK_SCHEMA.md` | JSON schema for `scenarios/shocks/{shock_name}.json` registry files, including the perturbation-operation vocabulary (`set_during_window`, `multiply_during_window`, `set_permanent`, `multiply_permanent`, `offset_permanent`). |
| `STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md` | Output path / filename / column / provenance rules that keep shock outputs strictly separated from baseline MC artefacts. |
| `STRUCTURAL_SHOCK_IMPLEMENTATION_PLAN.md` | Minimal-viable Stage-3 implementation plan: helper functions, `TransportModel.shock_schedule` kwarg, CLI additions, registry authoring, validation runs, deferred items. |
| `STAGE_2_COMPLETION_REPORT.md` | This file. |

## Validation

**V1. Design stays separate from ordinary MC.**
Every shock output path lives under `results/shocks/`. The schema has no `data_uncertainty`-shaped knobs. The implementation plan explicitly forbids mixing shock samples into `results/{region}__policy-baseline__model-fixed_table_*.csv`. `STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md §5–§6` enforces this at the file-system level.

**V2. Design uses CA/OH only.**
`paper_safe_regions` field on every shock registry JSON is a subset of `{"california", "ohio"}`. The CLI rejects U.S. Average unless the user explicitly forces `--allow-quarantined`, in which case outputs land under `results/shocks/quarantined/` with a `__QUARANTINED` filename suffix.

**V3. Design is consistent with reviewer criticism about disruptive events.**
`STRUCTURAL_SHOCK_FAMILY_DESIGN.md §6` maps each shock family directly to a reviewer concern: grid stall, EV slowdown, hardware supply, policy freeze, and geopolitical disruption. Paper scope marks four of five as main-text-worthy, one as supplementary.

## Decision — Stage 3 may proceed

Design is implementable with narrow, well-scoped backend changes (`footprint_model.py` helpers + `TransportModel.shock_schedule` kwarg + CLI flags + registry authoring). Baseline path remains byte-identical. Risk classification in the implementation plan: **safe** for the schedule-lookup pattern, **medium** for the `config_path` resolver, **low** for the `shock_active` column.

Stage 3 begins autonomously with the sequence in `STRUCTURAL_SHOCK_IMPLEMENTATION_PLAN.md §7`:
1. Author five registry JSONs.
2. Add helpers and `shock_schedule` kwarg.
3. Add CLI flags.
4. Run validation.
5. Write `STRUCTURAL_SHOCK_IMPLEMENTATION.md` and `STRUCTURAL_SHOCK_VALIDATION.md`.

## Known deferrals

- Dashboard shock page.
- Figure-building helper for shocks (`scripts/build_shock_figures.py`).
- Stochastic shock-onset sampling.
- Region-correlated shocks.
- Positive shocks.

All listed in `STRUCTURAL_SHOCK_IMPLEMENTATION_PLAN.md §5`.
