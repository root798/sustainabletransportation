# Figure 6 (Sankey) — extracted values, v9 dashboard baseline

_Scenario source: v9 dashboard default (policy=baseline, weather=Auto p_state)_

**Pipeline.** For each (region, year) the v9 dashboard's `load_runtime_config(region, 'baseline')` is loaded, then `attach_weather_region(cfg, region)` is applied (Auto p_state weather, the same default the Scenario Explorer ships with), then `run_simulation(cfg, years=68)` is called to produce the full 2024-2092 deterministic trajectory. The requested year is sliced out of the resulting DataFrame.

**Scope reminder.** Values are utility-phase only. Production / logistics / end-of-life are reported on the One-Time Energy page and are not included here. ATS-side gasoline energy refers to the sensing/computing/communication overhead of ICE-powered CAVs (ICECAV), not to vehicle propulsion fuel.

## California — 2045

_Source: v9 dashboard default (policy=baseline, weather=Auto p_state)_

### A. Top layer — total ATS utility-phase energy

| Quantity | Value | Unit |
|---|---:|---|
| Total ATS energy | 6.0462 | TWh |
| Electricity-based ATS energy | 2.1187 | TWh |
| Gasoline-based ATS energy | 3.9275 | TWh |
| Electricity share | 35.04% | of total energy |
| Gasoline share    | 64.96% | of total energy |

### B. Energy by ATS category (electricity branch)

| Quantity | Value | Unit |
|---|---:|---|
| ECAV (electricity) | 0.5017 | TWh |
| STI  (electricity) | 1.6170 | TWh |
| ECAV share of electricity | 23.68% | |
| STI  share of electricity | 76.32% | |

### C. Energy by ATS category (gasoline branch)

| Quantity | Value | Unit |
|---|---:|---|
| ICECAV (gasoline) | 3.9275 | TWh |
| ICECAV share of gasoline branch | 100.00% | |

### D. Electricity source mix

| Quantity | Value | Unit |
|---|---:|---|
| Low-carbon grid share | 100.00% | of electricity |
| Fossil grid share     | 0.00% | of electricity |
| Low-carbon electricity to ATS | 2.1187 | TWh |
| Fossil electricity to ATS     | 0.0000 | TWh |

### E. Fuel source mix (gasoline branch)

| Quantity | Value | Unit |
|---|---:|---|
| Gasoline share of gasoline branch | 100.00% | |

### F. Bottom layer — total ATS CO₂ emissions

| Quantity | Value | Unit |
|---|---:|---|
| Total ATS CO₂ | 6,544.0 | kt CO₂ |
| Electricity-based CO₂ | 63.6 | kt CO₂ |
| Gasoline-based CO₂    | 6,480.4 | kt CO₂ |
| ECAV electricity CO₂  | 15.0 | kt CO₂ |
| STI electricity CO₂   | 48.5 | kt CO₂ |
| ICECAV gasoline CO₂   | 6,480.4 | kt CO₂ |
| Electricity share of total CO₂ | 0.97% | |
| Gasoline share of total CO₂    | 99.03% | |
| ECAV share of electricity CO₂  | 23.68% | |
| STI  share of electricity CO₂  | 76.32% | |
| ICECAV share of gasoline CO₂   | 100.00% | |

### G. Emission intensity

| Quantity | Value | Unit |
|---|---:|---|
| Total CO₂ intensity       | 1,082.32 | kt CO₂ / TWh |
| Electricity CO₂ intensity | 30.00 | kt CO₂ / TWh |
| Gasoline CO₂ intensity    | 1,650.00 | kt CO₂ / TWh |

### H. Consistency residuals

| Check | Absolute residual | Relative |
|---|---:|---:|
| electricity + gasoline = total energy   | 0.000e+00 kWh | 0.00e+00 |
| ECAV + STI = electricity                | 0.000e+00 kWh | 0.00e+00 |
| ICECAV = gasoline-objective             | 0.000e+00 kWh | 0.00e+00 |
| electricity CO₂ + gasoline CO₂ = total CO₂ | 0.000e+00 kg | 0.00e+00 |
| ECAV CO₂ + STI CO₂ = electricity CO₂    | 0.000e+00 kg | 0.00e+00 |

