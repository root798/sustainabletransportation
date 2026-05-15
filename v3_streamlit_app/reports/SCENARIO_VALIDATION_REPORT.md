
# Scenario Validation Report

## Before Vs After

- Before: some pages could blur aligned `results/` quantiles and legacy notebook quantiles through shared loader fallback.
- After: live scenario pages request aligned sources only; the uncertainty page exposes legacy notebook files only in an explicitly labeled legacy mode.

## Checks

| check | status |
| --- | --- |
| Explorer and utility pages use aligned `results/` quantiles only | pass |
| Uncertainty page separates aligned results from legacy notebook outputs | pass |
| Ohio and U.S. Average aggressive/conservative are treated as deterministic-only | pass |
| No cross-region substitution is used for missing files | pass |
| DU-INJECTED notebook registry includes California, Ohio, and U.S. Average baseline | pass |
| Invalid policy fallback is marked in runtime metadata | pass |

## Combination Matrix

| region | scenario | page | deterministic_support | quantile_support | fallback_used |
| --- | --- | --- | --- | --- | --- |
| California | Aggressive | Scenario Explorer | yes | none | no |
| California | Aggressive | State Results | yes | support table only | no |
| California | Aggressive | Turning Points | yes | not used | no |
| California | Aggressive | Uncertainty Analysis (aligned results) | n/a | no | no |
| California | Aggressive | Uncertainty Analysis (legacy notebook) | n/a | yes | no |
| California | Aggressive | Utility Phase Analysis | yes | none | no |
| California | Baseline | Scenario Explorer | yes | aligned `results/` only at exact defaults | no |
| California | Baseline | State Results | yes | support table only | no |
| California | Baseline | Turning Points | yes | not used | no |
| California | Baseline | Uncertainty Analysis (aligned results) | n/a | yes | no |
| California | Baseline | Uncertainty Analysis (legacy notebook) | n/a | yes | no |
| California | Baseline | Utility Phase Analysis | yes | aligned `results/` only at exact defaults | no |
| California | Conservative | Scenario Explorer | yes | none | no |
| California | Conservative | State Results | yes | support table only | no |
| California | Conservative | Turning Points | yes | not used | no |
| California | Conservative | Uncertainty Analysis (aligned results) | n/a | no | no |
| California | Conservative | Uncertainty Analysis (legacy notebook) | n/a | yes | no |
| California | Conservative | Utility Phase Analysis | yes | none | no |
| Ohio | Aggressive | Scenario Explorer | yes | none | no |
| Ohio | Aggressive | State Results | yes | support table only | no |
| Ohio | Aggressive | Turning Points | yes | not used | no |
| Ohio | Aggressive | Uncertainty Analysis (aligned results) | n/a | no | no |
| Ohio | Aggressive | Uncertainty Analysis (legacy notebook) | n/a | no | no |
| Ohio | Aggressive | Utility Phase Analysis | yes | none | no |
| Ohio | Baseline | Scenario Explorer | yes | aligned `results/` only at exact defaults | no |
| Ohio | Baseline | State Results | yes | support table only | no |
| Ohio | Baseline | Turning Points | yes | not used | no |
| Ohio | Baseline | Uncertainty Analysis (aligned results) | n/a | yes | no |
| Ohio | Baseline | Uncertainty Analysis (legacy notebook) | n/a | yes | no |
| Ohio | Baseline | Utility Phase Analysis | yes | aligned `results/` only at exact defaults | no |
| Ohio | Conservative | Scenario Explorer | yes | none | no |
| Ohio | Conservative | State Results | yes | support table only | no |
| Ohio | Conservative | Turning Points | yes | not used | no |
| Ohio | Conservative | Uncertainty Analysis (aligned results) | n/a | no | no |
| Ohio | Conservative | Uncertainty Analysis (legacy notebook) | n/a | no | no |
| Ohio | Conservative | Utility Phase Analysis | yes | none | no |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Scenario Explorer | yes | none | no |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | State Results | yes | support table only | no |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Turning Points | yes | not used | no |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Uncertainty Analysis (aligned results) | n/a | no | no |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Uncertainty Analysis (legacy notebook) | n/a | no | no |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Utility Phase Analysis | yes | none | no |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Scenario Explorer | yes | aligned `results/` only at exact defaults | no |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | State Results | yes | support table only | no |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Turning Points | yes | not used | no |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Uncertainty Analysis (aligned results) | n/a | yes | no |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Uncertainty Analysis (legacy notebook) | n/a | yes | no |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Utility Phase Analysis | yes | aligned `results/` only at exact defaults | no |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Scenario Explorer | yes | none | no |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | State Results | yes | support table only | no |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Turning Points | yes | not used | no |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Uncertainty Analysis (aligned results) | n/a | no | no |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Uncertainty Analysis (legacy notebook) | n/a | no | no |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Utility Phase Analysis | yes | none | no |

## Remaining Scientific Limitations

- Legacy notebook quantiles remain on disk and are still scientifically limited because they diverge from the current deterministic pipeline.
- Non-baseline aligned quantiles are still absent for all regions.
- `cav` and `sti` remain target-fraction controls under the current model implementation.
