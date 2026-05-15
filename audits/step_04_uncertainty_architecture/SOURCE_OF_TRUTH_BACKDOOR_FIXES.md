# SOURCE_OF_TRUTH_BACKDOOR_FIXES.md

Mechanical fixes applied to eliminate the four source-of-truth back-doors identified in `CHECKPOINT_SOURCE_OF_TRUTH_AUDIT.md §B`. No scientific values changed; only load-path priorities and provenance strings.

---

## Summary

| # | File | Old behaviour | New behaviour |
| --- | --- | --- | --- |
| 1 | `v3_streamlit_app/data_contracts/load_results.py` | Private `load_config(region)` read only from `configs/{region}.json`. | Reads `scenarios/{region}/scenario.json` first; falls back to `configs/{region}.json`. |
| 2 | `v3_streamlit_app/data_contracts/provenance.py` | Nine `source_files` strings referenced `configs/*.json`. | Updated to `scenarios/{region}/scenario.json`. |
| 3 | `app.py` | `get_valid_states()` scanned `configs/` only. | Scans `scenarios/` first, then `configs/`; de-duplicates; sorted list. |
| 4 | `run.py` | Pre-flight `check_configs_exist` demanded `configs/*.json`. | Accepts either `scenarios/{region}/scenario.json` or `configs/{region}.json`. |

No other code was modified. `footprint_model.load_config`, `v3_streamlit_app.dashboard_core.load_base_config`, and `v4_streamlit_app.core.load_base_config` already follow the canonical-first rule and were not touched.

---

## 1. `v3_streamlit_app/data_contracts/load_results.py`

### Old path assumption

```python
CONFIGS_DIR = DATA_ROOT / "configs"

CONFIG_PATHS = {
    "california": CONFIGS_DIR / "california.json",
    "ohio": CONFIGS_DIR / "ohio.json",
    "us_average": CONFIGS_DIR / "us_average.json",
}

def load_config(region):
    path = CONFIG_PATHS.get(region)
    ...
```

The `load_config` function in this module is imported by `validators.py` and is callable from any page under `v3_streamlit_app/`. It bypassed the canonical loader in `dashboard_core`.

### New canonical priority

```python
SCENARIOS_DIR = DATA_ROOT / "scenarios"
CONFIGS_DIR   = DATA_ROOT / "configs"

SCENARIO_PATHS = {
    "california": SCENARIOS_DIR / "california" / "scenario.json",
    "ohio": SCENARIOS_DIR / "ohio" / "scenario.json",
    "us_average": SCENARIOS_DIR / "us_average" / "scenario.json",
}
CONFIG_PATHS = {
    "california": CONFIGS_DIR / "california.json",
    "ohio": CONFIGS_DIR / "ohio.json",
    "us_average": CONFIGS_DIR / "us_average.json",
}

def load_config(region):
    primary = SCENARIO_PATHS.get(region)
    legacy  = CONFIG_PATHS.get(region)
    path = primary if (primary is not None and primary.exists()) else legacy
    ...
```

### Compatibility note

- `CONFIG_PATHS` is preserved so any external code that imports the symbol directly still works.
- The public `load_config(region)` signature is unchanged.

---

## 2. `v3_streamlit_app/data_contracts/provenance.py`

### Old path assumption

Three provenance blocks (`Fleet Counts`, `EV Fraction`, `Clean Energy Fraction`) listed `source_files` as:

```python
"source_files": [
    "configs/california.json",
    "configs/ohio.json",
    "configs/us_average.json",
    ...
]
```

### New canonical priority

All three blocks now list:

```python
"source_files": [
    "scenarios/california/scenario.json",
    "scenarios/ohio/scenario.json",
    "scenarios/us_average/scenario.json",
    ...
]
```

### Compatibility note

These strings are metadata only — rendered in the Data & Provenance page and in reports. Changing them does not affect any runtime read path. They were wrong (pointed at the legacy fallback rather than the canonical source), and are now correct.

