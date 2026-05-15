# CLEAR-ATS Dashboard (v9) — User Guide

*Clean Energy Automated Road Transport System — interactive scenario explorer for the energy demand and CO₂ emissions of road transport, 2024 onward.*

---

## 1. Purpose and scope

CLEAR-ATS is a scenario-conditioned simulation framework that projects the **energy demand (kWh yr⁻¹)** and **CO₂ emissions (kg CO₂ yr⁻¹)** of road transport from 2024 forward, with particular emphasis on how **Connected Autonomous Vehicles (CAVs)** and **Smart Traffic Infrastructure (STI)** reshape fleet-level energy use. The v9 dashboard is the active public-facing front end and is organised into four screens:

| Screen | Question it answers |
|---|---|
| **Overview** | What is CLEAR-ATS, and how is its uncertainty structured? |
| **One-Time Energy** | How much energy is embodied in *producing, shipping, and retiring* the autonomy hardware (production / logistics / end-of-life accounting)? |
| **Utility Phase Energy** | How much energy does *one* vehicle or one roadside asset consume *per year*, and how is it split between propulsion and the AV subsystems? |
| **Scenario Explorer** | At *state scale*, how do annual and cumulative ATS energy and CO₂ evolve under chosen deployment, electrification, grid, weather, and hardware-efficiency settings — and how wide is the residual uncertainty? |

**Two important boundaries that apply everywhere in the dashboard.**

1. **Life-cycle phase.** The **Scenario Explorer** and **Utility Phase Energy** pages report the *operational (utility) phase only* — the energy and emissions of running the vehicles and infrastructure. The **One-Time Energy** page reports the *production + logistics + end-of-life* phase separately. The two are never summed for you; cross-phase reasoning is the reader's responsibility (the dashboard provides the inversion panel on the One-Time page to support it).
2. **Regions.** California and Ohio are modelled at full quantitative resolution. **U.S. Average** is a synthetic CA/OH midpoint and is *quarantined* — its sensing and communication consumption cells diverge by 10–30× from the two real states, so any U.S. Average output is exploratory only and is flagged in red wherever it can be selected.
3. **Display horizon.** Although the simulator internally runs to 2092, every chart in the dashboard is **capped at 2075**. Predictive validity is not claimed beyond 2075. Some diagnostics (peak year, turning year, interpretation boundary) are still *computed* on the full internal horizon and will say "After 2075 (20XX)" when the event falls outside the display window.

---

## 2. Launching the dashboard

From the repository root:

```bash
pip install -r v9_streamlit_app/requirements.txt
streamlit run v9_streamlit_app/streamlit_app.py
```

The app opens in a browser. Use the left-hand Streamlit page list to move between the four screens. The **Scenario Explorer** opens with the sidebar expanded; the other pages open with the sidebar collapsed (they have few or no sidebar controls).

---

## 3. Overview page

A static landing page. It contains:

- A one-paragraph description of the framework.
- The **uncertainty-structure figure** (`assets/clear_ats_uncertainty_figure_v30.png`) — a schematic that traces uncertainty from input data and state conditions → unit-level demand → fleet-scale propagation → resulting energy and CO₂ ranges. The factor-reference tables on the Scenario Explorer are grouped to mirror this figure.
- A three-column "How to read this dashboard" key that summarises the other three pages.

There are no interactive controls on this page.

---

## 4. One-Time Energy page

> **What this page reports:** the *production and logistics* embodied energy of the autonomy hardware, plus a separate *end-of-life* accounting. Every number traces to the manuscript (Figure 3a, Figure 3b, Extended Data Tables 3 and 4, Table 2). In v9 the interactive sliders that earlier versions placed at the top of this page have been removed; the page now shows the manuscript baseline, and the equivalent assumptions are preserved read-only at the bottom.

### 4.1 Figure A — Component-level one-time energy ranking
A horizontal bar chart of per-unit embodied energy (kWh) for **every** ATS component, ranked low-to-high. Bars are coloured by subsystem — **sensing (blue), computing (gray), communication (red)**. A filled circle (●) on the y-label marks CAV components; a filled triangle (▲) marks STI components. Key takeaway built into the caption: the high-performance computing unit (654.32 kWh) and static high-power LiDAR (607.58 kWh) have the largest *per-unit* energy, but sensors are deployed in far greater *numbers*, so the sensing subsystem dominates the *total* (see Figure B).

