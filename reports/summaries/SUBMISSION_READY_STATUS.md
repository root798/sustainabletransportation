# SUBMISSION_READY_STATUS.md

**Date:** 2026-04-14
**Scope:** California + Ohio baseline quantitative package. U.S. Average quarantined.
**Governing diagnosis:** `audits/final_consistency/MASTER_FULL_STACK_DISCOVERY_DOSSIER.md`
**Patch record:** `audits/final_consistency/SUBMISSION_CRITICAL_FIXES.md`

---

## Headline verdict

**Submission-safe** for the California / Ohio baseline story. All nine review-bait defects flagged in the dossier are now either fixed (Tier 1) or safely disclosed + gated (Tier 2 safe items). No redesign of uncertainty, priors, policy-conditional MC, L2 architecture, or U.S. Average rehabilitation was performed, consistent with the patch-pass scope.

## Paper-safe scope — unchanged

- **Paper-safe regions:** California, Ohio.
- **Quarantined:** U.S. Average (banners now present on v4 pages 00, 01, 02, 03, 04, 05; visually de-emphasised on page 02).
- **Paper-safe MC scope:** baseline policy only. Aggressive / conservative MC are exploratory and must not be cited (Methods M14; warning banner on v4 page 04; `NON_PAPER_SAFE_QUANTILE_KEYS` in `v3_streamlit_app/data_contracts/load_results.py`).
- **Interpretation boundary:** California 2030, Ohio 2031 (unchanged — MC was not regenerated).
- **Peak / turning attribution:** deterministic central trajectory (Methods M12). MC p50 trajectory values appear only in supplementary MC metrics table; never mixed with deterministic numbers in the main text.
- **Ohio turning year:** "not reached within horizon" for the deterministic trajectory. MC conditional p50 = 2081 across 87/200 runs (achieved_fraction = 0.435) is now an explicit column in `results/ohio__policy-baseline__model-fixed_table_metrics_quantiles.csv` and disclosed in Methods M13. This conditional figure is NOT cited as an unconditional main-text claim.
- **CA BEV saturation wording:** sidecar is authoritative. CA BEV shows `no_saturation_detected`, so the cap-artefact caveat is withdrawn for that panel; replacement wording in place across Methods M5, RESULTS R5, CAPTION Fig. 3c, caption .txt, and v4 page 00 annotation.
- **Shocks:** only `moderate` severity on disk. `SHOCK_SCOPE_HONESTY.md` gates paper wording; no paper-support figure cites mild / severe.

## Tier 1 — all fixed

1. Ohio turning-year quantile handling patched (backend + support files).
2. Methods-support sentences added (M9 utility-phase; M10 battery-production; M11 2075 linear ramp).
3. Peak-year attribution convention applied uniformly (deterministic central trajectory).
4. CA BEV saturation wording reframed to match sidecar across captions, dashboard, and alignment docs.
5. Dashboard trust fixes: US Average banners on v4 pages 01 + 05; page 02 de-emphasised to dashed line with opacity 0.4 and "(quarantined — exploratory only)" legend suffix.
6. Affected CA/OH paper-support captions updated.

## Tier 2 — safe items fixed

- A — Baseline-only MC honesty disclosed in Methods M14 + UI + alignment docs.
- B — Policy-conditional MC gated at the UI label level and the data-contracts registry.
- C — Stale `QUANTILE_PATHS` repointed; legacy notebook paths moved behind explicit `"notebook"` variant.
- D — v3/v4 live-resim both now forward `model_variants` to `TransportModel`.
- E — Defensive warnings for unknown dist / orphan data_uncertainty key / degenerate beta / cav_levels + sti_levels sum.
- F — Shock-scope wording honesty note created; limits paper claims to moderate severity.
- G — Lightweight supplementary shock UI page implemented (`v4_streamlit_app/pages/06_Structural_Shocks_Explorer.py`).
- H — Minor dashboard wording polish in place.

## Files of interest for reviewers

- Patch record: `audits/final_consistency/SUBMISSION_CRITICAL_FIXES.md`
- Attribution + disclosure rules: `audits/step_06_paper_alignment/METHODS_ALIGNMENT.md` (M9–M14), `audits/step_06_paper_alignment/RESULTS_ALIGNMENT.md` (R4, R5, do-not-use), `audits/step_06_paper_alignment/CAPTION_ALIGNMENT.md` (header + Fig. 3c)
- Shock honesty: `audits/step_07_structural_shocks/SHOCK_SCOPE_HONESTY.md`
- Shock UI: `audits/step_07_structural_shocks/SHOCK_UI_IMPLEMENTATION_NOTE.md`
- Regenerated support CSVs:
  - `results/california__policy-baseline__model-fixed_table_metrics_quantiles.csv`
  - `results/ohio__policy-baseline__model-fixed_table_metrics_quantiles.csv`

## Submission gate

- **Remaining hard blockers:** 0.
- **Remaining editorial tasks before submission paste-in:** re-retrieve the exact 2050 CA p50 for RESULTS R3 (currently cited as `≈ 4.2 × 10⁹`, live value); confirm no rebuttal or manuscript text contradicts Methods M12–M14 after paste-in.
- **Remaining computational risk:** none introduced by this patch pass. Baseline quantile + mc_runs CSVs unchanged. Interpretation boundary unchanged. Sidecar saturation metadata unchanged.
- **Deferred** (documented in `SUBMISSION_CRITICAL_FIXES.md`): policy-conditional MC redesign, Ohio prior recalibration, dual-axis scale-factor redesign, U.S. Average rehabilitation, mild/severe shock regeneration, `_SHOCK_ATTR_MAP` patch, v2/v2.1/nested-clone housekeeping.

## One-line conclusion

The California + Ohio baseline package is **submission-safe**; remaining risk is **editorial**, not computational.
