# STRUCTURAL_SHOCK_IMPLEMENTATION_PLAN.md

Minimal-viable implementation plan for Stage 3. Implements the five shock families described in `STRUCTURAL_SHOCK_FAMILY_DESIGN.md` using the schema in `STRUCTURAL_SHOCK_SCHEMA.md` and the output contract in `STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md`.

**Scope**: backend only. No dashboard integration in this stage. No new figures in this stage (figures can be added later with `scripts/build_shock_figures.py`).

---

## 1. Code additions

### 1.1 New helpers in `footprint_model.py`

```python
def load_shock_registry(shock_name: str) -> dict
def apply_shock_to_config(cfg: dict, shock: dict, severity: str,
                          onset_year: int, duration_years: int) -> dict
def run_shock_simulation(region: str, shock_name: str, severity: str,
                         onset_year: int, duration_years: int,
                         mc_samples: int = 1, seed: int = 42) -> dict
```

- `load_shock_registry` reads `scenarios/shocks/{shock_name}.json`, validates the schema, and returns the parsed dict.
- `apply_shock_to_config` does NOT perturb the raw scenario; it returns a wrapped object containing the baseline scenario plus a per-year perturbation table keyed by `(year, config_path)`. The simulator looks up the perturbation table each year to decide what value to use for that year.
- `run_shock_simulation` orchestrates the shock run: loads the registry, loads the canonical baseline scenario for `region`, applies the shock, runs the simulator, writes outputs per the output contract.

### 1.2 Minimal change to `TransportModel`

Add an optional `shock_schedule` argument to the constructor. When present, the simulator consults the schedule each year to override specific parameters. When absent (baseline), behaviour is byte-identical to the current implementation.

The shock schedule is a dict:

```python
shock_schedule = {
    <year>: {
        <config_path>: <value>,
        ...
    },
    ...
}
```

Years outside the schedule get the baseline value. For `set_permanent` / `multiply_permanent` / `offset_permanent` operations, the schedule carries entries for every year from onset onward.

### 1.3 CLI additions to `footprint_model.main`

```
python footprint_model.py --shock grid_stall --severity moderate \
                          --onset-year 2030 --duration-years 15 \
                          --scenarios california ohio --mc 0 --seed 42
```

Flags:
- `--shock {shock_name}` (or `all` to iterate over every registered shock).
- `--severity {mild|moderate|severe}` (default = the shock's `default_severity`).
- `--onset-year {int}` (default = registry default).
- `--duration-years {int}` (default = registry default).

When `--shock` is absent, the CLI behaves exactly as it does today (baseline runs).

When `--shock` is present, the CLI:
1. Rejects `us_average` with an error message pointing at `US_AVERAGE_SOURCE_TRACE.md` (or lands under `results/shocks/quarantined/` if the user explicitly forces with `--allow-quarantined`).
2. Writes outputs exclusively under `results/shocks/`.
3. Emits a provenance JSON sidecar.

## 2. Registry files to author

Five JSON files under `scenarios/shocks/`, one per shock in `STRUCTURAL_SHOCK_FAMILY_DESIGN.md §2`:

- `grid_stall.json`
- `ev_slowdown.json`
- `hardware_supply_shock.json`
- `policy_freeze.json`
- `geopolitical_disruption.json`

Plus `scenarios/shocks/README.md` as the human-readable index.

## 3. Validation runs (Stage 3)

1. Byte-identical baseline: run `python footprint_model.py --scenarios california --years 68 --policy baseline --mc 0` before and after the code additions; MD5 of `results/california_results.csv` must match.
2. Shock execution for all five shocks × both regions × `moderate` severity, deterministic (`--mc 0`). All 10 outputs appear under `results/shocks/`. None appear under `results/` root.
3. Reproducibility: re-run one shock with the same seed; MD5 of the output CSV matches.
4. U.S. Average rejection: `--shock grid_stall --scenarios us_average` must error out without writing any file.
5. Provenance sidecar: every shock run emits a `_provenance.json` with the perturbations actually applied.
6. Per-year perturbation correctness: for `grid_stall` at `moderate`, the `Clean Energy Fraction` must remain at its onset-year value throughout the shock window, then resume exponential growth after.

## 4. Edge cases to handle

- Onset year before `BASE_YEAR`: reject.
- Duration exceeding horizon: clip duration to horizon end.
- Perturbed `config_path` that doesn't exist in the scenario: error with a helpful message.
- Multiple perturbations on the same path: last one wins, warning logged.
- Interaction with `data_uncertainty` sampling: if `--mc > 0` is combined with `--shock`, the shock's deterministic perturbations are applied AFTER uncertainty sampling, so each MC sample sees the same shock override. This is the cleaner semantic.

## 5. Things deferred

- `scripts/build_shock_figures.py` — figure-building helper. Can be added later using `scripts/build_paper_figures.py` as a template.
- Dashboard shock page (`v4_streamlit_app/pages/05_Structural_Shocks.py`) — deferred to a follow-up UI stage.
- Stochastic onset year or duration — the registry schema allows it in principle but Stage 3 treats these as deterministic.
- Region-correlated shocks — each shock is applied per-region; multi-region coordination is deferred.
- Positive shocks (tech breakthroughs) — machinery is identical but framing is out of scope for the first revision.

## 6. Implementation risk assessment

**Safe**: the schedule-lookup pattern is narrow; every baseline call path skips it when `shock_schedule is None`. The failure mode in the worst case is "shock run produces a corrupt output file" — which is isolated under `results/shocks/` and cannot contaminate the baseline.

**Medium risk**: the `config_path` resolver must deep-walk the scenario dict (including `model_variants` which is a single-level dict) and must not accidentally touch `data_uncertainty` or `policy_scenarios` (both are out of scope for shocks).

**Low risk**: adding the `shock_active` column to outputs is isolated.

## 7. Sequence for Stage 3

1. Author five registry JSONs.
2. Add helpers and the `shock_schedule` kwarg to `TransportModel`.
3. Add the CLI flags.
4. Run validation §3.
5. Document the implementation (`STRUCTURAL_SHOCK_IMPLEMENTATION.md`) and the validation (`STRUCTURAL_SHOCK_VALIDATION.md`).

## 8. Stop condition for Stage 3

Safe to stop if any of:
- Validation V1 (byte-identical baseline) fails.
- Validation V4 (U.S. Average rejection) cannot be enforced safely.
- Validation V6 (per-year perturbation correctness) fails on any shock.

In a stop-early case, Stage 3 completes the design-only deliverables, writes a blocker note, and proceeds to Stage 4.