## California — 2075

_Source: v9 dashboard default (policy=baseline, weather=Auto p_state)_

### A. Top layer — total ATS utility-phase energy

| Quantity | Value | Unit |
|---|---:|---|
| Total ATS energy | 4.7799 | TWh |
| Electricity-based ATS energy | 4.7799 | TWh |
| Gasoline-based ATS energy | 0.0000 | TWh |
| Electricity share | 100.00% | of total energy |
| Gasoline share    | 0.00% | of total energy |

### B. Energy by ATS category (electricity branch)

| Quantity | Value | Unit |
|---|---:|---|
| ECAV (electricity) | 2.9712 | TWh |
| STI  (electricity) | 1.8086 | TWh |
| ECAV share of electricity | 62.16% | |
| STI  share of electricity | 37.84% | |

### C. Energy by ATS category (gasoline branch)

| Quantity | Value | Unit |
|---|---:|---|
| ICECAV (gasoline) | 0.0000 | TWh |
| ICECAV share of gasoline branch | 0.00% | |

### D. Electricity source mix

| Quantity | Value | Unit |
|---|---:|---|
| Low-carbon grid share | 100.00% | of electricity |
| Fossil grid share     | 0.00% | of electricity |
| Low-carbon electricity to ATS | 4.7799 | TWh |
| Fossil electricity to ATS     | 0.0000 | TWh |

### E. Fuel source mix (gasoline branch)

| Quantity | Value | Unit |
|---|---:|---|
| Gasoline share of gasoline branch | 0.00% | |

### F. Bottom layer — total ATS CO₂ emissions

| Quantity | Value | Unit |
|---|---:|---|
| Total ATS CO₂ | 143.4 | kt CO₂ |
| Electricity-based CO₂ | 143.4 | kt CO₂ |
| Gasoline-based CO₂    | 0.0 | kt CO₂ |
| ECAV electricity CO₂  | 89.1 | kt CO₂ |
| STI electricity CO₂   | 54.3 | kt CO₂ |
| ICECAV gasoline CO₂   | 0.0 | kt CO₂ |
| Electricity share of total CO₂ | 100.00% | |
| Gasoline share of total CO₂    | 0.00% | |
| ECAV share of electricity CO₂  | 62.16% | |
| STI  share of electricity CO₂  | 37.84% | |
| ICECAV share of gasoline CO₂   | 0.00% | |

### G. Emission intensity

| Quantity | Value | Unit |
|---|---:|---|
| Total CO₂ intensity       | 30.00 | kt CO₂ / TWh |
| Electricity CO₂ intensity | 30.00 | kt CO₂ / TWh |
| Gasoline CO₂ intensity    | 0.00 | kt CO₂ / TWh |

### H. Consistency residuals

| Check | Absolute residual | Relative |
|---|---:|---:|
| electricity + gasoline = total energy   | 0.000e+00 kWh | 0.00e+00 |
| ECAV + STI = electricity                | 0.000e+00 kWh | 0.00e+00 |
| ICECAV = gasoline-objective             | 0.000e+00 kWh | 0.00e+00 |
| electricity CO₂ + gasoline CO₂ = total CO₂ | 0.000e+00 kg | 0.00e+00 |
| ECAV CO₂ + STI CO₂ = electricity CO₂    | 0.000e+00 kg | 0.00e+00 |

## Ohio — 2045

_Source: v9 dashboard default (policy=baseline, weather=Auto p_state)_

### A. Top layer — total ATS utility-phase energy

| Quantity | Value | Unit |
|---|---:|---|
| Total ATS energy | 1.0623 | TWh |
| Electricity-based ATS energy | 0.3202 | TWh |
| Gasoline-based ATS energy | 0.7421 | TWh |
| Electricity share | 30.14% | of total energy |
| Gasoline share    | 69.86% | of total energy |

