# US_AVERAGE_TRACE_VALIDATION.md

Validation that the forensic-trace stage completed correctly and that all actionable source-of-truth back-doors have been closed. U.S. Average quantitative outputs remain in quarantine pending external source confirmation.

---

## A. Scenario loader priority — clean across all four active codepaths

Live check:

```python
from footprint_model import load_config as fm_lc
from v3_streamlit_app.dashboard_core import load_base_config as v3_lc
from v4_streamlit_app.core import load_base_config as v4_lc
from v3_streamlit_app.data_contracts.load_results import load_config as dc_lc

# All four return identical values for every region.
```

Result:

| region | footprint_model | v3 dashboard_core | v4 core | v3 data_contracts | agree? |
| --- | ---: | ---: | ---: | ---: | :---: |
| california | 37 428 700 | 37 428 700 | 37 428 700 | 37 428 700 | ✓ |
| ohio | 10 385 000 | 10 385 000 | 10 385 000 | 10 385 000 | ✓ |
| us_average | 23 906 850 | 23 906 850 | 23 906 850 | 23 906 850 | ✓ |

All four loaders try `scenarios/{region}/scenario.json` first and fall back to `configs/{region}.json`. The v3 data-contracts loader (previously a `configs/`-only back-door) is now part of this contract.

### A.1 Canonical + legacy both present

```
scenarios/california/scenario.json     exists
configs/california.json                 exists
scenarios/ohio/scenario.json            exists
configs/ohio.json                       exists
scenarios/us_average/scenario.json      exists
configs/us_average.json                 exists
```

All three regions have both copies in sync. No drift.

### A.2 Flask region discovery

```
app.get_valid_states() → ['california', 'ohio', 'us_average']
```

`scenarios/` is scanned first. Works even if `configs/` is empty (sorted, de-duplicated union).

### A.3 run.py pre-flight

```
run.check_configs_exist() → True
log line: "All required scenario files found (canonical scenarios/ or legacy configs/)."
```

Accepts either path per region.

---

## B. No remaining stale direct `configs/` dependency in active code

Grep over all active Python:

```
rg 'configs/(california|ohio|us_average)\.json|CONFIGS_DIR / "(california|ohio|us_average)|CONFIG_PATHS\['   --glob '*.py' --glob 'app.py' --glob 'run.py'
```

Hits, with classification:

| File | Line | Reference | Status |
| --- | ---: | --- | --- |
| `v3_streamlit_app/data_contracts/load_results.py` | 59 | `"california": CONFIGS_DIR / "california.json"` inside `CONFIG_PATHS` fallback dict | **intentional** — preserved legacy fallback; primary `SCENARIO_PATHS` dict now precedes it. |
| `v2_streamlit_app/data_contracts/load_results.py` | 47 | Same pattern in archived v2 app. | **archived** — not on active stack. |
| `v2_1_streamlit_app/data_contracts/load_results.py` | 47 | Same pattern in archived v2.1 app. | **archived**. |
| `v2_streamlit_app/data_contracts/provenance.py` | 145, 159 | `source_files: ["configs/..."]` metadata. | **archived**. |
| `v2_1_streamlit_app/data_contracts/provenance.py` | 145, 159 | Same. | **archived**. |
| `v2_streamlit_app/pages/02_Utility_Phase_Analysis.py` | 558 | Narrative string "Scenario parameters documented in configs/california.json (and variants)." | **archived**. |
| `v2_1_streamlit_app/pages/02_Utility_Phase_Analysis.py` | 568 | Same narrative. | **archived**. |

**No active-path back-door remains.** The only `configs/`-only references are either (a) the deliberate fallback dict in the v3 data-contracts loader, or (b) archived v2 / v2.1 apps documented as not-on-active-stack in `docs/ROOT_CLEANUP_RECOMMENDATIONS.md`.

---

## C. Provenance correctness

`v3_streamlit_app/data_contracts/provenance.py` blocks for `Fleet Counts`, `EV Fraction`, and `Clean Energy Fraction` now list `source_files` as:

