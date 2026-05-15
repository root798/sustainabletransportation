# step_07_structural_shocks

Design, schema, implementation, and validation of the structural-shock scenario family for California and Ohio. Shocks are **discrete labelled scenarios**, not extra distributions folded into Monte-Carlo sampling.

## Files

| file | purpose |
| --- | --- |
| `STRUCTURAL_SHOCK_FAMILY_DESIGN.md` | Five shock families (grid stall, EV slowdown, hardware supply, policy freeze, geopolitical disruption), onset / duration / severity / perturbed parameters / expected effects / paper scope. |
| `STRUCTURAL_SHOCK_SCHEMA.md` | JSON schema for `scenarios/shocks/{shock_name}.json` registry files. |
| `STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md` | Output path / filename / column / provenance rules. |
| `STRUCTURAL_SHOCK_IMPLEMENTATION_PLAN.md` | Minimum-viable Stage-3 plan. |
| `STRUCTURAL_SHOCK_IMPLEMENTATION.md` | Actual implementation log (helpers, `shock_schedule` kwarg, CLI flags, registry authoring). |
| `STRUCTURAL_SHOCK_VALIDATION.md` | Validation evidence (baseline unchanged, shock reproducible, US avg rejected, per-year perturbation correctness). |
| `STAGE_2_COMPLETION_REPORT.md` | Design-stage completion. |
| `STAGE_3_COMPLETION_REPORT.md` | Implementation-stage completion. |

## Runtime artefacts

- Registry: `scenarios/shocks/{grid_stall,ev_slowdown,hardware_supply_shock,policy_freeze,geopolitical_disruption}.json` + `scenarios/shocks/README.md`.
- Outputs: `results/shocks/{region}__{shock}__{severity}__onset-{YYYY}__duration-{NN}_{results.csv,provenance.json}`.
- CLI: `python footprint_model.py --shock {name|all} --scenarios california ohio --mc 0`.
- U.S. Average rejected by default; `--allow-quarantined` routes to `results/shocks/quarantined/`.

## Key outcomes

- Baseline byte-identical with/without shock flag.
- Five shocks × two regions produce scientifically-plausible emissions deltas (policy_freeze −50 % CA 2050; geopolitical +74 %; ev_slowdown +12 %; hardware_supply +1 %; grid_stall effect concentrated in 2030–2049 before clean cap saturation).
- Shock outputs cleanly isolated from baseline MC pipeline.