### B. Energy by ATS category (electricity branch)

| Quantity | Value | Unit |
|---|---:|---|
| ECAV (electricity) | 0.0097 | TWh |
| STI  (electricity) | 0.3105 | TWh |
| ECAV share of electricity | 3.04% | |
| STI  share of electricity | 96.96% | |

### C. Energy by ATS category (gasoline branch)

| Quantity | Value | Unit |
|---|---:|---|
| ICECAV (gasoline) | 0.7421 | TWh |
| ICECAV share of gasoline branch | 100.00% | |

### D. Electricity source mix

| Quantity | Value | Unit |
|---|---:|---|
| Low-carbon grid share | 50.87% | of electricity |
| Fossil grid share     | 49.13% | of electricity |
| Low-carbon electricity to ATS | 0.1629 | TWh |
| Fossil electricity to ATS     | 0.1573 | TWh |

### E. Fuel source mix (gasoline branch)

| Quantity | Value | Unit |
|---|---:|---|
| Gasoline share of gasoline branch | 100.00% | |

### F. Bottom layer — total ATS CO₂ emissions

| Quantity | Value | Unit |
|---|---:|---|
| Total ATS CO₂ | 1,308.0 | kt CO₂ |
| Electricity-based CO₂ | 83.6 | kt CO₂ |
| Gasoline-based CO₂    | 1,224.4 | kt CO₂ |
| ECAV electricity CO₂  | 2.5 | kt CO₂ |
| STI electricity CO₂   | 81.0 | kt CO₂ |
| ICECAV gasoline CO₂   | 1,224.4 | kt CO₂ |
| Electricity share of total CO₂ | 6.39% | |
| Gasoline share of total CO₂    | 93.61% | |
| ECAV share of electricity CO₂  | 3.04% | |
| STI  share of electricity CO₂  | 96.96% | |
| ICECAV share of gasoline CO₂   | 100.00% | |

### G. Emission intensity

| Quantity | Value | Unit |
|---|---:|---|
| Total CO₂ intensity       | 1,231.28 | kt CO₂ / TWh |
| Electricity CO₂ intensity | 260.92 | kt CO₂ / TWh |
| Gasoline CO₂ intensity    | 1,650.00 | kt CO₂ / TWh |

### H. Consistency residuals

| Check | Absolute residual | Relative |
|---|---:|---:|
| electricity + gasoline = total energy   | 0.000e+00 kWh | 0.00e+00 |
| ECAV + STI = electricity                | 0.000e+00 kWh | 0.00e+00 |
| ICECAV = gasoline-objective             | 0.000e+00 kWh | 0.00e+00 |
| electricity CO₂ + gasoline CO₂ = total CO₂ | -2.384e-07 kg | -1.82e-16 |
| ECAV CO₂ + STI CO₂ = electricity CO₂    | 0.000e+00 kg | 0.00e+00 |

## Ohio — 2075

_Source: v9 dashboard default (policy=baseline, weather=Auto p_state)_

### A. Top layer — total ATS utility-phase energy

| Quantity | Value | Unit |
|---|---:|---|
| Total ATS energy | 1.3712 | TWh |
| Electricity-based ATS energy | 0.4207 | TWh |
| Gasoline-based ATS energy | 0.9505 | TWh |
| Electricity share | 30.68% | of total energy |
| Gasoline share    | 69.32% | of total energy |

### B. Energy by ATS category (electricity branch)

| Quantity | Value | Unit |
|---|---:|---|
| ECAV (electricity) | 0.0679 | TWh |
| STI  (electricity) | 0.3528 | TWh |
| ECAV share of electricity | 16.13% | |
| STI  share of electricity | 83.87% | |

### C. Energy by ATS category (gasoline branch)

| Quantity | Value | Unit |
|---|---:|---|
| ICECAV (gasoline) | 0.9505 | TWh |
| ICECAV share of gasoline branch | 100.00% | |

### D. Electricity source mix

