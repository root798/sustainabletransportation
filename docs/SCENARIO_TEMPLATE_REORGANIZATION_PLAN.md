# SCENARIO_TEMPLATE_REORGANIZATION_PLAN.md

Plan that was executed in the post-audit cleanup stage to move regional scenario data from `configs/` into a cleaner, human-editable `scenarios/{region}/` tree.

## Problem

Before this stage:

- Scenario data lived in `configs/{region}.json`. That folder name implies "configuration for the runtime", not "source of truth for scenario assumptions".
- There was no matching README or provenance note for each region.
- A human asked to "edit the original California numbers" had to know to open `configs/california.json` — not obvious from the layout.
- Load paths in `footprint_model.load_config`, `v3_streamlit_app/dashboard_core.load_base_config`, and `v4_streamlit_app/core.load_base_config` were hard-coded to `configs/`.

## Options considered

**Option A** — keep `configs/{region}.json` as canonical, add documentation only. Rejected: the word "config" still obscures the scenario-data role.

**Option B** — split each scenario into multiple files (initial_data.json, uncertainty.json, policies.json, ...). Rejected: the sampler and deep-merge expect a single dict; splitting adds an assembly step for no gain.

**Option C** (chosen) — relocate to `scenarios/{region}/scenario.json`, keep the single-file JSON format, add a per-region README, update the loader to prefer the new path and fall back to the old one.

## What changed

1. Created the tree:
   ```
   scenarios/
   ├── README.md
   ├── california/ { scenario.json, README.md }
   ├── ohio/       { scenario.json, README.md }
   └── us_average/ { scenario.json, README.md }
   ```

2. Copied each `configs/{region}.json` verbatim to `scenarios/{region}/scenario.json`. Byte-identical content to start.

3. Updated loaders to try `scenarios/` first, fall back to `configs/`:
   - `footprint_model.load_config` (lines touched: the function body).
   - `v3_streamlit_app/dashboard_core.load_base_config`.
   - `v4_streamlit_app/core.load_base_config`.
   - New module-level constant `SCENARIOS_DIR` alongside the retained `CONFIGS_DIR`.

4. Wrote per-region README under `scenarios/{region}/README.md` with provenance, headline values, active distribution specs, known L2 gaps, editing notes, and paper-safety status. U.S. Average README includes the full anomaly warning.

5. Wrote top-level `scenarios/README.md` with load-path contract, edit rules, and links.

6. Wrote the convention (`docs/SCENARIO_FILE_CONVENTION.md`) and index (`docs/SCENARIO_SOURCE_OF_TRUTH_INDEX.md`).

## What was deliberately NOT changed

- `configs/*.json` remain on disk. This preserves backward compatibility with any external notebook, script, or legacy tool (for example `app.py` reads through the same loader; `v2_streamlit_app/` hard-codes `configs/` paths in its data contracts). Removing `configs/` now would break those.
- The JSON format itself is unchanged. Keys, sections, and value shapes are identical.
- No config-key renames (`growth_rates.cav` → `targets.cav_by_2075`) were applied. That remains deferred with `"semantic"` annotations as mitigation.

## Forward sync obligation

Whenever `scenarios/{region}/scenario.json` is edited, the `configs/{region}.json` fallback goes out of date. Options:

1. **Do nothing** — the canonical path wins because it is tried first. The fallback silently holds older numbers. Acceptable while nothing else reads `configs/`.
2. **Manual copy** — after editing `scenarios/{region}/scenario.json`, copy it over `configs/{region}.json`. Low-effort, prevents drift.
3. **Delete `configs/` entirely** — remove the legacy fallback once nothing depends on it. Best long-term answer; deferred to a later cleanup round.

Current recommendation: option 2 for now; option 3 at the next refactor that also removes the archived Flask / v2 Streamlit code.

## Verification

See `docs/REPORT_REORGANIZATION_VALIDATION.md §Scenario load path` for end-to-end evidence that both CLI and dashboards now read from `scenarios/` first.