```
scenarios/california/scenario.json
scenarios/ohio/scenario.json
scenarios/us_average/scenario.json
```

Verified by reading the file post-edit. Previous `configs/*.json` strings were removed via a `replace_all` operation; grep for `configs/california.json` in `v3_streamlit_app/data_contracts/provenance.py` returns zero hits.

Archived `v2_streamlit_app` and `v2_1_streamlit_app` provenance files still say `configs/*.json`. Intentionally not modified per `docs/ROOT_CLEANUP_RECOMMENDATIONS.md §To IGNORE in later prompts`.

---

## D. U.S. Average status — QUARANTINED

Forensic trace result (see `US_AVERAGE_SOURCE_TRACE.md`):

- **Upstream source**: not discoverable in the repository. No script, notebook, CSV, TeX table, or comment derives the 12 anomalous cells.
- **Historical origin**: commit `26cb28c` (2025-03-12, author xiw019, message "updated new algorithm and fixed bugs"). Values entered directly into JSON without an accompanying derivation.
- **Pattern**: 12 of 18 cells (all sensing + communication) are 3.3–42× CA/OH; the remaining 6 (all computing) are 0.6–1.0× CA/OH. The pattern is consistent and systematic, which rules out random data-entry error.
- **Most likely cause**: source-table mismatch — the sensing / communication entries appear to come from an infrastructure-scale engineering reference that was not reconciled with the per-vehicle / per-intersection scale used for CA and OH. Cannot be confirmed without the original author.
- **Propagation**: the anomaly drives U.S. Average 2050 annual energy to **2.44× California** and **7.39× Ohio** despite U.S. Average having lower CAV and STI targets. All derived metrics (peak year, turning year, interpretation-boundary year) for U.S. Average are contaminated.

**Verdict**: **U.S. Average is NOT repaired.** It remains quarantined. `REGION_NOTES` in both v3 and v4 dashboards already warns that U.S. Average load figures are not paper-safe; that warning is retained and the forensic report now documents the exact cells, the exact multipliers, and the exact git commit at fault.

---

## E. Files changed

| File | Why |
| --- | --- |
| `v3_streamlit_app/data_contracts/load_results.py` | Added `SCENARIOS_DIR`, `SCENARIO_PATHS`; rewrote `load_config` to prefer `scenarios/` with fallback to `configs/`. |
| `v3_streamlit_app/data_contracts/provenance.py` | `source_files` lists updated from `configs/*.json` to `scenarios/{region}/scenario.json`. |
| `app.py` | `get_valid_states()` now unions `scenarios/{region}/scenario.json` presence with legacy `configs/*.json` presence; sorted output. |
| `run.py` | `check_configs_exist()` accepts either canonical or legacy path per region. |

### Reports created in this stage

- `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`
- `audits/step_04_uncertainty_architecture/SOURCE_OF_TRUTH_BACKDOOR_FIXES.md`
- `audits/step_04_uncertainty_architecture/US_AVERAGE_TRACE_VALIDATION.md` (this file)

### Reports NOT created (intentionally)

- No code change was made to `scenarios/us_average/scenario.json`. The anomalous values are documented, not silently patched.
- No code change was made to `_update_quantities` or any other simulation-engine function. The forensic stage is audit-only for simulation code.

---

## F. Deferred (requires human input)

1. Confirm or cite the upstream source of the 12 anomalous U.S. Average `consumption_rates` cells. If no source is produced within one review cycle, the recommended action is:
   - Rescale sensing and communication cells to the arithmetic midpoint of CA and OH, documenting the change.
   - OR regenerate `scenarios/us_average/scenario.json:consumption_rates` as a true midpoint of CA+OH across every cell.
2. Decide whether to remove `configs/` entirely in a later stage, now that every active codepath has been migrated to the canonical `scenarios/` path.
3. Decide whether to retire the archived `v2_streamlit_app/` and `v2_1_streamlit_app/` apps. They still reference `configs/` exclusively.

Until item (1) is resolved, U.S. Average remains quarantined from paper figures.