| Quantity | Value | Unit |
|---|---:|---|
| Low-carbon grid share | 100.00% | of electricity |
| Fossil grid share     | 0.00% | of electricity |
| Low-carbon electricity to ATS | 0.4207 | TWh |
| Fossil electricity to ATS     | 0.0000 | TWh |

### E. Fuel source mix (gasoline branch)

| Quantity | Value | Unit |
|---|---:|---|
| Gasoline share of gasoline branch | 100.00% | |

### F. Bottom layer — total ATS CO₂ emissions

| Quantity | Value | Unit |
|---|---:|---|
| Total ATS CO₂ | 1,581.0 | kt CO₂ |
| Electricity-based CO₂ | 12.6 | kt CO₂ |
| Gasoline-based CO₂    | 1,568.4 | kt CO₂ |
| ECAV electricity CO₂  | 2.0 | kt CO₂ |
| STI electricity CO₂   | 10.6 | kt CO₂ |
| ICECAV gasoline CO₂   | 1,568.4 | kt CO₂ |
| Electricity share of total CO₂ | 0.80% | |
| Gasoline share of total CO₂    | 99.20% | |
| ECAV share of electricity CO₂  | 16.13% | |
| STI  share of electricity CO₂  | 83.87% | |
| ICECAV share of gasoline CO₂   | 100.00% | |

### G. Emission intensity

| Quantity | Value | Unit |
|---|---:|---|
| Total CO₂ intensity       | 1,152.99 | kt CO₂ / TWh |
| Electricity CO₂ intensity | 30.00 | kt CO₂ / TWh |
| Gasoline CO₂ intensity    | 1,650.00 | kt CO₂ / TWh |

### H. Consistency residuals

| Check | Absolute residual | Relative |
|---|---:|---:|
| electricity + gasoline = total energy   | 0.000e+00 kWh | 0.00e+00 |
| ECAV + STI = electricity                | 0.000e+00 kWh | 0.00e+00 |
| ICECAV = gasoline-objective             | 0.000e+00 kWh | 0.00e+00 |
| electricity CO₂ + gasoline CO₂ = total CO₂ | 0.000e+00 kg | 0.00e+00 |
| ECAV CO₂ + STI CO₂ = electricity CO₂    | 0.000e+00 kg | 0.00e+00 |


## Recommended figure label corrections

| Old wording | Recommended replacement | Reason |
|---|---|---|
| "Terra Watts Hour" | "terawatt-hours (TWh)" or simply "TWh" | "Terra" is a misspelling and "Watts Hour" is not the SI form. TWh is the standard SI prefix for the energy unit. |
| "CO2" | "CO₂" | Subscript is the chemical-formula convention used in the manuscript and in IPCC outputs. |
| "EAV" | "ECAV" | The current code calls the battery-electric autonomous vehicle category `ECAV` (Electric CAV) throughout `footprint_model.py`, the v9 `core.py`, the `weather_module.py`, and every output CSV column. "EAV" is older notation that no longer matches the live model — using it would diverge from `ECAV Power (kWh)` / `ECAV Emissions (kg CO2)` columns. Recommendation: rename the figure label to **ECAV** for consistency. |
| "Consumption By Objectives" | "Energy by ATS category" | "Objective" is ambiguous in figure context; the rows correspond to ATS categories (ECAV, ICECAV, STI). |
| "Electricity Source Type" | "Electricity source mix" | "Mix" matches the f_clean / 1−f_clean partition the model exposes. |
| "Fuel Source Type" | "Fuel source" | The model has only one fuel-side category (gasoline) so "type" is misleading. |
| "Kiloton" / "Kton" | "kt CO₂" or "kilotons CO₂" | SI symbol with explicit CO₂ tag avoids ambiguity with mass-only kt. |
| "Renewable" (if used) | "Low-carbon electricity" | The code variable is `f_clean` and the label inside `weather_module.py`, the configs, and the dashboards is "low-carbon electricity share". `f_clean` includes nuclear and large hydro, which are non-renewable but low-carbon. Use **low-carbon** to stay faithful to the code definition. |
