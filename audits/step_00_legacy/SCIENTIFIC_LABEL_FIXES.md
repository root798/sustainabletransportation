# SCIENTIFIC_LABEL_FIXES

| Location | Old | New | Reason |
| --- | --- | --- | --- |
| dashboard_core.CONTROL_SPECS | CAV growth rate | CAV target fraction by 2075 | Matches actual _update_quantities() semantics. |
| dashboard_core.CONTROL_SPECS | STI growth rate | STI coverage target by 2075 | Matches actual _update_quantities() semantics. |
| dashboard_core.CONTROL_SPECS | Initial EV share | Initial BEV share of modeled light-duty stock | Current code uses BEV-only total_ev / total_cars. |
| dashboard_core.CONTROL_SPECS | Initial clean energy fraction | Initial modeled low-carbon electricity share | Makes modeled non-fossil semantics explicit. |
| Home / Scenario Explorer / Utility / State Results | Power (kWh) display wording | Annual energy demand in kWh/year-style units | Stored values are annual totals, not instantaneous power. |
| Scenario Explorer / Utility / Framework Scope | ICECAV displayed without definition | ICEAV definition surfaced while keeping internal ICECAV columns | Makes unit naming explicit for readers. |
| Scenario Explorer / Utility | EV share and clean-grid fraction | BEV share and modeled low-carbon electricity share | Avoids semantic drift between config meanings and public statistics. |
| Scenario Explorer / Utility | Partial subsystem labels | Consistent sensing / computing / communication breakdown across ECAV, ICEAV, and STI | Matches manuscript subsystem partitioning. |
| State Results | U.S. Average treated like a normal region label | U.S. Average (synthetic CA/OH midpoint) plus provenance note | The region is synthetic, not an official U.S. baseline. |
| Uncertainty Analysis | Unlabeled band source ambiguity | Explicit aligned-results vs legacy-notebook modes with pointwise p05-p95 / p50 language | Prevents silent source mixing and overclaiming. |
