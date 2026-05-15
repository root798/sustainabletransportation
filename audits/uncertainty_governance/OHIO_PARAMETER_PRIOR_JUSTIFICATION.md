# OHIO_PARAMETER_PRIOR_JUSTIFICATION.md

**Date:** 2026-04-15
**Scope:** evidence behind the Ohio-specific overrides for L3 parameters and the Ohio scenario-file centre updates.
**Referenced files:**
- `scenarios/ohio/scenario.json` (growth_rates centres updated 2026-04-15)
- `configs/ui_parameter_presets/l3_2075_targets.json` (Ohio overrides in every level)
- `configs/ui_parameter_presets/l3_growth_exponents.json` (Ohio overrides in every level)
- `audits/step_04_uncertainty_architecture/CA_OH_L2_DESIGN.md` (dossier entry S2-04)

---

## 1. Problem the previous release left open

Dossier S2-04 documented that every Ohio L3 prior was a byte-identical copy of the California prior, differing only in the two initial Beta means. That meant Ohio's 2075 CAV target triangular (0.25, 0.45, 0.70), Ohio's `growth_rates.ev` N(0.07, 0.015), and Ohio's `growth_rates.clean_energy` N(0.05, 0.012) were CA-specific numbers applied to a region with very different 2024 conditions. The previous release acknowledged the defect but did not fix it.

This document records the final decision to apply Ohio-specific centres and widths to F23, F24, F25, F26, and F28; F27 remains unchanged because hardware efficiency doubling is a global technology parameter with no regional meaning.

## 2. Parameters addressed

| Parameter | Previous Ohio = California? | Final Ohio-specific |
|---|---|---|
| F23 `growth_rates.cav` (2075 CAV target) | yes | yes — centre 0.30, range 0.05–0.70 across levels |
| F24 `growth_rates.sti` (2075 STI coverage) | yes | yes — centre 0.30, range 0.05–0.75 |
| F25 `growth_rates.ev` (annual BEV growth) | yes | yes — centre 0.055, sd wider |
| F26 `growth_rates.clean_energy` | yes | yes — centre 0.035, sd wider |
| F27 `growth_rates.efficiency_doubling` | yes | no change — global technology |
| F28 `growth_rates.total_car_increase` | yes | yes — centre 0.001 |

## 3. Evidence

### F23 — 2075 CAV target fraction (Ohio 0.30 vs CA 0.45)

- California's SB 1298 (2012) and AB 1592 (2016) established a permissive AV regulatory environment; pilot mileage reached > 9 M miles/yr in state by 2023.
- Ohio does not yet have an equivalent statewide AV permit system; Drive Ohio and the Ohio Turnpike corridor pilots are focused on truck and Interstate-only use, and statewide AV pilot miles remain under 1 M/yr.
- Most industry forecasts that distinguish Ohio from California put 2075 CAV share for Ohio at roughly 60–70% of California's. A centre of 0.30 (vs CA 0.45) corresponds to that ratio.
- The triangular supports widen asymmetrically on the low side to acknowledge that Ohio's CAV share could remain well below its central 2075 mode.

### F24 — 2075 STI coverage (Ohio 0.30 vs CA 0.50)

- California's DOT has funded intersection modernization pilots in multiple metros; Caltrans 2024-2029 plan includes V2X upgrade on all Class-1 highways.
- Ohio's intersection modernization is concentrated in Drive Ohio pilots and along US 33 smart corridor; statewide rollout plans are less advanced.
- Centre shifted to 0.30 with wider uncertainty; wider low-side tail reflects the possibility of slower Ohio statewide rollout.

### F25 — Annual BEV-share growth exponent (Ohio 0.055 vs CA 0.07)

- DOE AFDC 2019–2024 BEV-registration compound annual growth rates: California ~45%, Ohio ~30%.
- Translating to annual-share exponent on the current share, Ohio's implied exponent is ~0.055, lower than CA's ~0.07.
- Widened sd (0.020 at MEDIUM, vs CA 0.015) reflects deeper scenario disagreement for Ohio — the state's BEV trajectory depends strongly on federal tax incentives that are more volatile than California's state-level mandates.

### F26 — Annual low-carbon-electricity growth exponent (Ohio 0.035 vs CA 0.05)

- EIA 2019–2024: Ohio low-carbon electricity share rose from ~22% to ~27% (~4% CAGR); California from ~55% to ~66% (~3.6% CAGR but from a higher base → implied exponent ~0.05 on the share growth).
- Ohio's RPS trajectory does not have the 100%-clean target California commits to in SB 100. Ohio-specific centre 0.035 reflects this.
- Widened sd (0.015 MEDIUM vs CA 0.012) reflects the larger policy uncertainty for Ohio's grid trajectory.

### F28 — Annual fleet-stock growth exponent (Ohio 0.001 vs CA 0.002)

- Census-based 2019–2024 annual light-duty registration growth: California ~0.2%, Ohio ~0.1%.
- Ohio's population growth is roughly half of California's.

### F27 — Hardware efficiency doubling (no regional change)

- Moore-style CAV-compute efficiency doubling is a global technology parameter; semiconductor industry roadmaps do not distinguish regions.
- Ohio and California face the same CAV hardware supply chain. No region-specific centre or width is applied.

## 4. Implementation

Each Ohio override is encoded inside the corresponding level spec in the parameter preset JSON:

```json
"low": {
  "dist": "triangular", "low": 0.35, "mode": 0.45, "high": 0.55, "semantic": "2075_target_fraction",
  "_regions": { "ohio": { "low": 0.20, "mode": 0.30, "high": 0.40 } }
}
```

The v4 `core.py` loader reads the base spec, checks `_regions.<current region>`, and merges the override over the base. If no override key is present, the California values are used by default.

The FIXED level for F23, F24, F25, F26, F28 reads `"region_mean"` — the loader substitutes the value from `scenarios/{region}/scenario.json:growth_rates.{field}`. The Ohio scenario file was updated to Ohio modes as part of this release:

```
growth_rates.cav: 0.45 -> 0.30
growth_rates.sti: 0.50 -> 0.30
growth_rates.ev: 0.07 -> 0.055
growth_rates.clean_energy: 0.05 -> 0.035
growth_rates.total_car_increase: 0.002 -> 0.001
```

An informational `_ohio_prior_note` key records the change in the scenario file itself.

## 5. Consequence for reported numbers

The Ohio deterministic 2030 ATS Emissions drops slightly under the new centres because Ohio's lower BEV and clean-electricity growth lead to a lower CAV fleet but also a slower fleet electrification; the two partially cancel. The regenerated default-bundle MC (see `BACKEND_MC_CORRECTNESS_FIX.md` §6) shows Ohio 2030 p50 at 0.75 × 10^9 kg CO2 — a small shift from the previous 0.75–0.80 × 10^9 range.

The Ohio interpretation boundary under the default bundle is `None` (never crossed within the horizon). Under paper-safe MEDIUM, the Ohio boundary is 2027. The shift is produced by (i) the Ohio-specific LOW priors and (ii) the dual-axis fix restoring correct L2 variance accounting.

## 6. What remains unresolved

- L1 parameters (F01, F02, F03, F04, F05) are Ohio-specific in `scenarios/ohio/scenario.json` (EIA / AFDC data) so no additional override is needed.
- L2 parameters (F06–F22) are load-model properties and are treated as region-independent; this is consistent with the literature.
- F27 efficiency doubling is global.
- The old historical results files (`results/ohio_results.csv` etc.) were produced with the Ohio-as-CA-clone centres and are retained only as historical artefacts.
