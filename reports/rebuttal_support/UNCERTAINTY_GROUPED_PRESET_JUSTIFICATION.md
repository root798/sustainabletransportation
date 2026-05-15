# UNCERTAINTY_GROUPED_PRESET_JUSTIFICATION.md

**Purpose:** support a reviewer question "why not a single low/medium/high slider for the whole model?"
**Primary source:** `audits/uncertainty_governance/GROUPED_PRESET_DESIGN.md`

---

## 1. The single-slider failure mode

A global LOW/MEDIUM/HIGH selector lumps three physically distinct sources of uncertainty onto one knob. That conflates:

- **L1** — measurement uncertainty on baseline data and emission factors, bounded by external evidence.
- **L2** — load-model per-device uncertainty, bounded by hardware measurement literature with known duplication issues (S2-01/S2-02).
- **L3** — long-horizon trajectory uncertainty, bounded only by policy-scenario imagination.

A single slider cannot express any of the following reasonable requests:

1. "Show me the band you can defend from evidence only" — requires narrowing L3 but keeping L1 and L2 at evidence-anchored medium.
2. "Fix the 2024 baseline so I can compare trajectories" — requires fixing L1 while keeping L2 and L3 free.
3. "Remove the known duplication in L2 but keep the paper-safe L3" — requires `L2=low, L3=medium`.
4. "Explore the full what-if envelope on trajectory only" — requires `L3=high, L1/L2=fixed or low`.

None of these can be expressed with a single LOW/MEDIUM/HIGH setting.

## 2. What grouped presets give the reader

The grouped scheme (per-layer LOW/MEDIUM/HIGH plus FIXED) exposes the three layers as independent control axes. The reader can:

- See which layer each preset applies to.
- See which factors each layer-preset fixes vs leaves free.
- Quantify how much each layer contributes to the band, directly from the Uncertainty Panel's contribution figure.
- Select a narrowed default (decision-meaningful) or a wide paper-safe reproduction with one click each.

The three advertised bundles on the panel correspond to distinct reader goals:

| Bundle | Goal | Composition |
|---|---|---|
| Decision-meaningful (default) | Read the 2030 band as a quantitative projection | `L1=fixed, L2=low, L3=low` |
| Paper-safe reproduction | Reproduce committed MC CSVs | `L1=medium, L2=medium, L3=medium` |
| Exploratory long-horizon | Interrogate 2050+ what-if envelopes | `L1=fixed, L2=medium, L3=high` |

## 3. Evidence that layer-specific control matters

From `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv` (California, baseline policy, 150 MC runs each):

- **L1-only 2030 relative width = 0.17** (Ohio: 0.15). Cheap to fix; reader-interpretability gain.
- **L2-only 2030 relative width = 1.27** (Ohio: 1.10). Dominated by S2-01/S2-02 dual-axis duplication. Can be narrowed ~45% by `l2_low`.
- **L3-only 2050 relative width = 1.46** (Ohio: 0.98). Dominated by compounding growth exponents. Can be narrowed ~60% by `l3_low`.

A single global slider cannot make these surgical cuts: widening L1 to LOW would narrow the dual-axis duplication that does not benefit from L1 narrowing; narrowing L3 to LOW would also narrow L1 (and hide the operational vs life-cycle `e_clean` spread the reader should see).

## 4. Academic defensibility per preset

Each layer preset is separately defensible (see the JSON `notes` field and the preset-design doc):

- **L1_fixed:** "Hold 2024 baseline conditions constant across runs so the band reflects trajectory divergence, not starting-condition noise." Paper-safe.
- **L1_low:** "Tightened Beta concentrations (κ ×2) and operational-only emission triangulars. Measurement-grade width." Paper-safe.
- **L1_medium:** "Paper-safe baseline, reproduces Methods M2." Paper-safe.
- **L2_fixed:** "Remove all load-model variance to isolate trajectory divergence." Paper-safe.
- **L2_low:** "Eliminate the known dual-axis duplication (S2-01/S2-02); retain per-subsystem and level-mix axes." Paper-safe.
- **L2_medium:** "Reproduce paper-safe baseline; retains dual-axis with disclosure." Paper-safe.
- **L2_high:** "Widen sigmas 30%; exploratory." Not paper-safe.
- **L3_fixed:** "Hold trajectory constant; diagnostic for isolating L1/L2 contribution." Paper-safe.
- **L3_low:** "Sigma halved on growth-rate exponents, CAV/STI triangular pulled to mode; narrower but still scenario-meaningful." Paper-safe.
- **L3_medium:** "Paper-safe baseline." Paper-safe.
- **L3_high:** "Sigma ×1.5, widened CAV/STI support; exploratory long-horizon." Not paper-safe.

No preset is "looser than evidence"; `l1_high` is deliberately absent because L1 priors are evidence-anchored and widening them would be non-scientific.

## 5. What happens to the old global preset

The legacy `configs/ui_presets/uncertainty_{low,medium,high}.json` files are retained. The v4 Uncertainty Panel maps them onto grouped-preset bundles:

- global LOW → `L1=low, L2=low, L3=low`
- global MEDIUM → `L1=medium, L2=medium, L3=medium`
- global HIGH → `L1=medium, L2=high, L3=high` (L1 capped at MEDIUM because `l1_high` is intentionally undefined)

This preserves backward compatibility; the new default mechanism is the grouped panel.

## 6. Bottom line for a reviewer

"We moved from a single global slider to per-layer grouped presets because the three uncertainty layers have physically different characters — evidence-anchored baseline, hardware measurement variance with a known duplication defect, and compounding trajectory assumptions — and a single slider cannot express decisions such as 'remove the duplication but keep paper-safe trajectory' or 'fix 2024 baseline to see pure trajectory divergence'. The paper-safe MEDIUM bundle remains available one click away and reproduces the committed Monte Carlo CSVs verbatim."