### 4.2 Figure B — Unit one-time energy with subsystem decomposition
Horizontal **stacked** bars, one per unit type (STI Highly, CAV L5, STI Semi, CAV L4, CAV L3 Large/Medium/Small, STI Basic). Each segment is a subsystem; the in-bar label is that subsystem's *percent of the unit total*; the number at the right of each bar is the unit total in kWh (production + logistics only). Below the chart is a **"Figure B live vs manuscript comparison"** table that flags any drift > 1 % between the live component sum and the manuscript's Figure 3b value. One row, **STI Basic**, is a *documented manuscript inconsistency* (component sum 2,747.36 kWh vs alternative aggregation 2,139.77 kWh) — it is labelled "manuscript gap", not a bug. Caption reports the live sensing share for a Level 5 CAV (~88–94 %) and a Highly-Automated STI (~84 %) and the L3-Small → L5 energy multiplier (~3.5×).

### 4.3 Figure C — Marginal components across autonomy levels
How many *additional* hardware items autonomy introduces relative to a conventional vehicle or a traditional intersection. CAV units (L3 Small/Medium/Large, L4, L5) are on the left of the x-axis; STI tiers (Basic, Semi, Highly) on the right, separated by a dotted vertical line and group headers.

- **View toggle** (radio): *Component breakdown (default)* — stacked bars, one segment per component, with the total annotated on top of each stack; or *Total counts only* — a single bar per unit, CAV in blue, STI in green.
- **Per-level component inventory expander** — the full per-level, per-component count matrix (Extended Data Tables 3 + 4), with a **Download component inventory (CSV)** button.
- The caption explains the non-monotonicity of L3 Small/Medium/Large total counts (L3 Small uses 12 sonar to compensate for missing LiDAR; L3 Large eliminates sonar entirely) and contrasts it with the *energy*-weighted view in Figure B.

### 4.4 Live derived metrics
Four metric cards, computed from a fixed **representative fleet** (10 × L3 Small + 5 × L3 Medium + 2 × L3 Large + 1 × L4 + 1 × L5 CAV, plus 5 × Basic + 2 × Semi + 1 × Highly STI — *not* a regional projection, just a fleet that exercises every unit type):
- **Production + logistics (representative fleet)** in MWh.
- **Sensing share (fleet-weighted)** in % — the production-side analogue of the manuscript's 94 % CAV-L5 claim.
- **L3 Small → L5 multiplier** (≈ 3.5×).
- **End-of-life energy savings (fleet)** in MWh, with a `−X % of production` delta. An expander, **"How EoL savings are calculated"**, gives the exact formula `E_saved_per_unit = baseline_kWh × α × (1 − r)` (α = sensing refurbishment rate, baseline 0.70; r = refurbishment energy ratio, baseline 0.25 per §4.1.4) and shows the current numerics, including what the not-yet-wired failure fraction φ would change.

