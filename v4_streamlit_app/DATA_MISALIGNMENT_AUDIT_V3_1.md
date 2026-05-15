# Data / Result Misalignment Audit — v4

## A. Region Loading Audit

### California (baseline)
| Parameter | Value | Unit |
|-----------|-------|------|
| total_cars | 37,428,700 | count |
| total_intersections | 380,400 | count |
| total_cav | 1,603 | count |
| total_sti | 0 | count |
| initial EV share | 0.040982 | fraction |
| initial f_clean | 0.656 | fraction |
| ev growth | 0.07 | fraction/yr |
| clean_energy growth | 0.05 | fraction/yr |
| cav target | 0.45 | fraction by 2075 |
| sti target | 0.50 | fraction by 2075 |
| efficiency_doubling | 2.8 | years |
| retire_year | 12 | years |
| e_clean | 0.03 | kg CO2/kWh |
| e_fossil | 0.50 | kg CO2/kWh |
| e_gasoline | 1.65 | kg CO2/kWh-eq |

### Ohio (baseline)
| Parameter | Value | Unit |
|-----------|-------|------|
| total_cars | 10,385,000 | count |
| total_intersections | 171,000 | count |
| total_cav | 400 | count |
| total_sti | 0 | count |
| initial EV share | 0.006683 | fraction |
| initial f_clean | 0.247 | fraction |
| ev growth | 0.07 | fraction/yr |
| clean_energy growth | 0.05 | fraction/yr |
| cav target | 0.45 | fraction by 2075 |
| sti target | 0.50 | fraction by 2075 |
| efficiency_doubling | 2.8 | years |
| retire_year | 12 | years |
| e_clean | 0.03 | kg CO2/kWh |
| e_fossil | 0.50 | kg CO2/kWh |
| e_gasoline | 1.65 | kg CO2/kWh-eq |

### U.S. Average (baseline)
| Parameter | Value | Unit |
|-----------|-------|------|
| total_cars | 23,906,850 | count |
| total_intersections | 275,700 | count |
| total_cav | 1,002 | count |
| total_sti | 0 | count |
| initial EV share | 0.033532 | fraction |
| initial f_clean | 0.4515 | fraction |
| ev growth | 0.07 | fraction/yr |
| clean_energy growth | 0.05 | fraction/yr |
| cav target | 0.24 | fraction by 2075 |
| sti target | 0.03 | fraction by 2075 |
| efficiency_doubling | 3.8 | years |
| retire_year | 12 | years |
| e_clean | 0.03 | kg CO2/kWh |
| e_fossil | 0.50 | kg CO2/kWh |
| e_gasoline | 1.65 | kg CO2/kWh-eq |

**Key inter-region differences (confirmed):**
- Vehicle stock: CA 37.4M >> US 23.9M >> OH 10.4M
- EV share: CA 4.1% >> US 3.4% >> OH 0.7%
- f_clean: CA 65.6% >> US 45.2% >> OH 24.7%
- CAV target: CA=OH 0.45 vs US 0.24
- STI target: CA=OH 0.50 vs US 0.03
- Efficiency doubling: CA=OH 2.8yr vs US 3.8yr
- Fleet growth: CA=OH 0.2% vs US 0.4%
- Consumption rates: US Average has ~10x higher sensing/communication per-unit kWh than CA/OH (reflects different infrastructure assumptions in the synthetic midpoint)

## B. Quantile Alignment Audit

| Region | Policy | Quantile file exists | Band non-zero | MC runs | Correctly aligned |
|--------|--------|---------------------|---------------|---------|-------------------|
| California | baseline | Yes | Yes | 200 | Yes — generated from california.json config |
| California | aggressive | No | — | — | N/A — no MC for non-baseline |
| California | conservative | No | — | — | N/A |
| Ohio | baseline | Yes | Yes | 200 | Yes — generated from ohio.json config |
| Ohio | aggressive | No | — | — | N/A |
| Ohio | conservative | No | — | — | N/A |
| US Average | baseline | Yes | Yes | 200 | Yes — generated from us_average.json config |
| US Average | aggressive | No | — | — | N/A |
| US Average | conservative | No | — | — | N/A |

**No hidden fallback**: v4 only loads quantiles from `results/{region}__policy-{policy}__model-fixed_table_quantiles.csv`.  No California or national default is substituted for missing files.  Dashboard explicitly states when uncertainty is unavailable.

## C. Metric Definition Audit

| Metric | Formula | Unit | Annual/Cumulative | Direct/Derived | Issues |
|--------|---------|------|-------------------|----------------|--------|
| ATS Total Power (kWh) | Σ(e+i+s power components) | kWh/yr | Annual | Direct | Column name says "Power" but is annual energy; display labels corrected |
| ATS Emissions (kg CO2) | e_em + i_em + s_em | kg CO2/yr | Annual | Direct | None |
| Cumulative emissions | Σ ATS_Emissions over [2024, year] | kg CO2 | Cumulative | Derived | v4 clarifies this is a running sum, not discounted |
| Peak year | argmax(ATS_Emissions) | year | Scalar | Derived | None |
| Turning year | First post-peak year where em ≤ 0.5 × peak | year | Scalar | Derived | None |
| EV Fraction | n_ev / total_cars | fraction | Annual | Direct | None |
| Clean Energy Fraction | f_clean × (1+growth)^t, capped at 1 | fraction | Annual | Direct | None |
| Interpretation boundary | First year ≥ 2027 where (p95-p05)/p50 ≥ 1.5 | year | Scalar | Derived | None |

## D. Semantic Audit

### Fixed in v4:
1. **"Power" → "Energy"**: all display labels now say "energy demand (kWh/yr)" instead of "power (kWh)"
2. **"forecast" → "projection"**: no chart or metric uses the word "forecast".  v4 uses "scenario-conditioned projection" and "modeled"
3. **Annual vs cumulative**: cumulative metrics always labeled with "(running sum from 2024)" or "(full horizon)"
4. **State comparison overstatement**: removed.  Cross-region diagnostics panel explains exactly which parameters differ and why
5. **Lifecycle overstatement**: Framework Scope page clearly marks Production/Logistics/End-of-life as "conceptual only — not quantitatively implemented"