---

## 3. `app.py` region discovery

### Old path assumption

```python
def get_valid_states():
    configs_dir = os.path.join(os.path.dirname(__file__), 'configs')
    valid_states = []
    try:
        for filename in os.listdir(configs_dir):
            if filename.endswith('.json'):
                valid_states.append(filename[:-5])
    except Exception as e:
        ...
    return valid_states
```

If `configs/` were ever emptied, the Flask UI would show no regions even though `scenarios/` was populated.

### New canonical priority

```python
def get_valid_states():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    scenarios_dir = os.path.join(repo_root, 'scenarios')
    configs_dir   = os.path.join(repo_root, 'configs')
    valid_states = set()
    # Scan scenarios/{region}/scenario.json first
    if os.path.isdir(scenarios_dir):
        for entry in os.listdir(scenarios_dir):
            if os.path.isfile(os.path.join(scenarios_dir, entry, 'scenario.json')):
                valid_states.add(entry)
    # Then scan legacy configs/
    if os.path.isdir(configs_dir):
        for filename in os.listdir(configs_dir):
            if filename.endswith('.json'):
                valid_states.add(filename[:-5])
    if not valid_states:
        valid_states = {'california', 'ohio', 'us_average'}
    return sorted(valid_states)
```

### Compatibility note

- Behaviour is additive — a region present in either folder is listed.
- Sort order is alphabetical (previously directory-traversal order). This is stable and reproducible across filesystems.
- Actual data loading still goes through `footprint_model.load_config`, which already uses the canonical-first rule.

---

## 4. `run.py` pre-flight check

### Old path assumption

```python
def check_configs_exist():
    config_dir = Path("configs")
    required_configs = ["california.json", "ohio.json", "us_average.json"]
    if not config_dir.exists():
        return False
    missing = [cfg for cfg in required_configs if not (config_dir / cfg).exists()]
    if missing:
        return False
    return True
```

A redesign that stopped writing to `configs/` would break this precondition even if `scenarios/` was fully populated.

### New canonical priority

```python
def check_configs_exist():
    scenarios_dir = Path("scenarios")
    configs_dir   = Path("configs")
    required_regions = ["california", "ohio", "us_average"]

    missing = []
    for region in required_regions:
        canonical = scenarios_dir / region / "scenario.json"
        legacy    = configs_dir / f"{region}.json"
        if not canonical.exists() and not legacy.exists():
            missing.append(region)
    return not missing
```

### Compatibility note

- Pre-flight passes if either path exists for each region.
- Log line updated to mention both paths so operators see which source was used.

---

## Remaining intentional fallbacks

1. `configs/{region}.json` kept on disk as a legacy fallback. This is deliberate; see `docs/FILE_PATH_REDIRECT_MAP.md §Scenario source files` and `docs/SCENARIO_TEMPLATE_REORGANIZATION_PLAN.md §Forward sync obligation`.
2. Archived `v2_streamlit_app/` and `v2_1_streamlit_app/` data_contracts still reference `configs/`. Not fixed here — these apps are archived, and the files include explicit "archive-only" notes in `docs/ROOT_CLEANUP_RECOMMENDATIONS.md`.
3. Nested `CLEAR_ATS/` clone still references its own `configs/`. Not a runtime path; ignored.
4. v2/v2_1 `data_contracts/provenance.py` still say `configs/*.json`. Not fixed — same archival reason.

If a future stage deletes `configs/`, items (2) and (4) will produce stale metadata but will not break; the archived apps will break on load. That is considered acceptable per the `docs/ROOT_CLEANUP_RECOMMENDATIONS.md §Rule of thumb for future root additions`.

---

## Files changed in this stage

- `v3_streamlit_app/data_contracts/load_results.py`
- `v3_streamlit_app/data_contracts/provenance.py`
- `app.py`
- `run.py`

Four edits total. No scenario values, no simulation code, no dashboard logic modified.
