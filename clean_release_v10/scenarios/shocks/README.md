# scenarios/shocks/

Registry of structural-shock scenarios. Each `{shock_name}.json` defines one shock per the schema in `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_SCHEMA.md`.

Shocks are **discrete labelled scenarios**, not extra distributions. They never merge into the baseline Monte-Carlo quantile CSVs — outputs live in `results/shocks/` only.

## Registered shocks

| file | narrative | default onset | default duration | default severity | paper scope |
| --- | --- | ---: | ---: | --- | --- |
| `grid_stall.json` | Grid decarbonisation stalls. | 2030 | 15 y | moderate | main text |
| `ev_slowdown.json` | BEV adoption slows (battery / infrastructure / macro). | 2028 | 10 y | moderate | main text |
| `hardware_supply_shock.json` | Semiconductor / sensor / V2X supply crunch pauses Moore scaling. | 2028 | 8 y | moderate | main text |
| `policy_freeze.json` | Permanent CAV / STI target rollback. | 2032 | 43 y (through 2075) | moderate | main text |
| `geopolitical_disruption.json` | Compound multi-parameter disruption. | 2029 | 12 y | moderate | supplementary |

## Paper-safe regions

Every shock declares `paper_safe_regions: ["california", "ohio"]`. U.S. Average is explicitly excluded and the CLI rejects `--scenarios us_average` when `--shock` is passed, unless `--allow-quarantined` is used (outputs land under `results/shocks/quarantined/` with `__QUARANTINED` suffix).

## Running a shock

```
python footprint_model.py --scenarios california ohio \
                          --years 68 --policy baseline --mc 0 \
                          --shock grid_stall --severity moderate
```

Outputs land under `results/shocks/` following the path contract in `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md §2`.

## Editing

- Adding a new shock: create `scenarios/shocks/{new_shock}.json` matching the schema; update this README.
- Modifying an existing shock: edit the JSON; regenerate any committed `results/shocks/` outputs for that shock.
- Retiring a shock: delete the JSON; optionally archive the file to `audits/step_00_legacy/shocks/`; update this README and any references.

## Related docs

- `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_FAMILY_DESIGN.md`
- `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_SCHEMA.md`
- `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md`
- `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_IMPLEMENTATION.md`
- `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_VALIDATION.md`
