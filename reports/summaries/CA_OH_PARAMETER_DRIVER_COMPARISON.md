# CA_OH_PARAMETER_DRIVER_COMPARISON.md

**Date:** 2026-04-17
**Source:** `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv` (144 rows: 24 params × 3 years × 2 regions, 80 MC runs each, seed 42).

---

## Top-5 band-width drivers by region and year

### At 2030

| Rank | California (W/M) | Ohio (W/M) |
|---:|---|---|
| 1 | F23 CAV target (0.56) | F23 CAV target (0.54) |
| 2 | F27 efficiency doubling (0.56) | F27 efficiency doubling (0.53) |
| 3 | F18 cav_levels Dirichlet (0.55) | F18 cav_levels Dirichlet (0.52) |
| 4 | F10 ECAV computing scale (0.44) | F10 ECAV computing scale (0.40) |
| 5 | F22 retire_year (0.40) | F22 retire_year (0.38) |

**Structural pattern:** F23, F27, F18, F10, F22 dominate at 2030 in both regions. The ranking is identical; magnitudes are slightly lower for Ohio because the Ohio fleet is smaller.

### At 2050

| Rank | California (W/M) | Ohio (W/M) |
|---:|---|---|
| 1 | **F27** efficiency doubling (**1.03**) | **F27** efficiency doubling (**0.68**) |
| 2 | F23 CAV target (0.56) | F23 CAV target (0.55) |
| 3 | F18 cav_levels Dirichlet (0.51) | F18 cav_levels Dirichlet (0.51) |
| 4 | F02 initial BEV share (0.44) | F09 ECAV sensing scale (0.51) |
| 5 | F09 ECAV sensing scale (0.43) | F06–F08 ECAV per-level axis (0.33) |

**Key difference at 2050:** F27 has a much larger absolute W/M in California (1.03) than Ohio (0.68), because the California fleet's higher BEV penetration in 2050 amplifies the ECAV computing decay channel. F02 (initial BEV share) is more impactful in California (0.44 vs not-top-5 for Ohio) because CA starts from 4.1% vs OH's 0.7%.

### At 2075

| Rank | California (W/M) | Ohio (W/M) |
|---:|---|---|
| 1 | **F27** efficiency doubling (**1.06**) | **F27** efficiency doubling (**0.99**) |
| 2 | F23 CAV target (0.55) | F23 CAV target (0.66) |
| 3 | F18 cav_levels Dirichlet (0.43) | F18 cav_levels Dirichlet (0.50) |
| 4 | F02 initial BEV share (0.40) | F09 ECAV sensing scale (0.39) |
| 5 | F09 ECAV sensing scale (0.36) | F24 STI target (0.36) |

**By 2075:** F27 dominates in both regions. Ohio's F23 (CAV target) has a larger W/M (0.66) than California's (0.55) — the Ohio fleet is still mid-transition at 2075 so the target-fraction prior has more leverage.

## Regional summary

| Feature | California | Ohio |
|---|---|---|
| Dominant 2050 driver | F27 (W/M 1.03) | F27 (W/M 0.68) |
| Dominant 2030 driver | F23 (W/M 0.56) | F23 (W/M 0.54) |
| Largest structural difference | F02 (initial BEV share) ranks 4th at 2050 | F09 (ECAV sensing scale) ranks 4th at 2050 |
| Turning-year destabiliser | F27 (spread between p05/p95 turning years) | F27 (Ohio turning year is "not reached" under many draws) |
| Key regional driver | BEV share matters more (CA starts at 4.1%) | Fossil grid intensity matters more (OH coal-heavy) |

## Policy interpretation

1. **Hardware-efficiency progress** (F27) is the single highest-leverage factor controlling ATS-emissions uncertainty across the entire horizon for both states. R&D investment and semiconductor technology policy are the primary uncertainty-reduction levers.
2. **CAV deployment ambition** (F23) is the second-highest lever — fleet-transition mandates and deployment timelines have a direct, material effect on the ATS emissions band.
3. **Autonomy-level mix composition** (F18, cav_levels Dirichlet) ranks consistently in the top 3, meaning the split between L3/L4/L5 autonomy (which determines how much compute each CAV burns) is a key design assumption. This can be influenced by regulatory standards on autonomy-level requirements.
4. **State-to-state parity** holds: the driver ranking is structurally similar across California and Ohio. The absolute magnitudes differ because of fleet-size and grid-mix differences, but the same policy levers (efficiency investment, CAV deployment policy, autonomy-level regulation) dominate in both states.
