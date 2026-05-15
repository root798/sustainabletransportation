# scenarios/

**Canonical source of truth for all regional scenario data.** Anything that the simulator, dashboards, or analysis code needs to know about California, Ohio, or the U.S. Average synthetic region comes from this directory.

## Layout

```
scenarios/
├── README.md                       (this file — index + editing rules)
├── california/
│   ├── scenario.json               (canonical California scenario)
│   └── README.md                   (provenance + edit notes for CA)
├── ohio/
│   ├── scenario.json               (canonical Ohio scenario)
│   └── README.md                   (provenance + edit notes for OH)
└── us_average/
    ├── scenario.json               (canonical U.S. Average synthetic scenario)
    └── README.md                   (provenance + anomaly warning for US avg)
```

Each `scenario.json` holds the complete scenario definition — initial state, growth/target parameters, per-level consumption tables, emission factors, policy overrides, uncertainty distributions, and model-variant defaults — in a single editable file.

## Edit rules

- **To change a region's baseline number** (e.g. initial vehicle stock, per-level power, emission factor): edit `scenarios/{region}/scenario.json`. That is the canonical source. No other file should be touched for a numeric change.
- **To change an uncertainty distribution**: edit the `data_uncertainty` block inside the same file. Keep the `"semantic"` annotation so the meaning of each spec is explicit.
- **To add a new policy scenario** (e.g. "very_aggressive"): add a key to `policy_scenarios` inside the same file.
- **To add a new region**: create `scenarios/{new_region}/scenario.json` and a matching `scenarios/{new_region}/README.md`. Update this index.

## Load path (for future code)

Production load path used by `footprint_model.load_config`, v3 `dashboard_core.load_base_config`, and v4 `core.load_base_config`:

```
scenarios/{region}/scenario.json    (primary, canonical)
configs/{region}.json               (legacy fallback — kept for older external tools)
```

If the canonical file exists, it wins. The `configs/` copy is preserved for backward compatibility with any script that still hard-codes that path, but it is **not** authoritative. Do not maintain two copies by hand — see `docs/FILE_PATH_REDIRECT_MAP.md` for the sync rules.

## What belongs in a scenario file

| Section | Meaning |
| --- | --- |
| `initial_data` | 2024 baseline state: vehicle stock, BEV count, CAV count, intersection count, STI count, low-carbon electricity share. |
| `growth_rates` | Mixed section (legacy name): (i) `cav`, `sti` are **2075 target fractions** despite the section name; (ii) `ev`, `clean_energy`, `total_car_increase` are annual growth exponents; (iii) `efficiency_doubling` is a hardware doubling time in years; (iv) `retire_year` is the vehicle service life. The `data_uncertainty.growth_rates.*` block carries `"semantic"` tags to disambiguate. |
| `consumption_rates` | Per-level sensing/computing/communication power tables for ECAV and STI; `icecav_power_factor`; `cav_levels` and `sti_levels` automation-level mixtures. |
| `emission_factors` | `e_clean`, `e_fossil`, `e_gasoline` kg CO₂/kWh. |
| `policy_scenarios` | Deep-merged overrides per named policy (baseline, aggressive, conservative). Only keys actually touched by a policy appear here. |
| `model_variants` | Adoption-curve and efficiency-curve form. |
| `data_uncertainty` | Distribution specs used by Monte Carlo. Same nested shape as the other sections; scalars are specs `{"dist":..., "mean":..., ...}` instead of point values. |

## What does NOT belong here

- Simulation outputs (`results/`)
- Dashboard code (`v3_streamlit_app/`, `v4_streamlit_app/`)
- Audit memos or validation reports (`audits/`, `reports/`, `docs/`)
- Legacy notebook artefacts (`results_notebook/`)

## Related documentation

- `docs/SCENARIO_FILE_CONVENTION.md` — formal convention document.
- `docs/SCENARIO_SOURCE_OF_TRUTH_INDEX.md` — per-field pointer to exactly where each scenario number lives.
- `audits/step_01_quantitative_audit/PARAMETER_AUDIT_CURRENT.csv` — inventory of every active quantity.
- `audits/step_02_audit_fixes/US_AVERAGE_DECISION_NOTE.md` — details on the U.S. Average anomaly and why its load figures are not paper-safe.
