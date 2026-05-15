# Component-Level Recalibration of CLEAR-ATS Utility-Phase Energy — Audit Memo

**Step:** `audits/step_08_component_power_realignment/`
**Surface:** new `v10_streamlit_app/` (calculation-only successor to v9).
**Scope of change:** the utility-phase energy *back-end* and its Monte-Carlo priors. No
production / logistics / end-of-life numbers change. No v3–v9 dashboard, no
`footprint_model.py`, and no `configs/*.json` file is modified. v10 is additive.

---

## 1. Problem statement

Figure 4 of the manuscript and the v9 dashboard implied that the **autonomy stack
(sensing + computing + communication)** is ~75–85 % of a battery-electric L5 CAV's
total energy. Fielded CAVs put that share at roughly **5 %–25 %** (Tesla FSD HW3/HW4
computer < 100 W system; NVIDIA DRIVE Orin SoC 15–60 W; NVIDIA DRIVE Thor system;
Waymo 5th-generation onboard compute estimated at a few hundred watts to ~2 kW for
robotaxi duty). Two independent issues, plus one critical follow-up, were found.

**(a) Inflated utility-phase computing energy.** `configs/california.json` carries
L3/L4/L5 CAV computing of **4,960 / 9,920 / 19,841 kWh/yr** — already above the
manuscript's own Extended Data Table 5 base case (**3,539 / 6,616 / 10,207 kWh/yr**),
which in turn came from per-inference energies measured on an **NVIDIA A100 server GPU**
(Table 6) multiplied by **per-agent inference counts** (§2.1.2(1): motion prediction
"15–36 Hz per agent"). At 3 h/day driving the config's L5 figure implies **~18.1 kW of
continuous on-vehicle compute** — about 20× the ~0.84–1.2 kW per-vehicle bound that
Sudhakar, Sze & Karaman (2023, *IEEE Micro*; reference [1] of the manuscript) identify
for AV computing emissions to stay below data-center scale.

**(b) Hidden propulsion back-solve in Figure 4.** `v9_streamlit_app/pages/02_Utility_Phase_Energy.py`
(lines 136–148; same hook in v7) hard-coded `_AV_SHARE_TARGETS = {("BEV","L5"): 0.2506, …}`
and computed `propulsion = av_total / target_share − av_total`. This forced the on-screen
percentages to match the manuscript while silently inflating the BEV propulsion bar to
~60 MWh/yr (vs the configured ~3.565 MWh/yr Tesla-Model-3-realistic anchor). The visible
bars therefore *hid* the underlying compute inflation.

**(c) Pre-change snapshot** (`v9_pre_change_baseline.csv`, captured before any edit) — implied
continuous on-vehicle / per-24h compute power at the manuscript's 3 h/day assumption:

| region | unit | level | computing kWh/yr | autonomy share | implied compute kW |
|---|---|---|---|---|---|
| california | ECAV | L3 | 4,960 | 58.6 % | 4.53 |
| california | ECAV | L5 | 19,841 | 85.0 % | **18.12** |
| california | ICECAV | L5 | 31,746 | 69.5 % | **29.0** (fuel-equiv) |
| california | STI | Highly | 158,730 | 100 % | **18.12** (per 24 h) |

Same diagnosis at Ohio (L5 ECAV computing 13,891; share 80.1 %) and the U.S.-Average
config (which additionally carries grossly out-of-scale sensing/communication numbers —
L3 sensing 1,053 kWh/yr, communication 506 kWh/yr — that have no physical basis at the
per-unit level).

---

## 2. Root cause — which term caused the overshoot

The error is **entirely in the computing-power term, not the component counts**. The
manuscript's Extended Data Tables 3 & 4 (CAV / STI component inventories) are within
Waymo / Tesla / U.S.-DOT-blueprint ranges; v10 re-uses them verbatim (they already live
in `v9_streamlit_app/one_time_data.py` as `CAV_COUNTS` / `STI_COUNTS`).

