# CHECKPOINT_SOURCE_OF_TRUTH_AUDIT.md

Checkpoint verification of the canonical scenario load path before the L1/L2/L3 redesign. Confirms that `scenarios/{region}/scenario.json` is genuinely the primary read path and identifies every remaining back-door that bypasses it.

## 1. Live verification — canonical loader wins

| Loader | Source of truth | Fallback | Verified |
| --- | --- | --- | --- |
| `footprint_model.load_config(region)` | `scenarios/{region}/scenario.json` | `configs/{region}.json` | ✓ |
| `v3_streamlit_app.dashboard_core.load_base_config(region)` | `scenarios/{region}/scenario.json` | `configs/{region}.json` | ✓ |
| `v4_streamlit_app.core.load_base_config(region)` | `scenarios/{region}/scenario.json` | `configs/{region}.json` | ✓ |

Live smoke test confirmed both canonical and fallback paths hold the same California baseline (`total_cars = 37 428 700`). Both paths currently carry the new `e_clean` / `icecav_power_factor` / `retire_year` distribution specs; there is no silent drift today.

## 2. Back-doors that bypass the canonical scenario files

These are the paths that still read from `configs/` directly and will therefore see `configs/` rather than `scenarios/` if the two ever diverge. They are NOT currently broken, because both copies are in sync. They are risks for the redesign.

| # | File | Line(s) | What it does | Risk |
| --- | --- | --- | --- | --- |
| B1 | `v3_streamlit_app/data_contracts/load_results.py` | 17–20, 48–52, 153–177 | Defines its own `CONFIG_PATHS = {"california": CONFIGS_DIR/"california.json", ...}` and a private `load_config(region)` that reads only from `CONFIGS_DIR`. Imported by `validators.py`. | **HIGH** — a separate data-contracts loader that does not consult `scenarios/`. If scenarios/ is edited and configs/ is not, any validator or provenance page using this loader reads stale data silently. |
| B2 | `v3_streamlit_app/data_contracts/provenance.py` | 133, 134, 135, 151, 152, 153, 168, 169, 170 | `source_files: ["configs/california.json", ...]` in the provenance registry. Metadata only, not a runtime read. | **MEDIUM** — provenance captions will mis-state the source. |
| B3 | `app.py` | 111–124 | Lists valid regions by scanning `os.path.join(..., 'configs')`. If `configs/` is ever emptied, the Flask UI will show no regions even though `scenarios/` has them. The loader call itself (`load_config(state)` via `from footprint_model import load_config`) already uses the canonical path. | **MEDIUM** — region discovery, not data loading. |
| B4 | `run.py` | 23–27 | Pre-flight check `required_configs = ["california.json", "ohio.json", "us_average.json"]` inside `configs/` before running. | **LOW** — precondition only, does not load data. |
| B5 | `v2_streamlit_app/`, `v2_1_streamlit_app/` | multiple | Archived Streamlit apps. Their `data_contracts/load_results.py`, `data_contracts/provenance.py`, and page references still hard-code `configs/*.json`. They do not import from `scenarios/`. | **LOW** (archived) — but anyone running the v2 apps will see results keyed to `configs/`. |
| B6 | `CLEAR_ATS/` (nested subfolder) | — | A full parallel clone of an earlier repo state. Contains its own `footprint_model.py`, `app.py`, `run.py`, `configs/`, `v2_streamlit/`, and stale root-level JSONs. Not imported by the active code (Python imports resolve from the repo root), but a user who opens that folder will see stale everything. | **MEDIUM (navigation) / LOW (runtime)** — no active code depends on it. |
| B7 | `v3_streamlit_app/scripts/generate_v2_1_reports.py` | file | Legacy-report generator still references `configs/`. | **LOW** — one-off tool. |
| B8 | `CONFIG_PATHS` / `DETERMINISTIC_PATHS` / `QUANTILE_PATHS` dicts in v2 & v2_1 data_contracts | multiple | Same pattern as B1 in the archived apps. | **LOW** (archived). |

## 3. Stale root-level JSONs — confirmed archived

Three loose root-level JSONs (`california.json`, `ohio.json`, `us_average.json` with older values such as CA `total_cars = 32 060 000`) were moved to `audits/step_00_legacy/stale_root_scenarios/` during step 03. Verified via `ls` — none remain at the repo root.

## 4. Drift detection — `scenarios/` vs `configs/` today

| Region | `scenarios/{region}/scenario.json` | `configs/{region}.json` | In sync? |
| --- | --- | --- | --- |
| california | present, canonical | present (identical copy) | ✓ |
| ohio | present, canonical | present (identical copy) | ✓ |
| us_average | present, canonical | present (identical copy) | ✓ |

All three pairs contain the new `e_clean` / `icecav_power_factor` / `retire_year` distributions and the `"semantic"` annotations. No drift today. Forward-sync obligation (from `docs/SCENARIO_TEMPLATE_REORGANIZATION_PLAN.md §Forward sync obligation`) is intact because no edits have happened post-reorg.

## 5. Summary — source-of-truth priority status

- **Canonical loader priority: CLEAN.** `footprint_model`, v3 `dashboard_core`, and v4 `core` all try `scenarios/` first.
- **Back-door count: 4 active + 4 archived.** The only high-risk one is `v3_streamlit_app/data_contracts/load_results.py`'s private `load_config`. Redesign must either point this loader at `scenarios/` or retire it and route v3 validators through `dashboard_core.load_base_config`.
- **Drift today: none.** All three scenario files agree between `scenarios/` and `configs/`.
- **Drift risk going forward: present.** As soon as anyone edits `scenarios/` and does not mirror to `configs/`, the back-doors listed in §2 read stale data.

## 6. Verdict

Source-of-truth loading is **clean for the three primary codepaths** (CLI, v3 dashboard_core, v4 core). Four remaining back-doors (B1–B4) must be addressed in the redesign. The simplest safe action is:

1. Retire the private loader in `v3_streamlit_app/data_contracts/load_results.py` → delegate to `dashboard_core.load_base_config`.
2. Update `v3_streamlit_app/data_contracts/provenance.py` source-file strings to point at `scenarios/`.
3. Update `app.py` region-discovery to scan `scenarios/` (fall back to `configs/`).
4. Update `run.py` pre-flight check to accept either `scenarios/{region}/scenario.json` or `configs/{region}.json`.

None of these require a redesign. They are one-line-each corrections that remove the drift risk before the redesign starts writing to scenarios/ only.
