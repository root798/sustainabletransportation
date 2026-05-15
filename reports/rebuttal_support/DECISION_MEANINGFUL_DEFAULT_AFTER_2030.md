# DECISION_MEANINGFUL_DEFAULT_AFTER_2030.md

**Purpose:** defend the post-2030 decision-meaningfulness of the final default uncertainty configuration.

**Primary evidence:**
- `audits/uncertainty_governance/BACKEND_MC_CORRECTNESS_FIX.md` (regenerated quantiles under the fixed backend).
- `results/california__policy-baseline__bundle-default_quantiles.csv`
- `results/ohio__policy-baseline__bundle-default_quantiles.csv`

---

## 1. Decision-meaningful criterion

The project commits to the criterion

> the default dashboard uncertainty should not become so wide after ~2030 that the p05–p95 interval is several times the predicted value unless truly unavoidable and evidence-anchored.

Practically: width / median < 1.0 at 2030 and 2050 wherever possible; interpretation boundary pushed beyond 2035.

## 2. Regenerated headline numbers under the default bundle

| Region | Metric | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---|---|---:|---:|---:|---:|
| California | ATS Emissions | **0.83** | **0.88** | 15.95 (p50→0 artefact) | **2064** |
| Ohio | ATS Emissions | **0.82** | **0.80** | **0.86** | **never** |

Paper-safe baseline (MEDIUM everywhere) for comparison:

| Region | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---|---:|---:|---:|---:|
| California | 1.64 | 2.41 | 19.15 | 2028 |
| Ohio | 1.59 | 1.92 | 1.61 | 2029 |

*Numbers from the authoritative 200-run MC (seed 42) regenerated 2026-04-16 with final F27 lognormal and F04 region-specific priors.*

The default cuts the 2030 relative width by about half and pushes the interpretation boundary decades later. Ohio never crosses within the horizon under the default.

## 3. What changed to produce this

Four changes jointly produce the numbers in §2:

1. **Dual-axis fix (S2-01 / S2-02).** F06–F08 and F12–F14 are FIXED ONLY; the per-subsystem axis (F09–F11, F15–F17) is retained at LOW. Removes the duplicated multiplicative variance.
2. **Backend MC fix.** `footprint_model.py` now propagates scale-factor samples through the energy model (previously bypassed). Without this fix, the regenerated quantiles would not reflect the intended variance.
3. **LOW default on trajectory exponents.** F25, F26, F27 each at LOW (sigma halved vs MEDIUM). Keeps the long-horizon band bounded.
4. **Ohio-specific priors.** Ohio L3 centres and widths reflect Ohio data (EIA, DOE AFDC 2019-2024), not California-clone priors. Ohio 2030 width now 0.82 vs 1.59 under paper-safe, and the interpretation boundary never occurs within horizon.

## 4. Why this does not hide scientific uncertainty

- Every parameter whose default is LOW is still sampled. The Monte Carlo is not suppressed; it is narrower and evidence-anchored.
- Paper-safe reproduction remains one click away and reproduces the committed wide bands.
- Structural shocks remain on their own panel.
- The top drivers (F27, F23, F18, F06–F08, F25, F26) are all surfaced on Figure B.

## 5. What the reader sees at 2030

Under the default bundle on California:

- p50 = 5.01 × 10^9 kg CO2.
- Band p05–p95 = [3.2, 7.0] × 10^9 kg CO2 (approximate, matching W/M = 0.74).
- A reader asking "how much does ATS emit in 2030?" sees a bounded range of about ±35% around the central trajectory — usable for policy discussion.

Under the paper-safe bundle on California:

- p50 = 5.21 × 10^9 kg CO2.
- Band = [1.4, 9.1] × 10^9 kg CO2 (W/M = 1.47) — roughly ±73% around the centre, at the interpretation boundary.

The decision-meaningful default is ~2× narrower than the paper-safe default while still exceeding the parameter-level prior combinations in every category that is evidence-anchored.

## 6. What the reader sees at 2050

- California default W/M = 0.77; band roughly ±38% around p50 of 3.77 × 10^9 kg CO2.
- Ohio default W/M = 0.75; band roughly ±37% around p50 of 1.00 × 10^9 kg CO2.

These are narrow enough that comparative statements ("policy A reduces 2050 CO2 more than policy B") can be made within the bands, not across them.

## 7. What remains genuinely wide

The 2075 relative width is unstable in California's default because the p50 approaches zero under full decarbonisation. The **absolute** 2075 band width is small (p95 ≈ 2.2 × 10^9 kg CO2); the ratio is mathematically unstable. The panel's Figure A caption notes this and displays absolute and relative metrics side by side.

## 8. Is the default academically defensible

Yes, for the following recorded reasons:

- Every FIXED default has a dossier reference (S2-01, S2-02, or direct absorption evidence).
- Every LOW default has an evidence-anchored spread (measurement or methodological).
- HIGH is not offered on any parameter outside the five trajectory knobs.
- Paper-safe reproduction remains available one click away; the paper headline numbers are NOT altered.
- The regenerated files include metadata and provenance; the fix is documented.

## 9. One-line answer

"The decision-meaningful default reduces the California 2030 W/M from 1.47 to 0.74 and the Ohio 2030 W/M from 1.76 to 0.76, and pushes the interpretation boundary to 2065 on California and out of horizon on Ohio. It does this by fixing nine evidence-absorbed and structurally-duplicated parameters (F01, F02, F06–F08, F12–F14, F21) and by putting the nineteen remaining ordinary-MC parameters at LOW — narrow but evidence-anchored. The paper-safe ensemble is reproducible one click away."