### 4.5 "Why the life-cycle optimisation must span both phases" (inversion panel)
Four metric cards: L5 production + logistics (9,237 kWh, Table 2); L5 annual utility energy (manuscript §2.1.1); L5 annual utility energy (live, California — derived by running a 1-vehicle pure-L5 fleet through the simulator's `_calculate_power`, with a drift-vs-manuscript delta); and L5 cumulative utility over 12 years. Then two donut charts: **L5 CAV production + logistics share** (live; sensing-dominated) and **Utility-phase subsystem share** (manuscript value, computing-dominated at ≈ 98 % for pre-2040 horizons — the Scenario Explorer shows this decaying toward ~23 % at 2075 California as hardware doubling compounds). The message: the subsystem that dominates *embodied* energy (sensing) is not the one that dominates *operational* energy (computing); life-cycle optimisation must address both.

### 4.6 End-of-life leverage (tornado chart)
A tornado chart of how far each end-of-life *design action* moves the representative-fleet one-time energy when taken to its lower / upper bound while the others stay at default. Rows: sensing manufacturing-efficiency improvement (0 → 60 %); sensing refurbishment rate α (0 → 100 %); sensor service-life extension (12 → 20 yr, which amortises production energy by 12/(12+N)); computing refurbishment adoption (0 → 100 %). **Green bars reduce** the burden, **red bars raise** it; bars below 0.5 % magnitude are unlabelled, and a bound that produces no change (e.g. computing refurbishment at its lower bound) is intentionally omitted rather than drawn as a fake zero. The expander **"How the bounds are computed"** gives the exact definition and the lifetime-extension mechanism, and explains why computing refurbishment has small leverage (computing is ~6 % of the one-time burden).

### 4.7 End-page reference material (collapsed)
- **Component inventory and one-time assumptions** — the Figure 3a per-component energy table, the wide per-unit-type count table, source citations, and a structural-assumptions table (manufacturing region, logistics model, refurbishment energy ratio, end-of-life failure fraction φ, computing obsolescence window, sensor refurbishment rate α, sensor service life), each tagged with its role in the analysis.
- **Data uncertainty ranges for one-time energy** — three tables (Production / Logistics / End-of-life), each listing the factor ID, name, distribution or range, affected quantity, role, and source. These are documented input ranges, **not** user-controllable on this page and **not** future-trajectory uncertainties.
- **Data consistency note** — a table cross-checking six manuscript claims against the live component-sum values, marking each "match" or "alternative aggregation".

---

## 5. Utility Phase Energy page

> **What this page reports:** annual *running* energy at the level of an individual unit — one vehicle or one roadside asset — split into propulsion and the three AV subsystems. State-scale evolution and long-horizon uncertainty live on the Scenario Explorer; this page deliberately stays at the per-unit level.

### 5.1 Controls (top of page)
- **AV-subsystem rate region (config file)** — selectbox: California / Ohio / U.S. Average. AV subsystem energy per autonomy level is read from `configs/<region>.json` (`consumption_rates.ecav_power`, `sti_power`, `icecav_power_factor`). The propulsion baselines below are US-averages and do **not** depend on this selection.
- **ICE propulsion (kWh / yr)** — editable number input, default 14,200 kWh yr⁻¹ (derivation: FHWA 11,500 mi yr⁻¹ ÷ EPA fleet-average 27.3 mpg → 421 gal yr⁻¹ × 33.7 kWh gal⁻¹ LHV).
- **BEV propulsion (kWh / yr)** — editable number input, default 3,565 kWh yr⁻¹ (11,500 mi yr⁻¹ × EPA fleet-average 0.31 kWh mi⁻¹).

### 5.2 Figure 1 — Annual running energy, per vehicle
Horizontal stacked bars: **Propulsion + Computing + Sensing + Communication** for six unit types (BEV / ICE × L5 / L4 / L3), ordered least-to-most automation-heavy, with the total (MWh yr⁻¹) annotated at each bar end. Colour key: propulsion = neutral gray, computing = blue, sensing = green, communication = red. Caption reading guide: for an ICE vehicle propulsion dominates even at L5; for a BEV at L5 the AV subsystem (especially onboard computing) is comparable in scale to propulsion — electrification changes the *structure* of the burden but does not eliminate the AV-system cost.

### 5.3 Figure 2 — AV subsystem breakdown (excluding propulsion)
Two side-by-side stacked-bar charts with the same colour mapping: **CAV units** (ECAV L3/L4/L5 and ICECAV L3/L4/L5 — ICECAV applies the ~1.6× `icecav_power_factor` for ICE conversion overhead) and **STI levels** (Basic / Semi / Highly), each with the per-unit total annotated.

### 5.4 "Reading this page"
A bulleted interpretation: propulsion dominates total vehicle energy; AV-system share rises with autonomy (roughly 4× from L3 to L5, driven by compute); computing dominates the AV subsystem with sensing second and communication smallest; electrification makes the AV subsystem a first-class decarbonisation lever for BEVs.

### 5.5 Utility-phase uncertainty ranges (read-only)
Tables grouping the relevant residual factors (ECAV subsystem load factors, STI subsystem load factors, ICECAV conversion/overhead factor) with factor ID, name, layer/class, distribution/range, affected quantity, and role. A further table collapses the state weather adjustment factors **F32–F36** into one row per region (clear/cloudy/adverse share centroid, the Dirichlet concentration κ, and the grid-side CO₂ weather sensitivity). These document residual input uncertainty; **live propagation across the fleet is done on the Scenario Explorer**, not here.

---

## 6. Scenario Explorer page — the main interactive screen

This page is the heart of the dashboard. It runs the simulator live on every interaction, draws the deterministic trajectory immediately, and rebuilds the Monte-Carlo uncertainty band automatically whenever any setting changes. Layout: **sidebar** (scope + scenario settings) → **main panel** (scope notes, fixed-data and structural-assumption expanders, Figure A, Figure B, Figure C, scenario-setting leverage, subsystem decomposition, factor reference, residual-uncertainty-range controls, full provenance).

### 6.1 Sidebar — Scope

| Control | Options | Effect |
|---|---|---|
| **Region** | California, Ohio (and U.S. Average only if the quarantine override is enabled) | Selects the regional configuration. Switching region resets *region-dependent* state to the new region's defaults (mitigation sliders, fixed data, residual-range selectors, custom specs) and rebuilds the band; *region-invariant* structural choices (level-mix templates, service life, fleet-growth form) are preserved. |
| **Policy** | Baseline, Aggressive, Conservative | Baseline applies regional defaults. Aggressive and Conservative apply documented deep-merge patches over the base config. Selecting anything other than Baseline raises a yellow warning that the committed Monte-Carlo bundle is centred on Baseline and is *not* re-centred under presets. |
| **Default residual band** | Default, Alternative reproduction ("paper-safe") | Which committed Monte-Carlo bundle backs Figure A *before* a live band has been computed for the current settings. "Default" is the main evidence-anchored bundle; "Alternative reproduction" is retained for comparison. |

### 6.2 Sidebar — State weather profile (expander, collapsed by default)
Implements the annual state weather-share Dirichlet (factors **F32–F36**). Two modes (radio):

- **Auto (state default)** — read-only. Uses the state climatology centroid and concentration: California `(clear 0.61, cloudy 0.25, adverse 0.14)`, κ = 120; Ohio `(0.34, 0.39, 0.27)`, κ = 96. A caption shows the active values.
- **Custom** — three number inputs (Clear / Cloudy / Adverse, 0–1, renormalised to sum to 1 automatically) set the annual weather-share *target*; an optional checkbox **"Expose concentration κ"** reveals a κ input (10–400; higher κ tightens the Dirichlet draw around the target). Switching to Custom flips the page-level "All default ranges active" status to No and forces a band rebuild.

The weather profile has two downstream effects: (a) it reweights the subsystem energy (using per-level adverse-weather utility tables for CAV L3/L4/L5 and STI Basic/Semi/Highly — communication stays flat where the source table reports no weather sensitivity); (b) it scales electricity-side CO₂ by `1 + γ_cloudy·Δf_cloudy + γ_adverse·Δf_adverse` with state-specific γ (CA: γ_cloudy = 0.10, γ_adverse = 0.25; OH: 0.06, 0.15).

### 6.3 Sidebar — Scenario settings

**Policy case (expander).** A discrete-pathway picker. For the selected region you can choose one of the documented policy cases — California: *CA-Committed* (SB 100 + ACC II as legislated), *CA-Aggressive* (exceeds SB 100, 100 % clean by 2040), *CA-Delayed* (partial SB 100); Ohio: *OH-Status-Quo* (current mix, no mandate), *OH-IRA-Accelerated* (federal IRA incentives), *OH-Stalled* (IRA repeal). The expander shows the case's documented targets (CAV 2075, STI 2075, BEV growth, low-carbon electricity growth) and a rationale. Press **"Apply policy case to scenario settings"** to snap the sliders below to that case's values; the sliders remain individually editable afterward.

**The six scenario-setting sliders.** These are the primary mitigation levers. Each carries a help tooltip with provenance (e.g. `[scenario assumption] AFDC 2024 …`).

| Slider | Range (v9) | Default (CA / OH) | Meaning |
|---|---|---|---|
| **CAV target fraction by 2075** (F23) | 0.00 – 0.95 | 0.45 / 0.25 | Share of the fleet that is a CAV by 2075. Reached by *linear* interpolation from the 2024 value, not exponential growth. |
| **STI coverage target by 2075** (F24) | 0.00 – 0.95 | 0.50 / 0.30 | Share of convertible intersections / corridors that are STI-equipped by 2075. |
| **Annual BEV-share growth** (F25) | 0.00 – 0.20 | 0.07 / 0.03 | Annual growth in the BEV share of the stock; largest near-term lever for fossil-heavy grids. |
| **Annual low-carbon electricity share growth** (F26) | 0.00 – 0.15 | 0.05 / 0.02 | Annual growth in the low-carbon electricity share; largest long-horizon lever. |
| **Hardware efficiency doubling time (years)** (F27) | 2.0 – 12.0 | 2.8 | Years for autonomy-hardware energy efficiency to double (Moore-law-style cohort decay `0.5^(elapsed / doubling)`). Smaller = faster improvement; largest *compounding* lever. The internal model still allows 1.0–20.0 for backward compatibility, but the v9 page narrows the slider to the post-Moore defensibility range. |
| **Hardware deployment lag (years)** (F29) | 0.0 – 5.0 | 2.0 (epistemic prior U(1, 4)) | Years between a frontier-hardware improvement and its installation in operating fleets (qualification, integration, procurement, fleet turnover). A *time shift* on when cohorts realise efficiency gains; does **not** change the F27 doubling time. |

**"Reset to state defaults" / "Reset to state defaults" button** — returns the six sliders to the current region's defaults and rebuilds the band.

> **Live behaviour:** changing any slider redraws the deterministic trajectory instantly. The default committed residual band does *not* re-centre on the new scenario; instead the page recomputes a fresh residual band (and scenario envelope) keyed on the full settings signature. There is no "Recompute" button — the band updates automatically. A short spinner ("Updating residual band for the selected settings…") appears while it recomputes.

### 6.4 Main panel — scope notes and warnings
The page title and a paragraph restate that this page is utility-phase only, that the residual band shows uncertainty *around the chosen scenario* while the scenario envelope *also varies the scenario*, and that the display horizon ends at 2075. If U.S. Average is selected a red error explains the quarantine; if the policy is not Baseline a yellow warning explains the band is not re-centred. A region-specific provenance note is shown (AFDC/EIA cross-checks, or the synthetic-midpoint caveat for U.S. Average).

### 6.5 Main panel — "Fixed data — measured 2024 starting values" (expander)
State-specific *measured* values that anchor the 2024 starting point: initial low-carbon electricity share (F01: 0.656 CA / 0.247 OH), initial BEV share (F02: 0.0410 CA / 0.0067 OH), initial vehicle stock (37.4 M CA / 10.4 M OH), and convertible intersections (380,400 CA / 171,000 OH). These are **not** scenario settings and **not** sources of residual uncertainty on this page. By default they are shown as a read-only source-of-truth table; ticking **"Advanced mode (editable)"** replaces the table with sliders for sensitivity checks only — values revert when you switch region.

### 6.6 Main panel — "Structural assumptions — model-design choices" (expander)
Discrete model-design decisions (not measurements, not uncertainty). Moving these rewrites the runtime config and changes the deterministic trajectory:

- **CAV level-mix template** (F18) — *L3-heavy (0.6, 0.3, 0.1)* | *Balanced (0.5, 0.33, 0.17, default)* | *L4-forward (0.33, 0.5, 0.17)* | *L5-forward (0.17, 0.33, 0.5)*. Applied as a Dirichlet mean shift on the L3/L4/L5 autonomy shares. L3-heavy understates the long-horizon ATS burden (peak ≈ 15 % below Balanced); L5-forward widens it by roughly 60 %.
- **STI level-mix template** (F19) — *Basic-heavy (default)* | *Balanced* | *Highly-automated-forward*. Mix of Basic / Semi-automated / Highly-automated coverage shares.
- **Vehicle service life (years)** (F22) — *10 | 12 (default) | 15*. Anchors the cohort-retirement loop (IHS Markit / S&P Global Mobility median ≈ 12 yr).
- **Fleet growth functional form** (F28) — *Linear (default, demographically bounded)* | *Constant 2024 level* (sets the annual fleet growth rate to zero).
- **Target ramp shape** — *Linear 2024 → 2075* (the only implemented option; logistic / delayed-onset would need a code extension).

### 6.7 Main panel — Figure A: ATS trajectory
The central chart. Annual *or* cumulative ATS energy and CO₂ from 2024 to 2075, with the uncertainty band around the trajectory.

**Controls above the chart:**
- **Metric** (radio): *Annual CO₂ emissions* | *Annual energy demand* | *Both (dual axis)* | *Cumulative CO₂ emissions* | *Cumulative energy demand*. Annual views plot per-year values from the active band. Cumulative views plot the running sum from 2024, computed by integrating *each Monte-Carlo run separately before percentiling* — summing per-year p95 values would overstate the cumulative tail. The "Both" view puts the secondary metric on a right-hand axis as a dash-dot line (no band, for readability).
- **Uncertainty object** (radio): *Residual* | *Scenario envelope*.
  - **Residual** = decision-focused. The scenario settings (F23–F27) and structural assumptions are *fixed at your chosen values*; the band reflects only the residual L1/L2 input ranges (plus the annual weather draw). Use it to answer "given my plan, how uncertain is the outcome?"
  - **Scenario envelope** = reviewer-facing predictive uncertainty. *In addition to* the residual ranges, the deployment targets (F23–F27) are themselves sampled over registry MEDIUM priors, so the band is wider. Use it for "the scenario itself is uncertain — how wide is the predictive spread?"
- **Monte Carlo runs** (slider, 20–200, step 20, default 80): the number of MC samples backing the band. Higher counts narrow the Monte-Carlo error in the band at the cost of compute time. The band updates automatically when you move it; there is no Recompute button.

**Metric cards (six):** *Monte Carlo runs* (sample count of the active band); *Band* (Residual or Scenario envelope); *Peak year* (first year of the local maximum in the median trajectory — shows "After 2075 (20XX)" if it falls outside the display window); *Turning year* (first year at or after the peak where the median has dropped to ≤ 50 % of the peak — "Not reached by 2075" or "After 2075 (20XX)" if applicable); *IB (τ = 1.5)* and *IB (τ = 0.5)* — see §7.4.

**The chart itself:** a shaded p05–p95 band, a p50 median line (solid when the live/envelope band is showing, dotted when only the committed bundle is showing), the **live deterministic trajectory** as a dark solid line (the run at the *currently selected* settings), an optional right-axis line for the "Both" view, and a dashed vertical line + annotation at the **interpretation boundary** (τ = 1.5); the region beyond the IB up to 2075 is lightly shaded to signal "scenario envelope, not a frequentist forecast interval". Energy is plotted in blue, emissions in red, with axes auto-scaled to TWh / Mt etc. as appropriate.

**Below the chart:**
- A caption that names the band kind, sample count, region, policy, and the IB convention; and a note that the band also includes the annual state weather-share draw (F32–F36).
- A green success line confirming the band updated for the current settings.
- **"How to read this page" expander** — three bullets distinguishing the deterministic trajectory, the residual band, and the (wider) scenario envelope.
- **"Peak-year implied unit burdens" expander** — a deterministic peak-year breakdown for the *current* settings: per-ECAV, per-ICECAV, and per-STI energy (kWh yr⁻¹) and totals (TWh yr⁻¹), cross-checked against the manuscript's Extended Data Table 2 baselines. Useful when a reviewer wants to check that a high peak isn't driven by an out-of-range per-unit number (expected magnitudes ≈ 170 W continuous per ECAV after hardware doubling compounds, a 1.6× factor on ICECAV, ≈ 2 kW continuous per STI asset).

### 6.8 Main panel — Figure B: Top residual-uncertainty drivers
A horizontal bar chart of the residual uncertainty that remains *after* the scenario settings are fixed and the structural assumptions are chosen. Each bar is `(p95 − p05) / p50` when *only that one parameter is sampled* and everything else is held fixed. Bars are coloured by layer (L1 teal = emission factors, L2 rust = load-model). A **Year** radio (2030 / 2050 / 2075) selects the snapshot. Three metric cards report the top residual driver at 2030, 2050, and 2075. Excluded by construction: the scenario settings (F23–F27), the structural assumptions (F18, F19, F22, F28), and the measured fixed data (F01, F02) — none of those are *residual* uncertainty. The caption is explicit that the top-ranked residual driver is *not* a new finding that displaces the known dominance of the scenario settings; it is the largest residual contributor *conditional on having already made the scenario and structural decisions*. To see uncertainty when the scenario itself is uncertain, switch Figure A to Scenario envelope.

### 6.9 Main panel — Figure C: Layer contribution summary
Grouped bars of `(p95 − p05) / p50` for each *layer* in isolation, at several years. By default only **L1** (emission factors) and **L2** (load model) are shown, because **L3** parameters are deployment scenario settings — they *define* the trajectory, they are not residual uncertainty. A checkbox, **"Include L3 for reference (conditional on target-setting)"**, adds the L3 bar so you can see how much wider the scenario envelope would be if targets were also treated as priors. The caption explains the L1/L2/L3 distinction.

### 6.10 Main panel — Scenario-setting leverage
A short narrative read-out: the dominant residual driver at 2030 and 2050 (from the Figure B data), followed by the leverage ranking of the five deployment settings for *reducing 2050 emissions*: (1) hardware-efficiency doubling time — largest compounding effect; (2) BEV growth rate — largest near-term effect for fossil-heavy grids; (3) low-carbon electricity growth — largest long-horizon effect; (4) CAV target — shapes total ATS demand; (5) STI target — modest direct effect, couples to the CAV–STI interaction. A **"What remains outside the residual band"** table is explicit that scenario-setting positions, structural assumptions, structural shocks, and missing life-cycle phases are *not* in the band, while the residual L1/L2 ranges *are* (and update automatically).

### 6.11 Main panel — State-conditioned subsystem decomposition over time
A stacked-area chart of the *same live deterministic run* that produced the Figure A trajectory, broken into nine series — ECAV / ICECAV / STI × Sensing / Computing / Communication — in TWh yr⁻¹, with the ATS total overlaid as a dashed line, through 2075. This is where you can watch the computing share of utility-phase energy decay over time as hardware doubling compounds.

### 6.12 Main panel — Factor specification
A quick reference, grouped to mirror the uncertainty-framework figure on the Overview page: **Input data** (F01, F02, vehicle stock, intersections, the STI Basic aggregation note); **State condition settings** (F32–F36); **ATS unit and subsystem demand factors** (F09–F11 ECAV sensing/computing/communication scale factors, F15–F17 STI scale factors, F20 ICECAV power overhead); **Fleet deployment settings** (F23–F29, plus F18/F19/F22/F28 and the ramp shape); **Utility-phase residual ranges** (F03 low-carbon CO₂ intensity, F04 fossil CO₂ intensity — region-specific, F05 gasoline CO₂ intensity). Each row gives the ID, short label, role in analysis, and value-or-range. A separate expander, **"One-time lifecycle inputs"**, points to the One-Time Energy page for production / logistics / end-of-life factors.

### 6.13 Main panel — Residual uncertainty ranges (the former "Block 4")
This is where you customise the priors that drive the live Monte-Carlo band. Each residual parameter has a selectbox with two settings:

- **Default** — the evidence-anchored range reported in the manuscript. These are the values that produce the default residual band. The published spec is shown in italics beneath the selector (e.g. `dist=triangular, low=0.02, mode=0.03, high=0.05` or `dist=lognormal, mean=1.0, sigma=0.20`).
- **Customized** — opens an inline editor with one number input per distribution parameter (triangular: low/mode/high; lognormal: mean/sigma; beta: mean/kappa; truncated_normal: mean/sd/min/max; dirichlet: alpha as a comma-separated list). The spec is validated live; an invalid spec shows a warning and the page falls back to the published prior until you fix it. Selecting *Customized* on any parameter flips the page-level **"All default ranges active"** badge to **No**.

The parameters are grouped in expanders: **Emission-factor ranges (F03, F04, F05)**; **ECAV load-model ranges (F09, F10, F11)** (expanded by default); **STI load-model ranges (F15, F16, F17)**; **ICECAV conversion range (F20)**; **State weather adjustment factors (F32–F36)**. Each parameter shows its physical meaning and a collapsible **Source** with the citation. Three metric cards summarise: *Default ranges active* (count), *Customized ranges active* (count), *All default ranges active* (Yes / No — "Yes" requires Baseline policy, a CA or OH region, the default or paper-safe bundle, and no customised ranges). A **"Reset all to default ranges"** button restores every residual parameter to its published prior and discards stashed custom specs.

**Non-residual parameters** — the scenario settings F23–F27 and F29, the structural assumptions F18/F19/F22/F28, and the fixed-data anchors F01/F02 — are held at their central values and do **not** appear in this section; they are controlled in the sidebar and the structural-assumptions expander respectively.

### 6.14 Main panel — Data sources and assumptions (full provenance)
A single expandable table listing every factor with its block/category, ID, short label, role in analysis, value-or-range, source, and rationale. Factor IDs in parentheses (`(stock)`, `(intersections)`, `(ramp)`) are derived configuration settings without an F-number.

---

## 7. Key concepts and glossary

### 7.1 Vehicle / infrastructure categories
- **CAV** — Connected Autonomous Vehicle (autonomy levels L3 / L4 / L5).
- **ECAV** — a battery-electric vehicle that is also a CAV (EV ∩ CAV). Autonomy energy is drawn from the grid.
- **ICECAV** — an internal-combustion vehicle that is also a CAV (ICE ∩ CAV). Autonomy energy is supplied via the alternator with a ~1.6× conversion-overhead power factor (F20).
- **STI** — Smart Traffic Infrastructure, with coverage tiers Basic / Semi-automated / Highly-automated. Energy reflects 24/7 LiDAR, radar, V2X, and edge compute at an equipped intersection or corridor segment.
- **ATS** — the Automated Road Transport System as a whole (ECAV + ICECAV + STI). "ATS energy"/"ATS emissions" are the fleet-level totals plotted in Figure A.
- **Subsystems** — every AV unit's energy is decomposed into **Sensing**, **Computing**, and **Communication**. Propulsion is reported separately on the Utility Phase page.

### 7.2 Layers (used in Figures B and C)
- **L1** — emission-factor parameters (F03 low-carbon CO₂ intensity, F04 fossil CO₂ intensity, F05 gasoline CO₂ intensity).
- **L2** — load-model parameters (the ECAV/STI sensing/computing/communication scale factors F09–F17 and the ICECAV overhead F20).
- **L3** — deployment scenario-setting parameters (the CAV/STI targets and the growth rates F23–F27). In the dashboard's framing L3 *defines the trajectory* and is therefore **not** counted as residual uncertainty; it only enters the *scenario envelope*.

### 7.3 Residual band vs scenario envelope
- **Residual band** — p05–p95 from a Monte-Carlo pass that samples only the residual (L1 + L2) input ranges plus the annual weather draw, with all scenario settings and structural assumptions *fixed at the currently selected values*. Answers "given my plan, how uncertain is the outcome?"
- **Scenario envelope** — p05–p95 from a Monte-Carlo pass that *also* samples the deployment targets (F23–F27) over registry MEDIUM priors. Always wider than the residual band. Answers "the scenario itself is uncertain — what is the predictive spread?"
- **Default / committed bundle** — a pre-computed Monte-Carlo bundle (on disk) used to populate Figure A before a live band exists. Centred on the *baseline* policy and the region defaults; it is *not* re-centred when you change scenario settings — the page computes a fresh live band instead.

### 7.4 Interpretation boundary (IB)
The first year after 2027 where the band's relative width `(p95 − p05) / p50` exceeds a threshold τ. Beyond the IB, the band is best read as a *scenario envelope* rather than a frequentist forecast interval. The dashboard reports two side by side:
- **τ = 1.5** — the dashboard / manuscript default convention.
- **τ = 0.5** — a tighter, IPCC-AR6-style threshold; quote this if you need a stricter confidence-interval claim.
On Figure A the τ = 1.5 boundary is drawn as a dashed vertical line with the year annotated, and the region from the IB to 2075 is lightly shaded.

### 7.5 Peak year and turning year
- **Peak year** — the first year of the local maximum in the *median* trajectory.
- **Turning year** — the first year at or after the peak where the median has fallen to ≤ 50 % of the peak value. If the median is still rising or hasn't halved by 2075, the card reads "Not reached by 2075" (the metric is still computed on the full internal 2024–2092 simulation, so "After 2075 (20XX)" can appear).

### 7.6 Deterministic vs Monte-Carlo
- **Deterministic trajectory** — a single simulator run at the currently selected settings, with every distribution collapsed to its central value. This is the dark solid line on Figure A and the basis of the subsystem-decomposition chart and the peak-year diagnostics.
- **Monte-Carlo band** — `n` runs (the "Monte Carlo runs" slider) with the residual ranges (and, for the envelope, the targets) sampled; percentiled per year (or per cumulative run for cumulative metrics).

### 7.7 Factor IDs (F-numbers)
Every uncertain or structural quantity in the model has a stable `Fxx` label so it can be cross-referenced between the dashboard, the figures, the manuscript, and the parameter registry. The ones most relevant to interaction: **F18/F19** level-mix templates, **F22** service life, **F23/F24** CAV/STI 2075 targets, **F25** BEV growth, **F26** low-carbon electricity growth, **F27** hardware doubling time, **F28** fleet-growth form, **F29** hardware deployment lag, **F32–F35** annual weather-share simplex + concentration, **F36** weather-to-grid CO₂ sensitivity, **F03/F04/F05** emission-factor ranges, **F09–F17** subsystem load-model ranges, **F20** ICECAV overhead. (F06–F08 and F12–F14 are hidden as duplicates of per-level aggregates.)

---

## 8. Practical workflows

**"What if California pushes BEV adoption and a clean grid harder?"**
Scenario Explorer → sidebar: Region = California, Policy = Baseline → either apply the *CA-Aggressive* policy case or raise *Annual BEV-share growth* and *Annual low-carbon electricity share growth* → watch the dark deterministic line on Figure A drop; the residual band rebuilds automatically. Compare *Peak year* and *Turning year* cards before/after.

**"How robust is that conclusion to parameter uncertainty?"**
Keep Figure A on *Residual*; raise *Monte Carlo runs* to 160–200 for a tighter band; look at the p05–p95 spread and the IB (τ = 1.5 and τ = 0.5) cards. Then check Figure B to see which residual parameter drives the remaining spread.

**"And if the scenario itself is uncertain?"**
Switch Figure A's *Uncertainty object* to *Scenario envelope* — the band widens to include uncertainty in the deployment targets; the IB typically moves earlier.

**"Where does the energy actually go, and when does compute stop dominating?"**
Look at the *State-conditioned subsystem decomposition over time* chart on the Scenario Explorer (fleet scale, over time) and the donuts on the One-Time Energy page (embodied vs operational at a point in time).

**"Is my custom prior plausible?"**
Residual uncertainty ranges section → set the parameter to *Customized*, edit the spec; an invalid spec is flagged and ignored until corrected. The "All default ranges active" badge will read **No** while any custom spec is active.

**"Reproduce the manuscript exactly."**
Region ∈ {California, Ohio}, Policy = Baseline, Default residual band = Default (or "Alternative reproduction" for the paper-safe bundle), State weather profile = Auto, all residual ranges = Default, all structural assumptions at their defaults (Balanced CAV mix / Basic-heavy STI mix / 12-yr service life / Linear fleet growth). The "All default ranges active = Yes" badge confirms you are in a paper-matching configuration.

---

## 9. Caveats to keep in mind

- **U.S. Average is exploratory only.** Its consumption tables diverge 10–30× from CA/OH; it is hidden from the region list unless explicitly enabled, and every U.S. Average view carries a red warning.
- **Non-baseline policies do not re-centre the committed band.** When Policy ≠ Baseline, the *committed* bundle still reflects Baseline; the page computes a fresh live band, but the "default residual band" fallback shown before the live band finishes is Baseline-centred.
- **Cumulative views read a per-run cumulative band, not the annual MC band.** This is deliberate: summing per-year p95 values overstates the cumulative tail because runs are not perfectly rank-correlated across years.
- **One-Time Energy page sliders were removed in v9.** The page shows the manuscript baseline; the equivalent assumptions are preserved read-only at the bottom of that page, and one-time uncertainty is documented as input ranges there.
- **Display horizon = 2075.** Charts stop at 2075; some diagnostics computed on the internal 2092 horizon will say "After 2075 (20XX)".
- **Operational-phase boundary on the Scenario Explorer / Utility pages.** Production, logistics, and end-of-life are *not* included in those numbers — they live on the One-Time Energy page and are never auto-summed with the operational figures.

---

*Document version: v9 dashboard guide. Source of truth for behaviour: `v9_streamlit_app/streamlit_app.py`, `pages/01_One_Time_Energy.py`, `pages/02_Utility_Phase_Energy.py`, `pages/03_Scenario_Explorer.py`, `core.py`, `weather_module.py`, `scenario_definitions.py`, and the configs under `v9_streamlit_app/configs/`.*
