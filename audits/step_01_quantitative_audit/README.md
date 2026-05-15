# step_01_quantitative_audit

Full quantitative audit of the CLEAR-ATS codebase before any fixes were applied. Read this stage first to understand what the repository looked like going in.

## Files

| File | What it contains |
| --- | --- |
| `PARAMETER_AUDIT_CURRENT.csv` | Machine-readable inventory of every active numerical parameter with per-parameter metadata (path, semantic role, units, region-specific vs global, used in live simulation vs dashboard only, overridden by policy, candidate uncertainty class, risk notes). |
| `PARAMETER_CODEPATH_TRACE.md` | Stage-by-stage live execution path from config load → policy merge → MC sampling → runtime controls → `TransportModel` → post-processing → CSV write → dashboard read, per parameter family. |
| `PARAMETER_INCONSISTENCY_REPORT.md` | Every mismatch between scientific framing, config files, simulation code, dashboards, and committed outputs. Tagged `[CRITICAL]` / `[STRUCTURAL]` / `[COSMETIC]`. |
| `UNCERTAINTY_LAYER_CANDIDATES.md` | Preliminary classification of every audited parameter into L1 / L2 / L3 / structural-shock / deterministic-control. |
| `QUANTITATIVE_AUDIT_MEMO.md` | Scientific interpretation memo. Sections: safe numbers, numbers to unify, numbers needing better uncertainty treatment, dead / stale items, numbers weakening the uncertainty story, top-10 risks. Final summary and pre-fix decisions list. |

## Status

Inputs to `step_02_audit_fixes`. No file here has been modified since its original creation; edits go into later stages.

## Key findings (condensed)

- Two coexisting turning-year definitions.
- Interpretation-boundary start year split between v3 (2026) and v4 (2027).
- `--mc 0` was not actually deterministic.
- U.S. Average narrative contradicted its growth/consumption numbers.
- Load-model uncertainty essentially absent (no MC on `consumption_rates.*`, `icecav_power_factor`, level mixes, `retire_year`, or `e_clean`).
- `growth_rates.cav`/`sti` were target fractions disguised as growth rates.
- Hard-coded `51` and `2024` in `_update_quantities`.
- `cumulative_new_cars[0] = self.n_cav` — off-by-`n_cav` bug.
- Dashboard overlay silently stale under slider motion.

All items tracked in `PARAMETER_INCONSISTENCY_REPORT.md §A–J`.
