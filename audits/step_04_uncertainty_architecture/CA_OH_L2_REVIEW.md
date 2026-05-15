# CA_OH_L2_REVIEW.md

Focused review of the L2 load-model uncertainty state for California and Ohio only. Establishes what is deterministic, what is already uncertain, and what correlation structure each remaining item requires before specs are written.

**U.S. Average is out of scope.** Its `consumption_rates` block is quarantined (see `US_AVERAGE_SOURCE_TRACE.md`) and must not inform the L2 design.

---

## A. Item-by-item state (CA + OH)

### A.1 `consumption_rates.ecav_power.L{3,4,5}.{sensing,computing,communication}` — 9 cells per region

| Cell | CA | OH | Deterministic? | Has uncertainty? |
| --- | ---: | ---: | --- | --- |
| ecav L3 sensing | 78 | 106 | yes | no |
| ecav L3 computing | 4960 | 3472 | yes | no |
| ecav L3 communication | 18 | 12 | yes | no |
| ecav L4 sensing | 184 | 249 | yes | no |
| ecav L4 computing | 9920 | 6945 | yes | no |
| ecav L4 communication | 26 | 17 | yes | no |
| ecav L5 sensing | 325 | 446 | yes | no |
| ecav L5 computing | 19841 | 13891 | yes | no |
| ecav L5 communication | 36 | 24 | yes | no |

All frozen in MC. No `data_uncertainty.consumption_rates.ecav_power.*` block exists in either scenario file.

Within-region ratios are sensible — CA L3→L4→L5 sensing ≈ 2.4× per step, computing ≈ 2× per step, communication ≈ 1.45× per step. Cross-region ratios (CA/OH) are roughly 0.7× for sensing, 1.4× for computing, 1.5× for communication. These suggest:

- Within a region, per-level sensing/computing/communication are **strongly correlated** — an L4 CAV that is expensive at sensing is probably also expensive at communication.
- Across subsystems within a level, the three values share a common hardware-cost prior — bump up computing and you almost certainly bump up sensing too.
- Across CA and OH, values are **not independent** — they cite the same engineering references but with small regional adjustments for typical operating conditions.

These correlations matter for the design: per-cell independent priors would produce unrealistically wide bands because they'd let sensing and communication drift in opposite directions.

### A.2 `consumption_rates.sti_power.{Basic,Semi,Highly}.{sensing,computing,communication}` — 9 cells per region

| Cell | CA | OH | Deterministic? | Has uncertainty? |
| --- | ---: | ---: | --- | --- |
| sti Basic sensing | 176 | 179 | yes | no |
| sti Basic computing | 39682 | 27782 | yes | no |
| sti Basic communication | 854 | 569 | yes | no |
| sti Semi sensing | 1054 | 1076 | yes | no |
| sti Semi computing | 79365 | 55564 | yes | no |
| sti Semi communication | 1103 | 735 | yes | no |
| sti Highly sensing | 1303 | 1417 | yes | no |
| sti Highly computing | 158730 | 111129 | yes | no |
| sti Highly communication | 1327 | 884 | yes | no |

All frozen. Same correlation story as ECAV. The only non-trivial intra-region shape is `sti_Basic_sensing` being sharply lower than Semi/Highly (6× jump), which reflects a step change in infrastructure sensor complexity between Basic and Semi deployments. That shape should be preserved under uncertainty — only multiplicative scaling makes sense.

### A.3 `consumption_rates.cav_levels` and `sti_levels`

- Both hold `[0.5, 0.333, 0.167]` in CA and OH. Deterministic.
- Natural Dirichlet candidate: concentration parameter ≈ 10 would allow modest variation around the simplex mean without huge deviations.
- Sampler already supports `dist: dirichlet` with list-valued result (verified in `_sample_distribution` line 148–150); the only requirement is to place the spec directly as the value of `cav_levels` / `sti_levels` in `data_uncertainty.consumption_rates`, which the existing `_apply_data_uncertainty` / `_is_distribution_spec` path handles correctly.

### A.4 `decay_factor = 0.7`

- Hard-coded literal in `footprint_model.py:_initialize_cohorts` (line 334).
- Controls the age-weight of the initial CAV cohort distribution (newest cohorts get weight `0.7^0 = 1`, oldest get `0.7^(retire_year-1)`).
- Not in any scenario file.
- Small but non-zero effect on year-0 to year-11 power curves (initial cohort dominates until the retirement-driven refresh kicks in).

Migration needed before this can be made uncertain. Once in config, a narrow triangular `(0.5, 0.7, 0.9)` is appropriate — the underlying assumption is that CAVs have relatively new hardware, which is a modelling choice, not a deep physical property.

### A.5 `growth_rates.retire_year`

- Already sampled (step 02): integer triangular `(8, 12, 18)`. No change needed.
- Material effect on cohort rollover; confirmed widening bands relative to pre-fix baseline.

### A.6 `consumption_rates.icecav_power_factor`

- Already sampled (step 02): triangular `(1.3, 1.6, 2.0)`. No change needed.
- Applied multiplicatively to the entire ICECAV limb (sensing + computing + communication).

### A.7 "Efficiency applied to computing only" — structural assumption

