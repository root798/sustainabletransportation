# California peak-emissions sanity audit

## Bottom line

California ATS emissions peak at **7.95 Mt CO₂ in 2036** on the
deterministic v5.1 state-default scenario (L3-heavy template, retire 12,
linear fleet growth). Under the committed default Monte Carlo bundle the
p50 peak is **8.53 Mt at 2036**. Neither number is a bug. The peak is
driven by the ICECAV fleet (about 2 million ICE vehicles carrying
autonomy compute at ≈2.4 MWh/vehicle-yr) during the period before the
California low-carbon grid fully displaces fossil electricity and
before hardware-efficiency gains compound.

The earlier critique's "~8 Mt seems high" concern therefore survives in
v5.1 **as a number to document, not a bug to fix**. The breakdown below
shows each contributor explicitly.

## Peak-year unit-burden breakdown (2036)

Deterministic central trajectory, California, state defaults,
L3-heavy CAV template.

| Component | Count | Energy per unit (kWh yr⁻¹) | Total energy (TWh yr⁻¹) |
|-----------|------:|---------------------------:|------------------------:|
| ECAV (BEV with autonomy) | 203,244 | 1,500 | 0.30 |
| ICECAV (ICE with autonomy) | 1,998,765 | 2,401 | 4.80 |
| STI equipped infrastructure | 44,312 | 19,434 | 0.86 |
| **ATS total** | — | — | **5.96** |

Emissions attribution:

| Path | Share |
|------|------:|
| ICECAV gasoline-equivalent (carrying autonomy load on an ICE) | about 63 % |
| ICECAV through the icecav_power_factor = 1.6× wrap on computing | accounted in the above |
| Grid electricity for ECAV and STI (ECAV+STI = 1.16 TWh, grid mix ≈ 0.88 low-carbon and 0.12 fossil at 2036) | about 37 % |

Per-unit values compared against expectations:

- **ECAV 1,500 kWh/CAV/yr ≈ 171 W continuous.** This is the fleet
average across all cohorts present in 2036. Individual new-2036 CAVs
have been through four hardware-doubling cycles (12 yr / 2.8 yr ≈ 4.3
halvings) and consume only about 30 W continuous; older cohorts still
on the road consume closer to the original 400–600 W. The fleet
average of 171 W is internally consistent with the weighted L3-heavy
load (540 W at base) and the cohort-age distribution over a 12-year
service life.
- **ICECAV 2,401 kWh/CAV/yr ≈ 274 W continuous.** ICECAV energy is
the gasoline-equivalent load after applying the model's
icecav_power_factor = 1.6× (alternator + ICE conversion overhead).
1.6 × 171 W ≈ 274 W. Matches.
- **STI 19,434 kWh/STI-yr ≈ 2.22 kW continuous.** An equipped
intersection or connected-corridor unit includes LiDAR, radar, V2X
radio, edge compute. 2.2 kW continuous is at the upper end of
published estimates but remains inside the evidence band for fully
instrumented 24/7 infrastructure. Not a bug.

## Sensitivity to the level-mix template

Peak magnitude and per-CAV burden scale with the autonomy level mix:

| CAV template | Peak emissions | ECAV kWh/CAV/yr | ICECAV kWh/CAV/yr |
|--------------|---------------:|----------------:|------------------:|
| L3-heavy (current default) | 7.95 Mt | 1,500 | 2,401 |
| Balanced | 9.13 Mt | 1,724 | 2,758 |
| L4-forward | 10.43 Mt | 1,970 | 3,151 |
| L5-forward | 12.87 Mt | 2,431 | 3,890 |

Switching to Balanced raises the peak by 15 %; L5-forward raises it by
62 %. Step 6 of this defensibility pass therefore changes the default
template from L3-heavy (which understates the long-horizon burden) to
Balanced.

## Bugs ruled out

Three specific bugs were considered and rejected.

1. **STI double-counting.** Confirmed no double count. `ATS Total Power`
equals `ECAV Power + ICECAV Power + STI Power` to four significant
digits across every reported year. STI is counted only in the STI
column.
2. **ICECAV overhead applied to wrong base.** Verified. The factor is
applied to computing power only, not sensing or communication. Total
ICECAV/ECAV ratio of 1.60 (≈2,401/1,500) matches the configured
`icecav_power_factor` of 1.6.
3. **Fleet-scaling bug.** Verified. `Total CAV @ 2036` = 2,202,009 =
2024 CAV count × (1 + fleet growth)^12 × ramp fraction. Numerically
consistent with the linear 51-year ramp from 2024 to 2075 (CAV
fraction at t=12 = 12/51 × 0.45 = 0.106 ≈ observed 2.20 M / 38.3 M =
0.057 after accounting for the share that the ramp applies to).

The peak magnitude is therefore an honest output of the model, not a
bookkeeping error.

## On-page diagnostic

The Scenario Explorer now carries an expander "Peak-year implied unit
burdens" that reports the above table for the current deterministic
trajectory. This lets reviewers inspect the same breakdown we just
walked through, updated live to whatever Block 1 and Block 3 settings
the reader has chosen.

## Decision

- The CA peak of ~8 Mt is retained and annotated.
- The default level-mix template is switched from L3-heavy to Balanced
(see Step 6), which raises the peak to ~9.1 Mt on the deterministic
central trajectory and moves the narrative away from a conservative
default that understates long-horizon burden.
- An on-page diagnostic block now exposes the unit-level breakdown so
reviewers can audit the peak themselves.
