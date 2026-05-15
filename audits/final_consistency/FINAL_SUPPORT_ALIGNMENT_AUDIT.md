# FINAL_SUPPORT_ALIGNMENT_AUDIT.md

**Date:** 2026-04-16
**Scope:** verify every support Markdown file that reports uncertainty numbers is aligned with the final regenerated bundle outputs (200-run MC, 2026-04-16).

---

## Authoritative numbers (from FINAL_BUNDLE_REGEN_STATUS.md)

| Region | Bundle | W/M 2030 | W/M 2050 | IB year |
|---|---|---:|---:|---:|
| CA | default | 0.83 | 0.88 | 2064 |
| CA | paper-safe | 1.64 | 2.41 | 2028 |
| OH | default | 0.82 | 0.80 | never |
| OH | paper-safe | 1.59 | 1.92 | 2029 |

## Files audited

### reports/rebuttal_support/DECISION_MEANINGFUL_DEFAULT_AFTER_2030.md

- **Section 2 table** reported CA default W/M 2030 = 0.74, IB = 2065 (from old 120-run regen).
- **Now stale.** Authoritative: 0.83, 2064.
- **Fix required:** update the numbers.

### reports/rebuttal_support/PARAMETER_LEVEL_CONTROL_JUSTIFICATION.md

- **Section 8** reported CA default 0.74, OH default 0.76, CA IB 2065, OH IB never.
- **Now stale.** Authoritative: CA 0.83, OH 0.82, CA IB 2064, OH never (unchanged).
- **Fix required:** update the numbers.

### reports/rebuttal_support/TOP_UNCERTAINTY_DRIVERS_SUMMARY.md

- Contains parameter-level isolation numbers (from the 80-run experiment). These are NOT bundle-specific and are still valid. **No fix needed.**
- The "one-line answer" at the end does not cite bundle W/M numbers. **No fix needed.**

### reports/summaries/FINAL_PARAMETER_LEVEL_UNCERTAINTY_STATUS.md

- **Section 7** reported CA default 0.74, OH 0.76, CA IB 2065, OH never.
- **Now stale.** Authoritative: CA 0.83, OH 0.82, CA IB 2064.
- **Fix required:** update.

### reports/summaries/SCENARIO_EXPLORER_FINAL_ALIGNMENT_STATUS.md

- **Section 7** same old numbers.
- **Fix required:** update.

## Fix plan

Update the four files above with the final 200-run authoritative numbers. The parameter-level experiment numbers (80-run isolation) remain valid and do not need updating.