- Hard-coded in `_calculate_power` (lines 515, 518, 535). Efficiency factor multiplies computing but not sensing or communication.
- This is a structural choice (S-class), not a continuous uncertainty.
- Two alternative regimes:
  1. Current: computing-only scaling (Moore's law applies only to processors).
  2. Alternative: all-subsystems scaling (sensor and radio technology also improves with the same doubling time).
- Effect is large at far horizon — in 24 doublings (CA, 68 years / 2.8 y), computing drops to 6×10⁻⁸ of original. If sensing/communication also scaled this way, the late-horizon trajectory would be dominated by entirely different factors.
- **Not an L2 continuous target**. Defer to a structural-scenario registry in a later stage. Call this out explicitly in the scope of this stage.

---

## B. Which items need per-cell vs per-level vs per-subsystem vs hierarchical uncertainty

### B.1 `ecav_power.*` and `sti_power.*` — **per-level × per-subsystem multiplicative factors**

Per-cell independent lognormal (18 priors per region):
- ❌ Too many knobs to author credibly.
- ❌ Breaks correlations within a level and within a subsystem — L4 CAV's sensing could drift up while its computing drifts down, which is unphysical.
- ❌ Produces bands that reviewers will read as "noisy" rather than "structured engineering uncertainty".

Per-level multiplicative factor only (3 priors per table = 6 per region):
- ✓ Preserves cross-subsystem correlation within a level — an expensive L4 stays expensive across sensing/computing/communication.
- ❌ Loses cross-level-within-subsystem correlation — sensing technology improves or worsens as a whole, but this design lets only level-wise shifts happen.

Per-subsystem multiplicative factor only (3 priors per table = 6 per region):
- ✓ Captures "sensing hardware is uncertain separately from computing hardware".
- ❌ Loses cross-subsystem correlation within a level — L4's sensing and L4's computing could move independently.

Hierarchical per-level × per-subsystem (3 + 3 = 6 priors per table = 12 per region):
- ✓ Both correlation dimensions are preserved.
- ✓ Effective multiplier on cell `(level, subsystem)` = `level_factor[level] × subsystem_factor[subsystem]`.
- ✓ Editable: one author can set 6 sigmas per region and produce reasonable bands.
- ✓ Minimal schema addition.

**Recommendation: hierarchical per-level × per-subsystem**. See `CA_OH_L2_DESIGN.md` for the final spec.

### B.2 `cav_levels` / `sti_levels` — **Dirichlet on the simplex**

- Single 3-dimensional prior per mix (2 priors total per region).
- Concentration ≈ 10 keeps draws close to the committed means while allowing moderate variation.
- Preserves the sum-to-1 constraint automatically.

### B.3 `decay_factor` — **narrow triangular after schema migration**

- `(0.5, 0.7, 0.9)` integer-free.
- Small additional band width; ensures the initial-cohort age distribution is not a silent lock-in.

### B.4 `retire_year` — **already handled** (step 02 triangular integer).

### B.5 `icecav_power_factor` — **already handled** (step 02 triangular).

### B.6 Efficiency-applied-to-computing-only — **defer (structural, not L2)**.

---

## C. Source-support that would improve the design

These items would let the L2 design become calibrated rather than expert-elicited. None are blocking; all would sharpen the story:

1. **Original engineering references** for CA and OH `ecav_power.*` and `sti_power.*` cells. Specifically:
   - Per-level sensing suite (what sensors? what operating duty cycle?).
   - Per-level computing hardware (what SoC / GPU class? what thermal envelope?).
   - Per-level communication radios (what standards? peak vs average power?).
   - If these are available, the per-subsystem sigma priors in §B.1 can be derived from the spread between cited references rather than guessed. Current recommendation uses `σ_level ∈ {0.15, 0.20, 0.25}` and `σ_subsystem ∈ {0.20, 0.30, 0.35}` — defensible but not calibrated.

2. **Confidence level for the 2075 CAV / STI target fractions** (CA 0.45 / 0.50; OH 0.45 / 0.50). Current triangular bounds are expert-elicited. A published adoption-pathway dataset would let us tighten or loosen these and document the source.

3. **Empirical vehicle service-life distribution** for the CA and OH light-duty fleets. The current integer triangular `(8, 12, 18)` covers reasonable uncertainty but is not cited. DOE AFDC or a national scrappage dataset would let us pin the mode and asymmetry.

4. **Efficiency-doubling-time histograms** from published compute-efficiency literature (e.g., Dennard scaling trend data, post-Moore-era server efficiency curves). Current triangular `(1.5, 2.8, 5.0)` is expert-elicited.

5. **Grid-intensity time-series** for CA and OH. Currently `e_clean = 0.03` and `e_fossil = 0.50` are deterministic means with triangular bounds on `e_fossil` and `e_gasoline`. EIA monthly grid-mix data would let us sharpen the distributions and optionally expand them to time-varying priors.

6. **Level-mix surveys or deployment plans** for CA / OH autonomous-vehicle stock projections. The `cav_levels = [0.5, 0.333, 0.167]` is a uniformly-decreasing prior with no regional specificity. A California AV pilot-deployment report or an Ohio DOT infrastructure plan could shift these meaningfully.

None of these are required to ship the next stage. They would let the L2 specs advance from "expert-elicited and defensible" to "calibrated and citable".

---

## D. What remains explicitly deterministic after the planned L2 stage

- All US Average `consumption_rates` — quarantined (not in scope for this stage).
- Adoption-curve form (`exponential`) — structural choice.
- Efficiency-curve form (`continuous`) — structural choice.
- Efficiency-model mode (`smooth`) — structural choice.
- Energy-model type (`fixed_table`) — structural choice.
- "Efficiency applied to computing only" — structural choice.
- Lifecycle boundary (utility-only) — structural choice.
- `BASE_YEAR = 2024`, `TARGET_YEAR = 2075` — calendar constants.
- `TURNING_YEAR_DECLINE_RATIO = 0.5` — definition.
- `INTERP_BOUNDARY_THRESHOLD = 1.5`, `INTERP_BOUNDARY_START_YEAR = 2027` — dashboard/back-end definition.
- `MAX_REASONABLE_POWER = 1e15` — numerical safeguard.
- `quantiles = [0.05, 0.5, 0.95]` — reporting convention.

These are by-design deterministic. None become L2 targets in this stage.
