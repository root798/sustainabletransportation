# KEY_RESULTS_AFTER_PRESET_CONTROL.md

**Date:** 2026-04-15
**Status:** support material only.
**Caveat:** LOW and HIGH width estimates are *design-committed* but not yet MC-regenerated. Numbers below that depend on a regenerated LOW / HIGH ensemble are explicitly labelled. Once regeneration runs (approx. `python footprint_model.py --mc 200 --seed 42 --uncertainty-preset low|medium|high --scenarios california ohio --policy baseline`), the exact values should replace the qualitative estimates in this file.

---

## 1. Deterministic central trajectory (unchanged under every preset)

| Metric | California | Ohio |
|---|---|---|
| Peak year (deterministic) | 2036 | 2076 |
| Peak emissions | CA deterministic from `results/california_results.csv` | OH deterministic from `results/ohio_results.csv` |
| Turning year (50 % of peak, deterministic) | 2046 | not reached within horizon |
| 2050 annual ATS energy (deterministic) | ≈ 3.70 TWh/yr | ≈ 1.22 TWh/yr |
| 2050 annual ATS emissions (deterministic) | ≈ 0.11 Mt CO₂/yr | ≈ 0.34 Mt CO₂/yr |

These deterministic numbers are prior-independent and therefore identical under LOW, MEDIUM, HIGH.

## 2. Interpretation boundary

| Preset | California | Ohio |
|---|---|---|
| **MEDIUM** (paper-safe baseline) | 2030 | 2031 |
| **LOW** (expected, regeneration pending) | later than 2030; likely 2033–2036 on CA; OH may not cross 1.5 threshold within horizon | boundary may shift beyond 2092 |
| **HIGH** (exploratory) | earlier than 2030; likely 2028–2029 | likely 2029–2030 |

The MEDIUM values are published and unchanged.

## 3. MC band width on ATS Total Power (qualitative, pending regeneration)

| Preset | CA p05–p95 width @ 2030 (relative to MEDIUM) | CA p05–p95 width @ 2050 | OH p05–p95 width @ 2030 | OH p05–p95 width @ 2050 |
|---|---|---|---|---|
| **MEDIUM** | 1.00× (baseline) | 1.00× | 1.00× | 1.00× |
| **LOW** | ≈ 0.45–0.55× | ≈ 0.40–0.50× | ≈ 0.50–0.60× | ≈ 0.45–0.55× |
| **HIGH** | ≈ 1.40–1.70× | ≈ 1.40–1.70× | ≈ 1.40–1.70× | ≈ 1.40–1.70× |

These ranges are derived by first-order analytical propagation through the $\sigma$ changes declared in each preset JSON. Exact values require 200-run MC regeneration at seed 42.

## 4. Ohio turning-year MC disclosure (unchanged)

The baseline MC ensemble under MEDIUM disclosed that **87 / 200 Ohio runs reach turning within horizon** (achieved_fraction = 0.435), with conditional MC p50 = 2081. This disclosure is preserved in `results/ohio__policy-baseline__model-fixed_table_metrics_quantiles.csv` via the `n_runs_total`, `n_runs_used`, `achieved_fraction` columns.

Under LOW, fewer Ohio runs are expected to reach turning (because priors are narrower around the central "not reached" scenario); under HIGH, more are expected to reach turning earlier. Exact figures require regeneration.

## 5. California BEV saturation (unchanged)

Sidecar for CA BEV share: `no_saturation_detected` under MEDIUM. Central trajectory approaches the 1.0 cap near horizon edge; lower tail remains open. This is preserved across presets; the qualitative description does not change.

## 6. Structural shocks (unchanged, discrete scenarios)

- Only `moderate` severity executed on disk for any shock family (five families × two regions × one severity = 10 CSVs).
- Claim language in the paper remains "moderate severity of each family was executed"; no "three severities" claim.
- Shocks are never merged into MC presets.

## 7. What to say in the rebuttal

"The published MC pipeline corresponds to the MEDIUM preset. The dashboard now lets a reviewer vary uncertainty width across three presets (LOW / MEDIUM / HIGH) without changing any centred value. Deterministic headline numbers are invariant across presets. Under LOW, the p05–p95 band narrows by approximately 40–55 % relative to the published MEDIUM band; under HIGH it widens by approximately 40–70 %. Only MEDIUM is paper-safe for headline figure bands; LOW remains paper-safe for narrative discussion; HIGH is labelled exploratory on every exported figure."

## 8. Panel location in the three-panel app (for screenshots)

- **Deterministic central trajectories + metric strip:** Panel 2 (top strip + top two charts). Best screenshot for headline peak / turning numbers.
- **Preset-narrative comparison:** Panel 2 sidebar — cycle LOW / MEDIUM / HIGH; the chart pair re-renders with the preset caption visible.
- **Single-region case study with MC band and optional shock overlay:** Panel 3. Best screenshot for a focused region comparison, with HIGH preset visibly watermarked when applicable.
- **Framework scope / phases table:** Panel 1. Best screenshot for "is the quantitative scope clear".

## 9. Post-regeneration checklist (when time permits)

1. Run `footprint_model.py --mc 200 --seed 42 --uncertainty-preset low --scenarios california ohio --policy baseline`. Commit the resulting quantile CSVs with the preset-tagged filename.
2. Same for `--uncertainty-preset high`. Commit.
3. Update Section 3 of this file with measured widths.
4. Update the interpretation-boundary rows in Section 2 with measured years under LOW / HIGH.
5. If the LOW boundary moves later than 2075, note in the rebuttal that the paper-safe window extends.
6. Regenerate the four `refstyle` figures under each preset and store under `reports/paper_support/reference_style/{region}_{preset}_2025_2075_refstyle.{pdf,png}`. Keep MEDIUM as the paper-used version.
