# State Diagnostics — California / Ohio / U.S. Average

## Diagnostic Summary

All three regions load from **separate config files** with genuinely different parameters.
There is no cross-contamination or silent default substitution.

## Key Year Comparison (baseline policy, deterministic)

### California
| Year | Annual energy | Annual emissions | Cumul. emissions | Grid EF | Clean share | BEV share | CAV | STI |
|------|--------------|-----------------|-----------------|---------|-------------|-----------|-----|-----|
| 2024 | 3.69e+06 kWh | 5.95e+06 kg | 5.95e+06 kg | 0.172 | 65.6% | 4.1% | 1,603 | 0 |
| 2025 | 5.46e+08 kWh | 5.66e+08 kg | 5.72e+08 kg | 0.156 | 68.9% | 4.4% | 29,918 | 3,729 |
| 2030 | 4.05e+09 kWh | 5.26e+09 kg | 1.68e+10 kg | 0.060 | 87.9% | 6.2% | 594,256 | 22,188 |
| 2045 | 4.34e+09 kWh | 4.81e+09 kg | 1.12e+11 kg | 0.030 | 100% | 17.0% | 6,619,862 | 77,434 |
| 2075 | 4.24e+09 kWh | 1.27e+08 kg | 2.00e+11 kg | 0.030 | 100% | 100% | 39,537,291 | 186,847 |
| 2092 | 4.72e+09 kWh | 1.42e+08 kg | 2.02e+11 kg | 0.030 | 100% | 100% | 42,875,560 | 190,200 |
| **Peak** | — | 7.51e+09 kg | — | — | — | — | — | — |
| **Peak year** | — | **2036** | — | — | — | — | — | — |

### Ohio
| Year | Annual energy | Annual emissions | Cumul. emissions | Grid EF | Clean share | BEV share | CAV | STI |
|------|--------------|-----------------|-----------------|---------|-------------|-----------|-----|-----|
| 2024 | 7.18e+05 kWh | 1.18e+06 kg | 1.18e+06 kg | 0.384 | 24.7% | 0.7% | 400 | 0 |
| 2025 | 1.35e+08 kWh | 1.34e+08 kg | 1.35e+08 kg | 0.371 | 25.9% | 0.7% | 8,252 | 1,676 |
| 2030 | 9.21e+08 kWh | 1.19e+09 kg | 3.44e+09 kg | 0.334 | 33.1% | 1.0% | 164,817 | 9,974 |
| 2045 | 1.25e+09 kWh | 1.53e+09 kg | 2.48e+10 kg | 0.156 | 68.8% | 2.8% | 1,836,646 | 34,808 |
| 2075 | 1.96e+09 kWh | 2.20e+09 kg | 8.90e+10 kg | 0.030 | 100% | 21.1% | 10,969,908 | 83,993 |
| 2092 | 1.87e+09 kWh | 1.11e+09 kg | 1.15e+11 kg | 0.030 | 100% | 66.5% | 11,896,291 | 85,500 |
| **Peak** | — | 2.34e+09 kg | — | — | — | — | — | — |
| **Peak year** | — | **2076** | — | — | — | — | — | — |

### U.S. Average
| Year | Annual energy | Annual emissions | Cumul. emissions | Grid EF | Clean share | BEV share | CAV | STI |
|------|--------------|-----------------|-----------------|---------|-------------|-----------|-----|-----|
| 2024 | 5.54e+06 kWh | 8.98e+06 kg | 8.98e+06 kg | 0.274 | 45.2% | 3.4% | 1,002 | 0 |
| 2025 | 1.24e+08 kWh | 1.89e+08 kg | 1.98e+08 kg | 0.263 | 47.4% | 3.6% | 10,913 | 162 |
| 2030 | 1.65e+09 kWh | 2.59e+09 kg | 6.85e+09 kg | 0.197 | 60.5% | 5.0% | 207,942 | 973 |
| 2045 | 7.46e+09 kWh | 1.11e+10 kg | 1.11e+11 kg | 0.030 | 100% | 13.9% | 2,347,866 | 3,404 |
| 2075 | 1.40e+10 kWh | 4.19e+08 kg | 4.69e+11 kg | 0.030 | 100% | 100% | 14,596,767 | 8,266 |
| 2092 | 1.67e+10 kWh | 5.01e+08 kg | 4.76e+11 kg | 0.030 | 100% | 100% | 25,160,148 | 8,271 |
| **Peak** | — | 1.31e+10 kg | — | — | — | — | — | — |
| **Peak year** | — | **2059** | — | — | — | — | — | — |

## Why Regions Differ — Real vs. Artifacts

### Real differences (correctly reflecting distinct configs):
1. **Vehicle stock**: CA 37.4M vs OH 10.4M vs US 23.9M → scales all absolute outputs
2. **Grid cleanliness**: CA 65.6% vs OH 24.7% vs US 45.2% → dramatically affects emissions
3. **BEV adoption start**: CA 4.1% vs OH 0.7% → Ohio is far behind on electrification
4. **Consumption rates**: US Average has ~10x higher per-unit sensing/communication kWh → US energy demand higher per CAV
5. **Growth rates**: US has lower CAV target (0.24 vs 0.45) and much lower STI target (0.03 vs 0.50)
6. **Peak year timing**: CA 2036 → OH 2076 → US 2059 — driven by grid decarbonisation speed and initial conditions

### Not artifacts:
- CA and OH have identical growth rates for cav/sti/ev/clean_energy/efficiency_doubling — this is intentional (same national technology trajectory, different starting points)
- US Average is a synthetic midpoint, not an official national average — correctly documented
- No quantile cross-substitution occurs
- No normalization artifacts in plotting (each region uses its own absolute values)

### Noteworthy observation:
Ohio's peak year (2076) is 40 years later than California's (2036).  This is because Ohio starts with 24.7% clean electricity vs California's 65.6%, so Ohio's grid-emission factor stays high much longer, causing emissions to keep rising as CAV fleet grows.  This is a genuine and scientifically meaningful difference.