| Term | Manuscript treatment | Why it overshoots | v10 fix |
|---|---|---|---|
| Per-inference energy | Measured on **NVIDIA A100** (400 W TDP server GPU), Table 6 | Deployed automotive ASICs (Tesla FSD chip < 40 W; NVIDIA DRIVE Orin SoC 15–60 W; DRIVE Thor system) run the same INT8-quantised, pruned models at ~5–10× lower energy per inference and **batch all agents in one forward pass**. | The compute *slot* in the registry is sized by **deployed-silicon class** (Tesla-FSD-class at L3, Orin-class at L4, Thor-class at L5), not A100 energy. |
| Inference *count* | "15–36 Hz **per agent** × N agents" → 450–1,800 inferences/s in heavy traffic | Scene-level motion-prediction models (AgentFormer, MotionNet, Trajectron++ — all in Table 6) run **one batched forward pass per frame** that handles all tracked agents jointly; agent count is sub-linear, not linear. | Agent count enters only through the dimensionless `traffic` scenario factor (≤ 1.42×), derived from the manuscript's own Table 5 light/moderate/heavy *ratios*. |
| Deployment mode | "Cloud Computing" marked as the base case (Table 5 asterisk) | Personal CAVs run onboard edge silicon; the cloud round-trip + datacenter overhead is not the default. | Edge is the v10 default; a `deployment` scenario factor (1.234×, the manuscript's own cloud/edge ratio) is available but off. |
| STI computing | Inherits the per-inference inflation × a 24/7 multiplier | Multiplies all of the above by ~8× duty | Bottom-up edge + HP-compute power at 24/7; ~0.8–1.0 kW continuous, not ~4.8–18 kW. |
| Component counts | Extended Data Tables 3 & 4 | **Not the problem** | Re-used verbatim. |

`old_vs_new_delta_table.csv` quantifies it: the **computing** ratio old/new is **75× /
57× / 27×** for L3 / L4 / L5 ECAV; the **sensing** ratio is only **~1.06–1.20×** (the
config's sensing numbers were already roughly right); communication ~6.7–8.7× (the
config's tiny communication numbers were slightly overstated).

---

## 3. The fix — bottom-up component registry (v10)

`v10_streamlit_app/component_registry.py` keeps the manuscript's *method*
(component → subsystem → unit → fleet → state; Methods §4.1.3 — `E_sensing = c_s Σ P_i t_i`
for sensing, discrete power modes for communication, measured-rate integration for
computing) and re-uses the existing component-count tables. Every per-unit subsystem
energy is assembled as

    E_{unit,subsys}^utility(scenario)
        = Σ_{i ∈ subsys}  N_i^(unit) · P_i^(level) · T · A_i · U_i^(level) · F_scenario

where `N_i` = component count (`one_time_data.CAV_COUNTS` / `STI_COUNTS`), `P_i` =
per-component power (this registry, **level-dependent for the compute slot**), `T` = active
hours/day (3 h for personal CAVs, 24 h for STI), `A_i` = active-fraction within active
hours, `U_i` = per-level utilization, `F_scenario` = dimensionless scenario multiplier.

`ComponentRegistryEnergyModel` is a drop-in replacement for `FixedTableEnergyModel`: it
returns `{sensing, computing, communication}` kWh/yr per (level, year), so
`TransportModel`, the year loop, fleet aggregation, cohort-efficiency decay, the weather
Dirichlet, and Monte Carlo are unchanged. Only the *source* of the numbers shifts. v10's
`core.py` routes the deterministic path and the live residual band through this model;
the v9 dashboard imports a separate module object and is untouched.

### 3.1 Per-component power table (every value sourced or honestly tagged)

Full table with source notes: `component_power_sources.csv`. Evidence tiers — *vendor_datasheet*
(datasheet range), *vendor_conference* (vendor technical talk / press), *blueprint*
(government engineering standard), *vendor_estimate* (blend of published part TDPs into a
system estimate — widened ×1.25 in Monte Carlo), *assumption* (engineering estimate
awaiting datasheet verification — widened ×1.5). Nothing is fabricated; every entry has a
`source_note`.

| Component | Subsystem | Power W (low / median / high) | Evidence | Anchor |
|---|---|---|---|---|
| Onboard Computing Unit — **L3** | Computing | 50 / 120 / 200 | vendor_conference | Tesla FSD HW3 board ~72–100 W (Hot Chips 2019); Mobileye EyeQ6 ~33 W/chip; NVIDIA Orin-N 15–40 W |
| Onboard Computing Unit — **L4** | Computing | 100 / 220 / 350 | vendor_conference | NVIDIA DRIVE AGX Orin SoC 15–60 W (254 INT8 TOPS); deployed L4 platform w/ carrier+redundancy ~100–350 W |
| Onboard Computing Unit — **L5** | Computing | 250 / 400 / 650 | vendor_conference | NVIDIA DRIVE Thor (~1000 INT8 TOPS / ~2000 FP4 TFLOPS); single→dual-Thor w/ full redundancy ~250–650 W |
| Edge Computing Unit (STI) | Computing | 50 / 120 / 250 | vendor_estimate | NVIDIA Jetson AGX Orin module 15–60 W + carrier/networking/PoE in cabinet |
| HP Computing Unit (STI) | Computing | 250 / 450 / 800 | vendor_estimate | DRIVE Thor-class accelerator / compact 2–4-GPU roadside edge server |
| Onboard Camera | Sensing | 1.5 / 2.5 / 4.0 | vendor_estimate | HDR imager (Sony IMX490 / onsemi AR0820 class) + ISP + GMSL2 serializer |
| Onboard LiDAR S | Sensing | 8 / 14 / 20 | vendor_datasheet | Solid-state short-range (Hesai FT120, RoboSense E1, Innoviz One) |
| Onboard LiDAR L | Sensing | 13 / 22 / 32 | vendor_datasheet | Long-range mechanical/hybrid (Hesai AT128/Pandar128, Velodyne VLS-128, Luminar Iris, Ouster OS2) |
| Onboard Radar | Sensing | 3 / 6 / 12 | vendor_estimate | 77 GHz (Continental ARS540 ~10–12 W; Bosch 5th-gen corner ~3–7 W) |
| Sonar | Sensing | 0.5 / 1.0 / 2.0 (active_fraction 0.25) | vendor_estimate | Ultrasonic park-assist transducer + driver IC, low-speed only |
| Inductive Loop Detector (STI) | Sensing | 3 / 6 / 12 | blueprint | NEMA TS-2 loop-detector card (FHWA Traffic Detector Handbook) |
| Static Camera (STI) | Sensing | 4 / 8 / 15 | vendor_estimate | Fixed IP traffic camera (Axis P-series, Bosch DINION) |
| Static HP LiDAR (STI) | Sensing | 25 / 40 / 60 | vendor_datasheet | Roadside 360° LiDAR (Hesai PandarQT/AT, RoboSense M-series, Ouster OS-series) |
| Static HP Radar (STI) | Sensing | 10 / 18 / 28 | vendor_estimate | Roadside imaging radar (Smartmicro UMRR, Continental ARS548RDI) |
| Cellular Comm. Unit | Communication | 2 / 4 / 8 (active_fraction 0.5) | vendor_datasheet | Automotive 5G/C-V2X module (Quectel AG550Q/RG500Q class) |
| DSRC | Communication | 3 / 5 / 10 (active_fraction 0.5) | vendor_datasheet | DSRC/C-V2X OBU (Cohda MK5/MK6 class) |
| Roadside Unit (STI) | Communication | 15 / 25 / 40 | vendor_datasheet | Roadside V2X unit (Cohda MK6, Kapsch RSU) |

Per-level utilization (duty within active hours): Onboard Computing 0.50 / 0.72 / 0.85 at
L3 / L4 / L5; Edge Computing 0.30 / 0.55 / 0.75 at Basic / Semi / Highly; HP Computing
0.75 at Highly; Cellular 0.6 / 0.8 / 0.9; DSRC 0.5 / 0.7 / 0.8; Roadside Unit 0.6 / 0.8 / 0.9;
all sensors 1.0. Duty cycle: CAV personal-use `Triangular(2.0, 3.0, 4.0)` h/day (the
manuscript's 3 h baseline; symmetric so the MC mean = the deterministic), CAV robotaxi
sensitivity `Triangular(8, 12, 16)`, STI `Triangular(20, 24, 24)`.

### 3.2 Why the compute slot is level-dependent

Extended Data Table 3 keeps a single "OnBoard Computing Unit" entry across L3/L4/L5, but
deployed silicon scales with autonomy level even when the *count* doesn't: an SAE-L3
highway-pilot system (Mercedes Drive Pilot, Honda Legend; Tesla HW3, Mobileye EyeQ6) runs
on ~70–120 W of compute, whereas an L5 stack (Waymo 5th-gen, robotaxi-grade) uses
Thor-class accelerators at ~250–650 W *and* the count doubles to 2 at L5 (Table 3). The
`P_i^(level)` dict captures this; the formula is still `N · P · T · A · U · F`.

---

## 4. Results — before vs after

Full tables: `corrected_subsystem_energy.csv`, `old_vs_new_delta_table.csv`,
`system_share_before_after.csv`. Base case = moderate traffic, clear weather, daytime,
edge compute, 3 h/day CAV duty, 24 h/day STI; `icecav_power_factor = 1.6`; propulsion
anchors BEV 3,565 kWh/yr (FHWA ~11,500 mi/yr × EPA fleet BEV ~0.31 kWh/mi), ICE 14,200
kWh/yr-eq (11,500 mi / EPA ~27.3 mpg × EIA 33.7 kWh/gal LHV).

### 4.1 Per-unit autonomy-stack energy (kWh/yr) and autonomy share of total vehicle energy

| Unit / level | v9 config AV total | v9 share | **v10 AV total** | **v10 share** | manuscript-reported share |
|---|---|---|---|---|---|
| ECAV (BEV) L3 | 5,056 | 58.6 % | **133.5** | **3.6 %** | 15.8 % |
| ECAV (BEV) L4 | 10,130 | 74.0 % | **350.7** | **9.0 %** | 20.0 % |
| ECAV (BEV) L5 | 20,202 | 85.0 % | **1,048.2** | **22.7 %** | 25.1 % |
| ICECAV (ICE) L3 | 8,090 | 36.3 % | **213.7** | **1.5 %** | 5.3 % |
| ICECAV (ICE) L4 | 16,208 | 53.3 % | **561.1** | **3.8 %** | — |
| ICECAV (ICE) L5 | 32,323 | 69.5 % | **1,677.2** | **10.6 %** | 8.2 % |
| STI Basic | 40,712 | 100 % | **1,892.2** | 100 % | (>80 %) |
| STI Semi | 81,522 | 100 % | **5,851.7** | 100 % | — |
| STI Highly | 161,360 | 100 % | **14,270.0** | 100 % | (96.7 %) |

**Computing sub-totals (kWh/yr):** L3 ECAV **65.7**, L4 **173.4**, L5 **744.6** (vs config
4,960 / 9,920 / 19,841 — 27–75× lower). STI Highly computing **9,066.6** (vs config
158,730 — 17.5× lower). Implied **average** on-vehicle compute power at L5: ~0.68 kW
(electrical), ~1.09 kW fuel-equivalent for an ICECAV — under the ~1.2 kW screening bound.
Implied STI Highly continuous compute: ~1.0 kW (24/7 infrastructure, not subject to the
per-vehicle bound).

**v10 L5/L3 computing ratio ≈ 11.3×** — consistent with the manuscript's "per-unit annual
energy demand rises by up to 11 times" (§2.1.2) — but here it arises from a manuscript-
grounded count doubling (Table 3: 1→2 compute units) × a documented silicon-class jump
(L3 ~120 W → L5 ~400 W) × a utilization rise (0.50→0.85), not from per-agent inference
inflation.

### 4.2 Headline numbers that change

- **"Enabling full self-driving adds 219 MWh of electricity over a 12-year vehicle
  lifespan"** (abstract / §2.1.1, = `L5_UTILITY_CUMULATIVE_12YR_KWH`): v10 gives
  12 × 1,048 ≈ **~12.6 MWh over 12 years** for the L5 autonomy stack — a ~17× reduction.
- **"Annual utility energy of a L5 CAV (18,232 kWh) is nearly twice its production energy
  (9,231 kWh)"** (§2.1.1, Table 2): v10 gives ~1,048 kWh/yr utility vs ~9,237 kWh
  production+logistics — the autonomy stack's *annual operational* energy is now ~11 % of
  its *one-time embodied* energy. The "utility ≈ 2× one-time" framing inverts for the
  autonomy subsystem (the manuscript already notes the one-time stage is 33–42 % of total
  L5 autonomy energy; v10 makes it the dominant share).
- **"STI Highly requires more than 2× the annual energy of a L5 ICE CAV and nearly 10× a
  L5 EV CAV"** (§2.1.3): under v10, STI Highly (~14.3 MWh/yr) is ~12× a L5 ECAV's autonomy
  stack and ~13.6× a L5 ICECAV's, so the ">10× the autonomy stack" ordering survives;
  but it is only ~0.9× a L5 ICE CAV's *total vehicle* energy and ~3.1× a L5 BEV's total,
  so the "2× the total energy of a L5 ICE CAV" phrasing does **not** survive — STI is
  larger than a CAV's *autonomy stack* by ~12–14×, not larger than a CAV's *whole-vehicle*
  energy by 2–10×.

### 4.3 What does *not* change

Production / logistics / end-of-life energy (Figure 3a/b, Table 2 production+logistics
columns, `one_time_data.COMPONENTS` / `TABLE2_PROD_LOG` / `FIGURE3B_UNIT_TOTALS`); fleet
growth / retirement logic; cohort-efficiency decay; the weather Dirichlet; the v3–v9
dashboards; `footprint_model.py`; `configs/*.json`. The component *counts* (Tables 3 & 4)
are re-used verbatim.

---

## 5. How the A100 / testbed data is now used

The manuscript's Table 6 per-inference energies (4–62 J on the A100) **no longer feed
absolute kWh** in v10. They feed only the dimensionless `SCENARIO_FACTORS` — the
light/moderate/heavy *traffic* ratio (0.667 / 1.000 / 1.416, from Table 5's own L5-CAV
computing entries), the clear/cloudy/adverse *weather* ratio (1.000 / 1.10 / 1.282), the
day/night ratio (1.000 / 1.150), the GPU-utilization-intensity ratio (1.000 / 2.333 /
4.000), and the edge/cloud ratio (1.000 / 1.234). These ratios are reproduced from the
manuscript's Tables 5 & 8 so the scenario *sensitivities* stay faithful even though the
absolute baseline is rebuilt bottom-up. Cloud-vs-edge is a separate `deployment` factor
that is **off by default** for personal CAVs.

---

## 6. Monte-Carlo change

v3–v9 propagated load-model (L2) uncertainty as multiplicative log-normal scale factors on
the *flat per-level aggregates* (`data_uncertainty.consumption_rates.ecav_scale_factors`,
σ ∈ [0.15, 0.35]; manuscript Table 9 L2 rows). v10's `compute_live_residual_band` instead
draws **physical-parameter** perturbations: per-component power multipliers (unit-median
log-normals whose 5–95 % interval matches the evidence-tier-widened registry range; median
= 1.0 exactly so the deterministic median stays inside the band) and the CAV duty cycle
`Triangular(2, 3, 4)` h/day. The legacy flat-table scale-factor priors remain in
`configs/*.json` (so v3–v9 keep working) but are inert under the registry model — they
perturb tables it does not read. All other priors (initial fleet / grid betas, emission-
factor triangulars, the CAV/STI level-mix Dirichlets, `icecav_power_factor`, `retire_year`,
`cohort_decay_factor`, the trajectory drivers, the weather Dirichlet) are unchanged and
still drive the band.

**Deterministic-vs-MC-p50 offset (known, inherited from v9 — `uncertainty_distribution_check.csv`).**
The deterministic line uses the manuscript's *modal* parameter values — in particular a
2.8-year hardware-doubling time, which the manuscript explicitly picks as "the optimistic
end of Moore's law" (§2.3). The MC p50 reflects the *median* of each prior; for the
efficiency-doubling prior `Triangular(1.5, 2.8, 5.0)` that median (≈3.04 yr), exponentiated
over decades, places the MC p50 well above the deterministic line. In high-renewables
California the deterministic line sits comfortably inside the q05–q95 envelope
(|det − p50| ≈ 6–15 %); in fossil-heavy Ohio (where long-lived grid emissions compound the
inefficiency) it sits near the lower edge (and in the earliest years just below q05). This
is a pre-existing characteristic of v3–v9 — the deterministic line should be read as the
*optimistic / most-likely* scenario, not the median outcome. Closing the gap would require
re-centering the deterministic line on prior medians or symmetrizing the efficiency prior,
both of which would change the manuscript's headline figures and break comparability with
v3–v9; it is therefore left as a documented follow-up rather than a v10 change.

---

## 7. Required manuscript-text edits (apply only on a second authorization)

1. **§2.1.2 / Extended Data Table 5.** Replace "the computing subsystem contributes 98 % of
   the total energy consumption for Levels 3, 4, and 5 CAV" with the bottom-up share — at
   L5 computing is ~71 % *of the autonomy subsystem* (sensing ~28.6 %, communication
   ~0.4 %); at L3/L4 sensing and computing are comparable. Note that 98 % was a property of
   the A100-server-GPU benchmark, not of deployed silicon. The Table 5 absolute kWh should
   be re-derived (or footnoted) as server-GPU benchmark values, with a parallel
   deployed-silicon column from the component registry.
2. **§2.1.1 / abstract / Table 2.** Revise "annual utility energy for a L5 CAV (18,232 kWh)
   is nearly twice its production energy" → "~1.05 MWh/yr (deployed-silicon estimate), ~11 %
   of the ~9.24 MWh one-time production+logistics energy." Revise the abstract's "adds
   219 MWh of electricity over a 12-year vehicle lifespan" → "~13 MWh over 12 years
   (deployed-silicon estimate)" and report the **robotaxi sensitivity** (~3.0 MWh/yr at
   12 h/day → ~36 MWh over 12 yr) separately.
3. **§2.1.3 / Figure 4.** Replace the autonomy-share figures (BEV 15.8 % → 25.1 % L3→L5;
   ICE 5.3 % → 8.2 %) with the bottom-up shares (BEV ~3.6 % → ~22.7 %; ICE ~1.5 % → ~10.6 %)
   — or report both side by side with the recalibration noted. The L5 figures agree closely
   with the manuscript (BEV ~22.7 % vs 25.1 %; ICE ~10.6 % vs 8.2 %); the L3/L4 figures are
   lower because the manuscript over-counts low-autonomy compute. Reframe "STI is more than
   2× a L5 ICE CAV in annual energy" → "STI Highly is ~12–14× a L5 CAV's *autonomy stack*"
   (it is ~0.9× a L5 ICE CAV's *total vehicle* energy). The "32 % less" ECAV-vs-ICECAV
   autonomy-energy claim becomes "~37.5 % less" at `icecav_power_factor = 1.6`; it is
   "~32 % less" only at the lower end of that factor's `Triangular(1.3, 1.6, 2.0)` prior.
4. **Figure 4 panel.** Replace the auto-confirmed shares (the v3–v9 `_AV_SHARE_TARGETS`
   back-solve) with the bottom-up shares from `corrected_subsystem_energy.csv`, and add a
   panel showing the personal-CAV vs robotaxi-CAV duty-cycle sensitivity.
5. **§4.1.3 (Methods).** Add a paragraph stating that the deployed estimate uses automotive-
   ASIC power (Tesla FSD, NVIDIA DRIVE Orin/Thor) rather than the A100 server-GPU per-
   inference energies, and that scene-level motion-prediction models run one batched
   forward pass per frame (agent count enters sub-linearly via the traffic scenario factor),
   not one inference per tracked agent.
6. **State-level results (§2.2/§2.3).** The absolute ATS-attributable energy and emissions
   trajectories scale down by roughly 15–20× (the per-unit recalibration ratio, fleet-mix
   weighted). The *turning-point years*, the relative sensitivities to hardware efficiency /
   electrification / renewable growth, and the qualitative California-vs-Ohio contrast are
   unchanged. Re-run `footprint_model.py` with the v10 energy model before quoting absolute
   MtCO₂ figures in the revised manuscript.

---

## 8. Verification

| # | Check | Result |
|---|---|---|
| 1 | No hidden corrections — no `_AV_SHARE_TARGETS` / `target_share` assignment in `v10_streamlit_app/` | **pass** (only the page-02 docstring describes the removed hook; no code) |
| 2 | Bottom-up reproducibility — `ComponentRegistryEnergyModel` reproduces the audit CSV to 1e-6 kWh | **pass** (`tests/test_component_utility_model_v10.py`) |
| 3 | Evidence-tier coverage — every component has a tier ∈ {vendor_datasheet, vendor_conference, peer_reviewed, blueprint, vendor_estimate, assumption} and a `source_note` | **pass** |
| 4 | Power bounds — L3 CAV computing < 100 kWh/yr; L5 CAV computing < 1,000 kWh/yr; per-AV avg compute < 1.2 kW; STI Highly computing < 10,000 kWh/yr | **pass** (65.7 / 744.6 / 0.68–1.09 kW / 9,066.6) |
| 5 | Autonomy-share bands — BEV L3 ∈ [3,8] %, L4 ∈ [8,18] %, L5 ∈ [15,30] %; ICE L3 ∈ [1,3] %, L4 ∈ [2,6] %, L5 ∈ [4,12] % | **pass** (3.6 / 9.0 / 22.7 ; 1.5 / 3.8 / 10.6) |
| 6 | No back-solve regression — propulsion bar = the entered value, full stop | **pass** |
| 7 | Monte-Carlo consistency — deterministic in q05–q95 | **pass for CA & U.S.-Average**; **near-miss for Ohio** (det ≈ q01–q03 in early years) — see §6; documented as a v9-inherited characteristic, not a v10 regression |
| 8 | One-time phase numbers unchanged | **pass** for the production/logistics figures; the one-time page's *utility-comparison panel* now shows the recalibrated ~1.05 MWh/yr with an explanatory banner (the manuscript reference 18,232/218,784 is retained alongside for comparison) |
| 9 | State-scale consistency — `ATS_total = ECAV + ICECAV + STI` to numerical tolerance, all years | **pass** |
| 10 | App smoke test — `streamlit run v10_streamlit_app/streamlit_app.py` boots; all three pages render; Figure 4 shows realistic shares; Scenario Explorer projections complete | core import + full 68-year simulation + residual band verified non-interactively; interactive Streamlit boot not run in this environment |

---

## 9. Known limitations / verify before publication

- The `vendor_estimate` and `assumption`-tier component powers (cameras, radars, static
  cameras, edge/HP compute, STI radar) are blends of published part TDPs, not single
  datasheets — verify against module-level datasheets before the revised manuscript. They
  are widened ×1.25 / ×1.5 in Monte Carlo.
- The L5 compute slot (250 / 400 / 650 W per unit, ×2 units) sits at the high end of
  deployed automotive accelerators; a Tesla-FSD-class L5 stack would be ~2–3× lower. v10
  deliberately uses the high (Thor-class, redundant) end so the autonomy-stack estimate is
  conservative (not under-claimed). The robotaxi duty-cycle sensitivity (12 h/day) is the
  upper-bound operating case.
- STI Highly computing (~9.1 MWh/yr, ~1.0 kW continuous) is the single largest remaining
  uncertainty — a generously-provisioned multi-GPU roadside server could be 3–5 kW (closer
  to the manuscript's Table 8 value of ~4.85 kW continuous). v10 uses the lean
  Jetson-/Thor-class estimate; the MC band on Edge/HP compute power and utilization is
  correspondingly wide.
- The "98 % computing share of utility energy", the "94 % CAV sensing share of production
  energy", and the "9,237 vs 10,155 kWh L5 production+logistics" reconciliations are
  manuscript-text items carried over from earlier audit steps; the first is superseded by
  this memo (§4.1, §7.1) and the latter two are unchanged (production-phase).
- The Monte-Carlo for v10's *Scenario Explorer* uses the live residual-band path
  (`compute_live_residual_band`) with the registry model + physical-parameter priors. The
  committed `results/*__bundle-*_mc_runs.csv` files were generated with the old config and
  are stale for v10; regenerating them with the v10 model (200 samples × region × policy)
  is a follow-up. The live band is what the v10 Scenario Explorer renders.

---

## Deliverable index (`audits/step_08_component_power_realignment/`)

| File | Contents |
|---|---|
| `v9_pre_change_baseline.csv` | Pre-change per-region per-level subsystem energy + autonomy share + implied compute kW (from `configs/*.json`). |
| `grep_paths.txt` | Inflation-fingerprint grep over `.py` + `.md` (back-solve hook, inflated literals, server-GPU / edge-platform names, per-agent inference language). |
| `component_power_sources.csv` | Every component × (low/median/high power per level, active fraction, utilization, evidence tier, source note). |
| `component_inventory_by_level.csv` | Manuscript Extended Data Tables 3 & 4 verbatim + level → inventory-key map (L3 ← "L3 Medium"). |
| `corrected_subsystem_energy.csv` | v10 per-unit subsystem totals per level (ECAV / ICECAV / STI), with autonomy share and implied avg compute kW. |
| `old_vs_new_delta_table.csv` | Per (unit, level, subsystem) old/new ratio with the term-changed attribution. |
| `system_share_before_after.csv` | Autonomy-share-of-total-vehicle-energy by (powertrain, level) before/after, with the realistic-band check and the manuscript-reported share alongside. |
| `uncertainty_distribution_check.csv` | Deterministic vs p05/p50/p95 of the v10 residual band, per region, at 2030/2040/2050/2060; det-vs-p50 relative gap; in-band flags. |
| `COMPONENT_REALIGNMENT_MEMO.md` | This memo. |

Generated by `scripts/audit_component_utility_v10.py`.
