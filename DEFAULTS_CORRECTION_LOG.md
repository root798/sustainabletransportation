# DEFAULTS_CORRECTION_LOG

| Region | Field | Before | After | Why |
| --- | --- | --- | --- | --- |
| California | initial_data.total_cars | 32,060,000 | 37,428,700 | Re-anchored to DOE AFDC 2024 total light-duty registrations. |
| California | initial_data.total_ev | 1,771,806 | 1,533,900 | Re-anchored to DOE AFDC 2024 BEV registrations and relabeled as BEV-only. |
| California | initial_data.f_clean | 0.63 | 0.656 | Re-anchored as a modeled low-carbon electricity share cross-checked to 2024 EIA California electricity data. |
| Ohio | initial_data.total_cars | 8,000,000 | 10,385,000 | Re-anchored to DOE AFDC 2024 total light-duty registrations. |
| Ohio | initial_data.total_ev | 47,490 | 69,400 | Re-anchored to DOE AFDC 2024 BEV registrations and relabeled as BEV-only. |
| Ohio | initial_data.f_clean | 0.39 | 0.247 | The old value was not defensible as a current Ohio clean/renewable share; replaced with a modeled low-carbon share cross-checked to 2024 EIA electricity data. |
| U.S. Average | initial_data.* | 20,030,000 cars / 909,648 EV / 0.51 clean fraction | 23,906,850 cars / 801,650 EV / 0.4515 clean fraction | Kept synthetic but re-derived from the corrected California and Ohio baselines and relabeled explicitly as synthetic. |
