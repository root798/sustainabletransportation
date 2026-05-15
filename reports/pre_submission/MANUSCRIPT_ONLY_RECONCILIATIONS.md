# Manuscript-only reconciliations

**Date.** 2026-04-18.
**Purpose.** Items listed here are **manuscript-text issues**. The
dashboard correctly reproduces every component-level value from the
Figure 3a inventory, Extended Data Tables 3 and 4, and the
`configs/ui_parameter_presets/*.json` priors. Where the manuscript
body text cites an aggregate value that does not reconcile with those
sources, the mismatch lives in the manuscript and is resolved by the
author's text-pass rather than by any dashboard change.

The dashboard no longer displays a yellow warning pill for these
items. It surfaces them as a neutral note inside a collapsed expander
so that readers who care can inspect the details without the page
appearing to carry a software error.

---

## 1. Sensing share: 94 % (manuscript) vs 88 % (live)

**Where it appears.** Manuscript §2.1.1 states "sensing accounts for
94 % of CAV one-time embodied energy."

**Dashboard live value.** For CAV L5, sensing is 88.0 % of the
component-sum one-time energy. Derivation: sensing components in
Extended Data Table 3 multiplied by their Figure 3a per-component
energies sum to 8,933 kWh. Total L5 one-time = 10,155 kWh. Share =
87.97 %.

**Hypothesis.** The 94 % figure is the sensing share of **component
count**, not energy. 63 of 67 marginal L5 components are sensors
(63 / 67 = 94.0 %). The energy share is 88 %.

**Recommended author action.** Rewrite the §2.1.1 sentence as two
complementary findings:

> "Sensing components make up 94 % of the Level 5 CAV marginal
> component count and 88 % of the Level 5 CAV one-time embodied
> energy. Sensors therefore dominate the autonomy stack by count and
> by embodied energy, while carrying roughly an 8 % per-unit energy
> discount relative to the highest-intensity components."

No dashboard change required.

---

## 2. STI Basic total: 2,140 kWh (Table 2) vs 2,747 kWh (component sum)

**Where it appears.** Table 2 column "Production + logistics" for
STI Basic lists 2,139.77 kWh. Figure 3b plots 2,140. Extended Data
Table 4 component counts for STI Basic (4 ILD, 2 RSU, 4 static
camera, 1 static HP LiDAR, 1 static HP Radar, 2 edge computing, 0 HP
computing) multiplied by Figure 3a per-component energies sum to
2,747.36 kWh.

**Gap.** 607 kWh, which is exactly 1 × Static HP LiDAR (607.58 kWh).

**Hypothesis.** Table 2 aggregation for STI Basic omits the Static
HP LiDAR row. This could be either (a) a typo in Extended Data
Table 4 (should show 0 Static HP LiDAR for Basic), or (b) a typo in
Table 2 (should show 2,747 kWh).

**Recommended author action.** Verify whether Basic STI deployments
actually include the Static HP LiDAR. If yes, update Table 2 / Figure
3b to 2,747 kWh. If no, update Extended Data Table 4 to show 0 Static
HP LiDAR for Basic and rely on the cheaper Static HP Radar only.

The dashboard reports the component-sum (2,747 kWh) because that is
reproducible from the published Extended Data tables.

---

## 3. L5 CAV production + logistics: 9,237 kWh (Table 2) vs 10,155 kWh (component sum)

**Where it appears.** Table 2 column "Production + logistics" for
CAV L5 lists 9,237.2 kWh. Figure 3b plots 10,155 kWh. Extended Data
Table 3 counts for L5 (35 camera, 4 LiDAR S, 2 LiDAR L, 14 radar,
8 sonar, 2 onboard computing, 1 cellular, 1 DSRC) multiplied by
Figure 3a per-component energies sum to 10,155.14 kWh.

**Gap.** 918 kWh, which is almost exactly 2 × Onboard Computing Unit
(2 × 458.59 = 917.18 kWh).

**Hypothesis.** Table 2 aggregation counts 1 Onboard Computing Unit
for L5, while Extended Data Table 3 counts 2. Only one of the two
numbers can be authoritative.

**Recommended author action.** Verify whether the Level 5 reference
architecture uses one or two Onboard Computing Units. Update
whichever table is inconsistent. Propagate the corrected total to
Figure 3b and the Main Text.

---

## 4. L5 annual utility: 18,232 kWh/yr (manuscript) vs 20,202 kWh/yr (live)

**Where it appears.** Manuscript §2.1.1 cites the L5 CAV annual
utility-phase energy at 18,232 kWh/yr. The dashboard's
`per_unit_l5_annual_utility_kwh(region="california")` helper returns
20,202 kWh/yr for a 1-vehicle pure-L5 California fleet with
hardware-doubling held constant at base year (no compounding).

**Gap.** 1,970 kWh/yr (10.8 %).

**Hypothesis.** The manuscript value may reflect (a) a fleet-
weighted cohort average rather than a pure base-year new-cohort
value, (b) a different state than California, or (c) a pre-v5.1.1
baseline scenario with different `consumption_rates.ecav_power`
values.

**Recommended author action.** Decide which scenario anchors the
18,232 figure and either (a) restore the manuscript assumption in
`scenarios/california/scenario.json` so the live value matches, or
(b) update §2.1.1 to 20,202 and propagate through dependent claims
(for example the 12-year cumulative "roughly 205 MWh" which should
become "roughly 242 MWh").

The dashboard shows both values side by side with the drift delta
labelled, but does not flag it as a software error.

---

## 5. Turning year: "before 2041" (manuscript) vs 2046 (dashboard default)

**Where it appears.** Abstract and Discussion cite "carbon-emissions
turning point reached before 2041 under the baseline scenario." The
dashboard default California turning year is 2046 under the
post-v5.1.3 defaults (Balanced CAV template, reverted Ohio values).

**Hypothesis.** The 2041 claim may reference the previous (pre-
v5.1.1) CAV template default of L3-heavy, or an aggressive-mitigation
scenario rather than the current Balanced baseline.

**Recommended author action.** Specify the scenario under which 2041
holds (for example: "under the aggressive mitigation preset with
L3-heavy template"). Alternatively update the abstract to 2046 with
the Balanced baseline explicitly named.

---

## 6. τ threshold: 0.5 (Methods) vs 1.5 (historical dashboard)

**Where it appears.** Methods Eq. 24 specifies τ = 0.5 as the
conservative default for the interpretation boundary. The dashboard
historically used τ = 1.5. v5.1.4 exposed both values side by side
in the Figure A metric strip so the reader can see both.

**Recommended author action.** Decide which threshold the manuscript
body text and rebuttal quote. If τ = 0.5 is the paper-facing choice,
update every IB reference to the τ = 0.5 year. If τ = 1.5, update
Methods Eq. 24 to match.

Current τ = 0.5 values under the default bundle after v5.1.3
regeneration:
- California: IB 2055
- Ohio: IB 2051

Current τ = 1.5 values:
- California: not reached within horizon
- Ohio: not reached within horizon

---

## Closing

None of items 1-6 is a dashboard bug. Each is a text / aggregation
inconsistency that the manuscript author must resolve. Estimated
2 – 3 hours of author time. After resolution, every on-page dashboard
value traces cleanly to the corrected manuscript.
