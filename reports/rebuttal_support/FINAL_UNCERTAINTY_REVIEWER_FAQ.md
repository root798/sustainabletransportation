# FINAL_UNCERTAINTY_REVIEWER_FAQ.md

**Date:** 2026-04-16
**Authoritative numbers:** 200-run MC, seed 42, regenerated 2026-04-16 under the final prior design.

---

### 1. Why are some parameters fixed by default?

Nine parameters are fixed because they satisfy at least one of three rules:
- **Absorbed downstream:** F01 (initial grid share) and F02 (initial BEV share) are 2024 measurements that the long-run growth exponents (F25, F26) subsume within 3–5 simulated years.
- **Structural duplicate:** F06–F08 (ECAV per-level scale factors) and F12–F14 (STI per-level) multiply on the same power cells as the per-subsystem axis (F09–F11, F15–F17), double-counting the same variance. Documented in dossier S2-01 / S2-02.
- **Effect vanishes:** F21 (cohort decay) affects only the pre-2024 cohort that retires by 2036 under the default service life.

Fixing these does not hide scientific uncertainty: the retained axis still carries hardware-variance draws, and the growth exponents still compound.

### 2. Why are F18/F19/F23/F24 treated as scenario assumptions rather than default residual uncertainty?

These four parameters define the scenario rather than represent residual measurement uncertainty. F23/F24 set the 2075 policy target for CAV/STI adoption; F18/F19 set the assumed distribution across automation levels. The user explicitly chooses a target on the slider; the MC band around it is conditional uncertainty about achieving that target, not uncertainty about whether the target itself is correct.

The page makes this explicit with an info banner: "These are scenario-defining assumptions. The uncertainty levels below represent conditional uncertainty around the chosen scenario."

### 3. Why is F04 region-specific?

California's fossil electricity fleet is gas-dominated (39% natural gas, negligible coal). Ohio's includes 34% coal. Coal emits 0.9–1.2 kg CO2/kWh; NGCC emits 0.35–0.45. Using the same triangular (0.35, 0.50, 0.65) for both regions would under-represent Ohio's higher carbon intensity and over-represent it for California. The fix:
- CA mode = 0.45, support = 0.38–0.55 (narrow, gas-dominated)
- OH mode = 0.62, support = 0.42–0.85 (broader, gas + coal)

Source: EIA State Electricity Profiles; NREL Life Cycle Greenhouse Gas Emissions from Electricity Generation Update (2021).

### 4. Why is F27 modeled as lognormal rather than the original triangular?

The hardware efficiency doubling time must be positive (you cannot halve computing energy in negative years). The previous triangular (1.5, 2.8, 5.0) could in principle be replaced by any positive-definite right-skewed distribution. Lognormal is the natural choice because:
- It is positive-definite by construction.
- It is right-skewed, reflecting that slow-down scenarios (longer doubling) are more plausible than impossibly-fast ones.
- Its two parameters (`mean` on original scale, `sigma`) are interpretable.

For MEDIUM (mean=2.8, sigma=0.30): median = 2.68 yr, mode = 2.45 yr, p05 = 1.63 yr, p95 = 4.39 yr — comparable to the old triangular range.

### 5. What parameter affects uncertainty most?

From the parameter-level contribution experiment (80-run isolated MC, California baseline):
1. **F27** (hardware efficiency doubling): top 2050 contributor (W/M = 1.02); top turning-year destabiliser (16-year spread).
2. **F23** (CAV 2075 target): top 2030 contributor (W/M = 0.56); second turning-year destabiliser.
3. **F18** (CAV level mix): top 2030 contributor (W/M = 0.55).

### 6. What layer affects uncertainty most?

- **L3 dominates overall** (2050 and 2075 bands driven by compounding growth exponents and target-fraction triangulars).
- **L2 dominates 2030** specifically (dual-axis scale factors + Dirichlet mixes).
- **L1 is the smallest layer** at every horizon.

### 7. Why is the default bundle more decision-meaningful after 2030?

The recommended default (9 fixed, 19 at LOW) produces:

| Region | W/M 2030 | W/M 2050 | IB year |
|---|---:|---:|---:|
| California | 0.83 | 0.88 | 2064 |
| Ohio | 0.82 | 0.80 | never |

The paper-safe bundle produces:

| Region | W/M 2030 | W/M 2050 | IB year |
|---|---:|---:|---:|
| California | 1.64 | 2.41 | 2028 |
| Ohio | 1.59 | 1.92 | 2029 |

Under the paper-safe bundle, the 2030 band exceeds 1.5 × p50 — the interpretation boundary fires immediately, and every point beyond 2028 is technically a scenario-conditioned envelope rather than a quantitative projection. Under the default, the 2030 band is ±40% around the central trajectory, the interpretation boundary is decades away, and a reader can meaningfully compare policy alternatives.

### 8. What limitations remain?

1. **F29 absolute power cells.** 18 per-level × per-subsystem ECAV/STI cells have no direct prior; all variance routes through the scale factors. A joint prior would require a model-structure redesign.
2. **Independence assumption.** All trajectory parameters (F23–F28) are sampled independently. Positive correlation is plausible and would narrow the tails; it is documented as a simplification, not implemented.
3. **Truncated-normal approximation.** F25, F26, F28 use normal + clamp rather than true rejection-based truncated normal. The approximation is negligible at the default LOW sigmas (<2% clamp rate).
4. **US Average quarantine.** The synthetic midpoint region is flagged exploratory.
5. **Aggressive / conservative policies.** Policy-conditional MC is exploratory per Methods M14.
