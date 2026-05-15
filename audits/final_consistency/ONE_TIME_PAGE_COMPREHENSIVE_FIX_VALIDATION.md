# One-Time Energy page — comprehensive fix validation (v5.1.5)

## Assertion results

All post-fix assertions executed against the live module and the
baseline data. Full trace:

### Part 1 — Figure A data integrity

- `len(COMPONENTS) == 15` → PASS
- `Static HP LiDAR.energy_kwh == 607.58` → PASS
- `HP Computing Unit.energy_kwh == 654.32` → PASS

Root cause was the `adjusted_component_energy_with_sensing_refurb`
helper multiplying sensing values by the EoL refurbishment factor
`(1 - α × (1 - ALPHA_B3))` = 0.475 under defaults. Fixed by splitting
the helper into:
- `production_display_energy` — production-side only (sens_eff, life_ext).
- `eol_savings_per_unit` — EoL savings only.
- `adjusted_component_energy_with_sensing_refurb` retained as a
backward-compatibility alias used by the tornado chart.

### Part 2 — Figure B unit totals match manuscript Figure 3b

7 / 8 unit totals MATCH manuscript within 0.01. The remaining row
(STI Basic) shows a documented manuscript inconsistency, not a bug:
the Extended Data Table 4 counts × Figure 3a energies sum to 2,747 kWh
while Table 2 reports 2,140 kWh for STI Basic. The dashboard reports
the component-sum traceable from first principles; the gap is
surfaced in the in-page warning and the rebuttal cross-check.

| Unit | Live | Manuscript | Δ |
|------|-----:|-----------:|---:|
| CAV L3 Small | 2,850.1 | 2,850.2 | MATCH |
| CAV L3 Medium | 3,202.6 | 3,202.6 | MATCH |
| CAV L3 Large | 3,832.9 | 3,832.9 | MATCH |
| CAV L4 | 4,993.1 | 4,993.0 | MATCH |
| CAV L5 | 10,155.1 | 10,155.1 | MATCH |
| STI Basic | 2,747.4 | 2,139.8 | manuscript gap (documented) |
| STI Semi-Automated | 9,206.6 | 9,206.5 | MATCH |
| STI Highly-Automated | 13,312.2 | 13,312.2 | MATCH |

### Part 3 — Figure C STI Highly bar

- `marginal_count(STI_COUNTS["Highly"]) == 58` → PASS

Root cause of the missing bar was the Plotly `xaxis2` subplot config
not rendering the third category reliably. Fixed by replacing the
two-panel layout with a single chart that holds all 8 bars on a
unified y-axis, with a dotted vertical separator between CAV and
STI groups.

### Part 4 — Live metrics under default settings

- `L3 Small → L5 multiplier = 3.563×` → PASS (manuscript 3.5×,
tolerance 0.1)
- `L5 sensing share = 87.97%` → live value; manuscript cites 94% under
a different aggregation (documented as Critical-4)
- `STI Highly sensing share = 83.85%` → PASS (manuscript 84%,
tolerance 2%)

### Part 5 — parameter_labels.json has F-OT entries

All six `F-OT-XX` entries present:
- F-OT-01: Component mass
- F-OT-02: Material composition
- F-OT-03: Fabrication energy intensity
- F-OT-04: Inland logistics distance
- F-OT-05: Transport mode split
- F-OT-06: Refurbishment energy ratio

### Part 6 — Block 4 migration + session-state hygiene

- Legacy `st.radio("level", ["fixed", "low"], ...)` pattern is gone.
- Published / Custom selectbox pattern matches Scenario Explorer.
- Session state is initialised before widget creation via a
validation-aware loop that migrates legacy `"fixed"` / `"low"`
values to `"published"`.

## Cross-check summary (as rendered on the live page)

| Claim | Manuscript | Live | Status |
|-------|-----------|------|--------|
| Sensing share, CAV L5 | 94 % | 87.97 % | mismatch (documented) |
| Sensing share, STI Highly | 84 % | 83.85 % | match |
| L3 Small → L5 multiplier | 3.5× | 3.56× | match |
| L5 production + logistics | 9,237 kWh | 10,155 kWh (component sum) | mismatch (documented) |
| HP Computing Unit per unit | 654.32 kWh | 654.32 kWh | match |
| Static HP LiDAR per unit | 607.58 kWh | 607.58 kWh | match |

**4 / 6 match within 2 % tolerance.** The two mismatches are
documented manuscript-reconciliation items that pre-date the current
comprehensive fix pass and require a manuscript text update to close.
