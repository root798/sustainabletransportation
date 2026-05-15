# CLEAR-ATS Dashboard (v9) — User Guide

*Clean Energy Automated Road Transport System — an interactive scenario explorer for the energy demand and CO₂ emissions of road transport, 2024 onward.*

A detailed, onboarding-friendly guide: a researcher or collaborator who has never seen this project can install it, launch it, navigate every screen, and reproduce the manuscript results from this document alone. The companion file `USER_GUIDE.md` is the original, more terse reference; the technical content is identical.

<!-- VISUAL PLACEHOLDER: hero screenshot of the Scenario Explorer (Figure A + sidebar). -->

## Contents

0. [Quick start](#0-quick-start)
1. [What CLEAR-ATS is — purpose and scope](#1-what-clear-ats-is--purpose-and-scope)
2. [Installation](#2-installation)
3. [Launching the dashboard](#3-launching-the-dashboard)
4. [Repository layout — what the app needs on disk](#4-repository-layout--what-the-app-needs-on-disk)
5. [Overview page](#5-overview-page)
6. [One-Time Energy page](#6-one-time-energy-page)
7. [Utility Phase Energy page](#7-utility-phase-energy-page)
8. [Scenario Explorer page — the main interactive screen](#8-scenario-explorer-page--the-main-interactive-screen)
9. [Key concepts and glossary](#9-key-concepts-and-glossary)
10. [Practical workflows](#10-practical-workflows)
11. [Reproducing the manuscript exactly](#11-reproducing-the-manuscript-exactly)
12. [Common errors and troubleshooting](#12-common-errors-and-troubleshooting)
13. [Caveats to keep in mind](#13-caveats-to-keep-in-mind)
14. [Where the numbers come from (source-of-truth files)](#14-where-the-numbers-come-from-source-of-truth-files)

---

## 0. Quick start

> Needs **Python 3.10+** and a copy of the **whole** `CLEAR_ATS` repository — not just `v9_streamlit_app/` (it reads sibling and parent folders; see [§4](#4-repository-layout--what-the-app-needs-on-disk)).

```bash
cd /path/to/CLEAR_ATS                              # repo root: contains v9_streamlit_app/, v4_streamlit_app/, scenarios/, configs/, results/
python3 -m venv .venv && source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install -r v9_streamlit_app/requirements.txt
streamlit run v9_streamlit_app/streamlit_app.py
```

**Expected output:** the terminal prints `Local URL: http://localhost:8501` and that page opens in your browser. Use the **left-sidebar page list** to switch screens; `Ctrl-C` to stop.

> ⚠️ **Run from the repository root.** A `ModuleNotFoundError` / `FileNotFoundError` on launch almost always means you launched from the wrong place — see [§12](#12-common-errors-and-troubleshooting).

### 0.1 Your first five minutes

1. Read the **Overview** page (loads first) — the three-column key explains the other pages.
2. Open the **Scenario Explorer** (sidebar → last page).
3. Leave Region = California, Policy = Baseline, Default residual band = Default. Figure A draws a deterministic trajectory immediately, then fills in a live uncertainty band.
4. Move the *Annual BEV-share growth* slider up — watch the trajectory drop and the *Peak year* / *Turning year* cards change.
5. Toggle *Uncertainty object* from *Residual* to *Scenario envelope* — the band widens, because it now also accounts for the deployment targets being uncertain.

> The dashboard re-runs the model on every interaction — there is **no "Recompute" button**.

---

## 1. What CLEAR-ATS is — purpose and scope

**In one sentence:** a scenario-conditioned simulator — you choose policy and deployment assumptions, it projects road-transport **energy demand (kWh yr⁻¹)** and **CO₂ emissions (kg CO₂ yr⁻¹)** from 2024 forward, focused on how **Connected Autonomous Vehicles (CAVs)** and **Smart Traffic Infrastructure (STI)** reshape fleet-level energy use — and how confident the answer is over a long horizon.

You don't need the simulation code: the dashboard *is* the front end. Behind it, a year-by-year simulator (`footprint_model.py` / `core.py`) re-runs whenever you change a control, with a Monte-Carlo uncertainty band on top. (Acronyms: [§9.1](#91-vehicle--infrastructure-categories).)

<!-- VISUAL PLACEHOLDER: a "sidebar settings → simulator → deterministic line + Monte-Carlo band → metric cards" pipeline diagram. -->

| Screen | The question it answers | Interactive? |
|---|---|---|
| **Overview** | What is CLEAR-ATS, and how is its uncertainty structured? | No (static) |
| **One-Time Energy** | How much energy is embodied in *producing, shipping, and retiring* the autonomy hardware? | A view toggle on one figure |
| **Utility Phase Energy** | How much energy does *one* vehicle or one roadside asset consume *per year*, split between propulsion and the AV subsystems? | Propulsion inputs + rate-region selector |
| **Scenario Explorer** | At *state scale*, how do annual and cumulative ATS energy and CO₂ evolve under chosen deployment, electrification, grid, weather, and hardware-efficiency settings — and how wide is the residual uncertainty? | **Yes — the main screen** |

### Three rules that apply on every screen

1. **One life-cycle phase per page.** Scenario Explorer + Utility Phase report the *operational (utility) phase only*; One-Time Energy reports the *production + logistics + end-of-life* phase separately. **The two are never summed for you** — cross-phase reasoning is the reader's job; the One-Time page provides an "inversion panel" to support it.
2. **California and Ohio are real; U.S. Average is not.** CA and OH are modelled at full quantitative resolution. **U.S. Average** is a synthetic CA/OH midpoint and is *quarantined* — its sensing and communication consumption cells diverge 10–30× from the two real states, so any U.S. Average output is exploratory only, flagged in red wherever it can be selected, and hidden from the region list unless a quarantine override is enabled.
3. **Charts stop at 2075.** The simulator runs internally to 2092, but every chart is capped at 2075 and predictive validity is not claimed beyond it. Some diagnostics (peak year, turning year, interpretation boundary) are still computed on the full internal horizon and will say "After 2075 (20XX)" when the event falls outside the display window.

---

## 2. Installation

### 2.1 Requirements

| Item | Detail |
|---|---|
| **OS** | Linux, macOS, or Windows. Examples use a Unix shell; the only Windows difference is the venv activation command (noted inline). |
| **Python** | **3.10 or newer** (tested on 3.10 and 3.13). Check: `python3 --version`. |
| **Dependencies** | `streamlit ≥ 1.32` (the web app), `pandas ≥ 2.0` (tables), `numpy ≥ 1.24` (numerics + MC sampling), `plotly ≥ 5.18` (charts), `matplotlib ≥ 3.7` (static figures + shared palette). Installed by `requirements.txt`. |
| **The full repo** | `v9_streamlit_app/` plus sibling `v4_streamlit_app/` and repo-root `scenarios/`, `configs/`, `results/`. The "repository root" is the directory that directly contains all of those — *not* the nested `CLEAR_ATS/CLEAR_ATS/` sub-folder, which is an older standalone copy. |
| **Disk** | ~1–2 GB if the large `results/*_mc_runs.csv` files are present; the dashboard itself only needs the much smaller `*_quantiles.csv` bundles, which ship with the repo. |
| **Internet** | Only for `pip install`; the dashboard runs fully offline afterward. |

### 2.2 Steps

```bash
# 1. Open a terminal at the repo root
cd /path/to/CLEAR_ATS
ls                                       # expect: v9_streamlit_app  v4_streamlit_app  scenarios  configs  results  ...

# 2. Create + activate an isolated environment (keeps versions from clashing)
python3 -m venv .venv
source .venv/bin/activate                # Windows (PowerShell): .venv\Scripts\Activate.ps1   |   cmd: .venv\Scripts\activate.bat
                                         # prompt should now show (.venv)

# 3. Install dependencies
pip install --upgrade pip
pip install -r v9_streamlit_app/requirements.txt
# Expected: "Successfully installed streamlit-… pandas-… numpy-… plotly-… matplotlib-…", no errors.

# 4. (Optional) pre-flight check — catches UI-breaking regressions; does NOT start a server
python scripts/validate_v9_dashboard_runtime.py
# Expected: a series of [ OK ]/[FAIL] lines ending in a pass summary.

# 5. Launch (see §3)
streamlit run v9_streamlit_app/streamlit_app.py
```

> **Each new session:** re-activate first — `cd /path/to/CLEAR_ATS && source .venv/bin/activate` — then launch.

---

## 3. Launching the dashboard

From the **repository root**, with the venv active:

```bash
streamlit run v9_streamlit_app/streamlit_app.py
```

- Streamlit starts a local web server and prints a `Local URL: http://localhost:8501` (plus a Network URL). Your browser opens it automatically; if not, paste the Local URL manually.
- The **Overview** page loads first. Use the **left-sidebar page list** for the other three. The **Scenario Explorer** opens with the sidebar expanded (many controls); the others open with it collapsed.
- Flags: `--server.port 8502` (different port), `--server.headless true` (don't auto-open a browser, e.g. on a remote machine).
- Stop with `Ctrl-C` in the terminal.

> Launch with the path `v9_streamlit_app/streamlit_app.py` exactly as written; the app resolves its sibling/parent folders relative to its own location. Running it from inside `v9_streamlit_app/` also works — copying that folder out on its own does not (see [§4](#4-repository-layout--what-the-app-needs-on-disk)).

---

## 4. Repository layout — what the app needs on disk

The v9 dashboard is **not** a self-contained folder. The minimal picture of what must be present:

```
CLEAR_ATS/                                  ← the "repository root" — run all commands from here
├── v9_streamlit_app/                        ← the active v9 dashboard (this folder)
│   ├── streamlit_app.py                      ← Overview page + Streamlit entry point — you launch THIS
│   ├── requirements.txt
│   ├── core.py                               ← v9 simulation/UI bridge (re-exports v4 helpers + v8/v9 additions)
│   ├── weather_module.py                     ← annual weather-share Dirichlet (factors F32–F36)
│   ├── one_time_data.py                      ← component inventory and one-time-energy tables
│   ├── scenario_definitions.py               ← named policy cases (CA-Committed, OH-IRA-Accelerated, …)
│   ├── figure_style.py                       ← shared Nature-family palette / chart defaults
│   ├── pages/                                ← 01_One_Time_Energy.py, 02_Utility_Phase_Energy.py, 03_Scenario_Explorer.py
│   ├── utils/                                ← small helpers (factor tables, chart guards)
│   ├── configs/                              ← policy_scenarios.json, mitigation_defaults.json, parameter_labels.json, weather_v8/
│   └── assets/clear_ats_uncertainty_figure_v30.png   ← the schematic shown on the Overview page
│
├── v4_streamlit_app/core.py                  ← REQUIRED: v9's core.py imports tested helpers from here
├── scenarios/{california,ohio,us_average}/scenario.json   ← canonical regional model parameters
├── configs/{california,ohio,us_average}.json             ← legacy fallback for the above (also read)
└── results/                                  ← pre-computed Monte-Carlo bundles the dashboard displays
    └── {region}__policy-baseline__bundle-{default,paper-safe}_quantiles.csv   (+ _mc_runs.csv, _metrics.csv)
```

- **`v4_streamlit_app/`** must sit alongside `v9_streamlit_app/` — v9's `core.py` loads `v4_streamlit_app/core.py` at import time. Missing → the dashboard won't start.
- **`scenarios/`** (preferred) / **`configs/`** (legacy fallback) hold the regional model parameters: 2024 starting values, growth rates, consumption rates, emission factors. The app tries `scenarios/{region}/scenario.json` first, then `configs/{region}.json`.
- **`results/…_quantiles.csv`** are the *committed Monte-Carlo bundles*. They ship with the repo and seed Figure A *before* a live band is computed for your settings. `"Default"` ↔ `bundle-default_quantiles.csv`; `"Alternative reproduction (paper-safe)"` ↔ `bundle-paper-safe_quantiles.csv`. You do **not** need to regenerate these to use the dashboard ([§11](#11-reproducing-the-manuscript-exactly)). The dashboard never *writes* to `results/`; live bands are recomputed in memory.

---

## 5. Overview page

A static landing page — no interactive controls — that orients you and links the rest together. It contains:

- A one-paragraph description of the framework.
- The **uncertainty-structure figure** (`v9_streamlit_app/assets/clear_ats_uncertainty_figure_v30.png`) — a schematic tracing uncertainty *from* input data and state conditions → unit-level demand → fleet-scale propagation → resulting energy and CO₂ ranges. The factor-reference tables on the Scenario Explorer are grouped to mirror it, so look at it once. *(If the PNG is missing, the page shows an info box instead of crashing.)*
- A three-column **"How to read this dashboard"** key summarising the other three pages.

---

## 6. One-Time Energy page

**Answers:** *"How much energy does it take to build, ship, and eventually retire the autonomy hardware itself?"* — the production + logistics embodied energy, plus a separate end-of-life accounting. This is the half of the life cycle the Scenario Explorer deliberately leaves out; comparing the two halves is the point of the inversion panel ([§6.5](#65-why-the-life-cycle-optimisation-must-span-both-phases-inversion-panel)). Every figure traces to the manuscript (Figure 3a, 3b, Extended Data Tables 3–4, Table 2).

> In v9 the interactive sliders earlier versions placed at the top of this page were removed. The page shows the manuscript baseline; the equivalent assumptions are preserved read-only at the bottom ([§6.7](#67-end-page-reference-material-collapsed)).

### 6.1 Figure A — component-level one-time energy ranking

Horizontal bars of per-unit embodied energy (kWh) for **every** ATS component, ranked low-to-high.

- Coloured by subsystem: **sensing (blue), computing (gray), communication (red)**.
- ● on the y-label = a CAV component; ▲ = an STI component.
- *Caption takeaway:* the high-performance computing unit (654.32 kWh) and static high-power LiDAR (607.58 kWh) have the largest *per-unit* energy — but sensors are deployed in far greater *numbers*, so the sensing subsystem dominates the *total* (see Figure B).

### 6.2 Figure B — unit one-time energy with subsystem decomposition

Horizontal **stacked** bars, one per unit type (STI Highly, CAV L5, STI Semi, CAV L4, CAV L3 Large/Medium/Small, STI Basic).

- Each segment = a subsystem; in-bar label = that subsystem's % of the unit total; the number at the right = the unit total in kWh (production + logistics only).
- A **"live vs manuscript comparison"** table flags any drift > 1 % vs the manuscript's Figure 3b value. One row, **STI Basic**, is a *documented manuscript inconsistency* (component sum 2,747.36 kWh vs alternative aggregation 2,139.77 kWh) — labelled "manuscript gap", not a bug.
- *Caption reports:* live sensing share for a Level 5 CAV (~88–94 %) and a Highly-Automated STI (~84 %), and the L3-Small → L5 energy multiplier (~3.5×).

### 6.3 Figure C — marginal components across autonomy levels

How many *additional* hardware items autonomy adds, relative to a conventional vehicle or a traditional intersection. CAV units (L3 Small/Medium/Large, L4, L5) on the left of the x-axis; STI tiers (Basic, Semi, Highly) on the right, split by a dotted line and group headers.

- **View toggle** (radio): *Component breakdown (default)* — stacked bars, one segment per component, total on top of each stack — or *Total counts only* — one bar per unit, CAV blue, STI green.
- **Per-level component inventory expander** — the full per-level, per-component count matrix (Extended Data Tables 3 + 4) with a **Download component inventory (CSV)** button.
- *Caption explains* the non-monotonic L3 Small/Medium/Large total counts (L3 Small uses 12 sonar to compensate for missing LiDAR; L3 Large eliminates sonar entirely) and contrasts it with the energy-weighted view in Figure B.

### 6.4 Live derived metrics

Four metric cards, computed from a fixed **representative fleet** (10 × L3 Small + 5 × L3 Medium + 2 × L3 Large + 1 × L4 + 1 × L5 CAV, plus 5 × Basic + 2 × Semi + 1 × Highly STI — not a regional projection, just a fleet exercising every unit type):

- **Production + logistics (representative fleet)** — MWh.
- **Sensing share (fleet-weighted)** — %; the production-side analogue of the manuscript's 94 % CAV-L5 claim.
- **L3 Small → L5 multiplier** — ≈ 3.5×.
- **End-of-life energy savings (fleet)** — MWh, with a `−X % of production` delta. Expander **"How EoL savings are calculated"** gives `E_saved_per_unit = baseline_kWh × α × (1 − r)` (α = sensing refurbishment rate, baseline 0.70; r = refurbishment energy ratio, baseline 0.25, per manuscript §4.1.4) and the current numerics, including what the not-yet-wired failure fraction φ would change.

### 6.5 "Why the life-cycle optimisation must span both phases" (inversion panel)

**The point:** the subsystem that dominates *embodied* energy (sensing) is not the one that dominates *operational* energy (computing) — so optimising one phase alone misses the other.

- **Four cards:** L5 production + logistics — 9,237 kWh (Table 2); L5 annual utility energy — manuscript §2.1.1; L5 annual utility energy (live, California) — from a 1-vehicle pure-L5 fleet through the simulator's `_calculate_power`, with a drift-vs-manuscript delta; L5 cumulative utility over 12 years.
- **Two donuts:** *L5 CAV production + logistics share* — live; sensing-dominated. *Utility-phase subsystem share* — the manuscript value, computing-dominated at ≈ 98 % pre-2040 (the Scenario Explorer shows this decaying toward ~23 % at 2075 California as hardware doubling compounds).

### 6.6 End-of-life leverage (tornado chart)

How far each end-of-life *design action* moves the representative-fleet one-time energy when pushed to its lower/upper bound while the others stay at default.

- **Rows:** sensing manufacturing-efficiency improvement (0 → 60 %); sensing refurbishment rate α (0 → 100 %); sensor service-life extension (12 → 20 yr, which amortises production energy by 12/(12+N)); computing refurbishment adoption (0 → 100 %).
- **Reading it:** **green bars reduce** the burden, **red bars raise** it. Bars below 0.5 % magnitude are unlabelled; a bound that produces no change (e.g. computing refurbishment at its lower bound) is *omitted* rather than drawn as a fake zero.
- Expander **"How the bounds are computed"** gives the exact definitions, the lifetime-extension mechanism, and why computing refurbishment has small leverage (computing ≈ 6 % of the one-time burden).

### 6.7 End-page reference material (collapsed)

- **Component inventory and one-time assumptions** — the Figure 3a per-component energy table, the wide per-unit-type count table, source citations, and a structural-assumptions table (manufacturing region, logistics model, refurbishment energy ratio, EoL failure fraction φ, computing obsolescence window, sensor refurbishment rate α, sensor service life), each tagged with its role.
- **Data uncertainty ranges for one-time energy** — three tables (Production / Logistics / End-of-life): factor ID, name, distribution or range, affected quantity, role, source. These are *documented input ranges* — not user-controllable here, not future-trajectory uncertainties.
- **Data consistency note** — a table cross-checking six manuscript claims against the live component-sum values ("match" or "alternative aggregation").

> **Expected output:** Figures A/B/C; four metric cards; the inversion panel with two donuts; the tornado chart; the three collapsed reference expanders. Nothing changes unless you toggle the Figure C radio or open an expander — no sliders on this page.

---

## 7. Utility Phase Energy page

**Answers:** *"How much energy does one vehicle or one roadside asset use per year while operating — and how is that split between propulsion and the AV subsystems?"* It isolates the per-unit picture; the Scenario Explorer scales it up to a state and lets it evolve over time.

### 7.1 Controls (top of page)

- **AV-subsystem rate region (config file)** — selectbox CA / OH / U.S. Average. AV subsystem energy per autonomy level is read from `configs/<region>.json` (`consumption_rates.ecav_power`, `sti_power`, `icecav_power_factor`). The propulsion baselines below are US-averages and do **not** depend on this.
- **ICE propulsion (kWh / yr)** — editable, default 14,200 (FHWA 11,500 mi yr⁻¹ ÷ EPA fleet-avg 27.3 mpg → 421 gal yr⁻¹ × 33.7 kWh gal⁻¹ LHV).
- **BEV propulsion (kWh / yr)** — editable, default 3,565 (11,500 mi yr⁻¹ × EPA fleet-avg 0.31 kWh mi⁻¹).

### 7.2 Figure 1 — annual running energy, per vehicle

Horizontal stacked bars — **Propulsion + Computing + Sensing + Communication** — for six unit types (BEV / ICE × L5 / L4 / L3), ordered least-to-most automation-heavy, total (MWh yr⁻¹) annotated at each bar end. Colours: propulsion gray, computing blue, sensing green, communication red. *Caption reading guide:* for an ICE vehicle propulsion dominates even at L5; for a BEV at L5 the AV subsystem (especially onboard computing) is comparable to propulsion — electrification changes the *structure* of the burden, not its existence.

### 7.3 Figure 2 — AV subsystem breakdown (excluding propulsion)

Two side-by-side stacked bars, same colours: **CAV units** (ECAV L3/L4/L5 and ICECAV L3/L4/L5 — ICECAV applies the ~1.6× `icecav_power_factor` for ICE conversion overhead) and **STI levels** (Basic / Semi / Highly), each with its per-unit total annotated.

### 7.4 "Reading this page"

On-screen bullets: propulsion dominates total vehicle energy; AV-system share rises with autonomy (~4× L3→L5, driven by compute); within the AV subsystem computing dominates, sensing is second, communication smallest; electrification makes the AV subsystem a first-class decarbonisation lever for BEVs.

### 7.5 Utility-phase uncertainty ranges (read-only)

Tables grouping the relevant *residual* factors (ECAV subsystem load factors, STI subsystem load factors, ICECAV conversion/overhead factor): factor ID, name, layer/class, distribution/range, affected quantity, role. A further table collapses the state weather adjustment factors **F32–F36** into one row per region (clear/cloudy/adverse share centroid, the Dirichlet concentration κ, the grid-side CO₂ weather sensitivity). These document residual input uncertainty; the *live propagation* across the fleet happens on the Scenario Explorer.

> **Expected output:** the two propulsion inputs + the rate-region selectbox; Figure 1; Figure 2; the "Reading this page" bullets; the read-only uncertainty tables. Editing a propulsion number updates Figure 1 immediately; changing the rate region updates the AV-subsystem segments.

---

## 8. Scenario Explorer page — the main interactive screen

<!-- VISUAL PLACEHOLDER: an annotated screenshot — sidebar controls and Figure A's metric cards labelled. The single most useful image in this guide. -->

### 8.0 How this page works (read this first)

You pick a future scenario in the sidebar; the page re-runs the simulator and shows the resulting state-scale energy and CO₂ trajectory through 2075, wrapped in an uncertainty band. Two things are drawn on every interaction:

1. **Deterministic trajectory** — one simulator run at exactly your current settings, every uncertain quantity collapsed to its central value. The dark solid line; appears *immediately*.
2. **Monte-Carlo uncertainty band** — many runs with the uncertain inputs sampled, summarised as a p05–p95 ribbon around a p50 median. Rebuilt *automatically* a moment later (a short "Updating residual band…" spinner shows while it computes). **There is no "Recompute" button** — and the committed bundle is *not* re-centred on your new scenario; the page computes a fresh live band keyed on the full settings signature.

**First-time recipe:** leave Region = California, Policy = Baseline, bundle = Default → look at Figure A → move one of the six sliders → watch the deterministic line move and the band rebuild → compare the *Peak year* / *Turning year* cards before/after.

**Layout, top to bottom:** *sidebar* — scope (region / policy / bundle) → state weather profile → scenario settings (policy-case picker + six sliders). *Main panel* — scope notes & warnings → "Fixed data" expander → "Structural assumptions" expander → Figure A (trajectory) → Figure B (top residual drivers) → Figure C (layer contributions) → scenario-setting leverage → subsystem decomposition over time → factor specification → residual-uncertainty-range controls → full provenance.

---

### 8.1 Sidebar — Scope

Sets *what* you're modelling, before any scenario lever. Every control here re-runs the simulator and rebuilds the band ([§8.0](#80-how-this-page-works-read-this-first)).

| Control | Options | What it does |
|---|---|---|
| **Region** | California, Ohio (U.S. Average only if the quarantine override is on) | Picks the regional config. Switching resets *region-dependent* state to that region's defaults (mitigation sliders, fixed data, residual-range selectors, custom specs); *region-invariant* structural choices (level-mix templates, service life, fleet-growth form) are preserved. |
| **Policy** | Baseline, Aggressive, Conservative | Baseline = regional defaults. *Aggressive* / *Conservative* apply a documented "deep-merge patch" on top of the base config — only the listed fields change. Choosing anything but Baseline raises a yellow warning that the committed fallback band stays Baseline-centred. |
| **Default residual band** | Default, Alternative reproduction ("paper-safe") | Which committed bundle backs Figure A *before* a live band exists. "Default" = the main evidence-anchored bundle (`results/{region}__policy-baseline__bundle-default_quantiles.csv`); "Alternative reproduction" = the paper-safe bundle (`…bundle-paper-safe_quantiles.csv`), kept for comparison. |

---

### 8.2 Sidebar — State weather profile (expander, collapsed by default)

**Answers:** *"How much does normal year-to-year weather variation move the numbers?"* Cloudy / adverse-weather years make sensors and compute work a little harder and shift the grid's emissions slightly. **Intuition:** each year the model picks a *clear / cloudy / adverse* day-share mix at random, clustered around a state target; a concentration knob, κ, controls how tightly (bigger κ → less year-to-year wobble). Mathematically a *Dirichlet distribution* over the three-way share simplex; factors **F32–F36**.

Two modes (radio):

- **Auto (state default)** — read-only, uses the state climatology centroid + concentration: California `(clear 0.61, cloudy 0.25, adverse 0.14)`, κ = 120; Ohio `(0.34, 0.39, 0.27)`, κ = 96. A caption shows the active values.
- **Custom** — three number inputs (Clear / Cloudy / Adverse, 0–1, auto-renormalised to sum to 1) set the annual weather-share *target*; an optional checkbox **"Expose concentration κ"** reveals a κ input (10–400). Switching to Custom flips the page-level "All default ranges active" status to **No**.

**Downstream — two effects:** (a) reweights subsystem energy via per-level adverse-weather utility tables for CAV L3/L4/L5 and STI Basic/Semi/Highly (communication stays flat where the source table reports no weather sensitivity); (b) scales electricity-side CO₂ by `1 + γ_cloudy·Δf_cloudy + γ_adverse·Δf_adverse`, state-specific γ — CA: 0.10 / 0.25; OH: 0.06 / 0.15.

---

### 8.3 Sidebar — Scenario settings

This is where you describe the future you want to test.

**Policy case (expander) — pick a documented pathway.** For the selected region: California — *CA-Committed* (SB 100 + ACC II as legislated), *CA-Aggressive* (exceeds SB 100, 100 % clean by 2040), *CA-Delayed* (partial SB 100); Ohio — *OH-Status-Quo* (current mix, no mandate), *OH-IRA-Accelerated* (federal IRA incentives), *OH-Stalled* (IRA repeal). The expander shows the case's documented targets (CAV 2075, STI 2075, BEV growth, low-carbon electricity growth) and a rationale. **"Apply policy case to scenario settings"** snaps the sliders below to that case's values; they remain individually editable afterward.

**The six scenario-setting sliders — the primary mitigation levers.** Each carries a help tooltip with provenance (e.g. `[scenario assumption] AFDC 2024 …`).

| Slider | Range (v9) | Default (CA / OH) | Meaning |
|---|---|---|---|
| **CAV target fraction by 2075** (F23) | 0.00 – 0.95 | 0.45 / 0.25 | Share of the fleet that is a CAV by 2075. Reached by *linear* interpolation from the 2024 value, not exponential growth. |
| **STI coverage target by 2075** (F24) | 0.00 – 0.95 | 0.50 / 0.30 | Share of convertible intersections / corridors that are STI-equipped by 2075. |
| **Annual BEV-share growth** (F25) | 0.00 – 0.20 | 0.07 / 0.03 | Annual growth in the BEV share of the stock. Largest near-term lever for fossil-heavy grids. |
| **Annual low-carbon electricity share growth** (F26) | 0.00 – 0.15 | 0.05 / 0.02 | Annual growth in the low-carbon electricity share. Largest long-horizon lever. |
| **Hardware efficiency doubling time (years)** (F27) | 2.0 – 12.0 | 2.8 | Years for autonomy-hardware energy efficiency to double — Moore-law-style cohort decay `0.5^(elapsed / doubling)`. Smaller = faster improvement; largest *compounding* lever. (Internal model still allows 1.0–20.0 for backward compatibility; the v9 slider is narrowed to the post-Moore defensibility range.) |
| **Hardware deployment lag (years)** (F29) | 0.0 – 5.0 | 2.0 (epistemic prior U(1, 4)) | Years between a frontier-hardware improvement and its installation in operating fleets (qualification, integration, procurement, fleet turnover). A *time shift* on when cohorts realise efficiency gains; does **not** change the F27 doubling time. |

**"Reset to state defaults" button** — returns the six sliders to the current region's defaults.

---

### 8.4–8.6 Main panel — context blocks above Figure A

- **§8.4 Scope notes & warnings.** Restates: utility-phase only; the residual band shows uncertainty *around the chosen scenario* while the scenario envelope *also varies the scenario*; the display horizon ends at 2075. Conditional banners: U.S. Average → red quarantine error; Policy ≠ Baseline → yellow "band not re-centred" warning; a region-specific provenance note (AFDC/EIA cross-checks, or the synthetic-midpoint caveat).
- **§8.5 "Fixed data — measured 2024 starting values" (expander).** State-specific *measured* anchors — **not** scenario settings, **not** residual uncertainty: initial low-carbon electricity share (F01: 0.656 CA / 0.247 OH), initial BEV share (F02: 0.0410 CA / 0.0067 OH), initial vehicle stock (37.4 M CA / 10.4 M OH), convertible intersections (380,400 CA / 171,000 OH). Read-only by default; **"Advanced mode (editable)"** turns them into sliders for sensitivity checks only — values revert when you switch region.
- **§8.6 "Structural assumptions — model-design choices" (expander).** Discrete design decisions — not measurements, not uncertainty; changing one rewrites the runtime config and shifts the deterministic trajectory:
  - **CAV level-mix template** (F18) — *L3-heavy (0.6, 0.3, 0.1)* | *Balanced (0.5, 0.33, 0.17 — default)* | *L4-forward (0.33, 0.5, 0.17)* | *L5-forward (0.17, 0.33, 0.5)*. A Dirichlet mean shift on the L3/L4/L5 autonomy shares. *L3-heavy understates the long-horizon ATS burden (peak ≈ 15 % below Balanced); L5-forward widens it ≈ 60 %.*
  - **STI level-mix template** (F19) — *Basic-heavy (default)* | *Balanced* | *Highly-automated-forward*.
  - **Vehicle service life (years)** (F22) — *10 | 12 (default) | 15*. Anchors the cohort-retirement loop (IHS Markit / S&P Global Mobility median ≈ 12 yr).
  - **Fleet growth functional form** (F28) — *Linear (default, demographically bounded)* | *Constant 2024 level* (annual fleet growth rate = 0).
  - **Target ramp shape** — *Linear 2024 → 2075* (the only implemented option; logistic / delayed-onset would need a code extension).

---

### 8.7 Main panel — Figure A: the ATS trajectory

The central chart: annual *or* cumulative ATS energy and CO₂ from 2024 to 2075, with the uncertainty band around it.

**How to read it at a glance:** dark solid line = the deterministic run at your *current* settings · shaded ribbon = p05–p95, with a p50 median line through it (solid when a live/envelope band is showing, dotted when only the committed bundle is) · dashed vertical line = the interpretation boundary (τ = 1.5), with the region from there to 2075 lightly shaded to mean "read this as a scenario envelope, not a frequentist forecast interval" ([§9.4](#94-interpretation-boundary-ib)) · energy is blue, emissions red, axes auto-scaled to TWh / Mt etc.

**The three controls above the chart:**

- **Metric** (radio): *Annual CO₂ emissions* | *Annual energy demand* | *Both (dual axis)* | *Cumulative CO₂ emissions* | *Cumulative energy demand*. Annual views plot per-year values from the active band. Cumulative views plot the running sum from 2024, computed by integrating **each Monte-Carlo run separately before percentiling** — *intuition:* a single bad year doesn't repeat identically in every other year, so summing per-year p95 values would describe a worst case that can't occur and overstate the cumulative tail. *Both* puts the secondary metric on a right-hand axis as a dash-dot line, no band, for readability.
- **Uncertainty object** (radio): *Residual* | *Scenario envelope*. **Intuition first:** *Residual* answers **"given my plan, how uncertain is the outcome?"** — your scenario choices are fixed; only the residual L1/L2 priors plus the annual weather draw wobble. *Scenario envelope* answers **"the plan itself is uncertain — how wide is the predictive spread?"** — it *also* samples the deployment targets (F23–F27) over registry MEDIUM priors (the model's own medium-confidence prior ranges for those targets), so the band is wider. (Precise definitions: [§9.3](#93-residual-band-vs-scenario-envelope).)
- **Monte Carlo runs** (slider, 20–200, step 20, default 80). *Intuition:* more runs = a smoother, less jittery band (you're sampling the uncertain inputs more densely), at the cost of compute per rebuild. 60–100 for exploring; 160–200 only for a final read. Updates automatically.

**Six metric cards:** *Monte Carlo runs* (sample count of the active band) · *Band* (Residual / Scenario envelope) · *Peak year* (first year of the local maximum in the median trajectory — "After 2075 (20XX)" if outside the display window) · *Turning year* (first year at/after the peak where the median has dropped to ≤ 50 % of the peak — "Not reached by 2075" or "After 2075 (20XX)" if applicable) · *IB (τ = 1.5)* and *IB (τ = 0.5)* ([§9.4](#94-interpretation-boundary-ib)).

**Below the chart:** a caption naming the region, policy, IB convention, and the included annual weather-share draw (F32–F36) · a green success line confirming the band updated · **"How to read this page" expander** — restates the deterministic-line / residual-band / scenario-envelope distinction · **"Peak-year implied unit burdens" expander** — a deterministic peak-year breakdown for the *current* settings: per-ECAV, per-ICECAV, per-STI energy (kWh yr⁻¹) and totals (TWh yr⁻¹), cross-checked against the manuscript's Extended Data Table 2 baselines (expected magnitudes ≈ 170 W continuous per ECAV after hardware doubling compounds, a 1.6× factor on ICECAV, ≈ 2 kW continuous per STI asset). Useful for confirming a high peak isn't driven by an out-of-range per-unit number.

### 8.8 Main panel — Figure B: top residual-uncertainty drivers

**Answers:** *"I've committed to a plan and the structural assumptions. What's the biggest source of uncertainty that's left?"* A horizontal bar chart of residual uncertainty remaining *after* the scenario settings are fixed and the structural assumptions chosen. Each bar = `(p95 − p05) / p50` when **only that one parameter is sampled** and everything else is held fixed. Coloured by layer (**L1 teal = emission factors, L2 rust = load-model**). A **Year** radio (2030 / 2050 / 2075) picks the snapshot; three cards report the top residual driver at each. **Excluded by construction:** the scenario settings (F23–F27), the structural assumptions (F18, F19, F22, F28), the measured fixed data (F01, F02) — none of those are *residual* uncertainty.

> Caveat (in the caption): the top-ranked residual driver is *not* a new finding that displaces the known dominance of the scenario settings — it is the largest residual contributor *conditional on having already made the scenario and structural decisions*. To see uncertainty when the scenario itself is uncertain, switch Figure A to *Scenario envelope*.

### 8.9 Main panel — Figure C: layer contribution summary

**Answers:** *"How much of the residual spread comes from each layer of the model, year by year?"* Grouped bars of `(p95 − p05) / p50` for each *layer* in isolation, at several years. By default only **L1** (emission factors) and **L2** (load model) are shown — **L3** parameters are deployment scenario settings: they *define* the trajectory, they are not residual uncertainty. A checkbox **"Include L3 for reference (conditional on target-setting)"** adds the L3 bar so you can see how much wider the scenario envelope would be if targets were treated as priors too. The caption explains the L1 / L2 / L3 distinction.

### 8.10 Main panel — Scenario-setting leverage

A short narrative read-out: the dominant residual driver at 2030 and 2050 (from the Figure B data), then the leverage ranking of the five deployment settings for *reducing 2050 emissions* — (1) hardware-efficiency doubling time (largest compounding effect); (2) BEV growth rate (largest near-term effect for fossil-heavy grids); (3) low-carbon electricity growth (largest long-horizon effect); (4) CAV target (shapes total ATS demand); (5) STI target (modest direct effect; couples to the CAV–STI interaction). A **"What remains outside the residual band"** table is explicit: scenario-setting positions, structural assumptions, structural shocks, and missing life-cycle phases are *not* in the band; the residual L1/L2 ranges *are* (and update automatically).

### 8.11 Main panel — State-conditioned subsystem decomposition over time

A stacked-area chart of the *same live deterministic run* that produced the Figure A trajectory, broken into nine series — ECAV / ICECAV / STI × Sensing / Computing / Communication — in TWh yr⁻¹, with the ATS total overlaid as a dashed line, through 2075. This is where you watch the computing share of utility-phase energy *decay over time* as hardware doubling compounds.

### 8.12 Main panel — Factor specification

A quick reference, grouped to mirror the Overview-page uncertainty figure: **Input data** (F01, F02, vehicle stock, intersections, the STI Basic aggregation note) · **State condition settings** (F32–F36) · **ATS unit and subsystem demand factors** (F09–F11 ECAV sensing/computing/communication scale factors, F15–F17 STI scale factors, F20 ICECAV power overhead) · **Fleet deployment settings** (F23–F29, plus F18/F19/F22/F28 and the ramp shape) · **Utility-phase residual ranges** (F03 low-carbon CO₂ intensity, F04 fossil CO₂ intensity — region-specific, F05 gasoline CO₂ intensity). Each row gives ID, short label, role, value-or-range. A separate expander **"One-time lifecycle inputs"** points to the One-Time Energy page for production / logistics / end-of-life factors.

### 8.13 Main panel — Residual uncertainty ranges (the former "Block 4")

**What this section is for:** the one place you can ask *"what if my assumptions about the emission factors or the subsystem load factors were different?"* — you edit the priors that drive the live Monte-Carlo band. Each residual parameter has a selectbox with two settings:

- **Default** — the evidence-anchored range reported in the manuscript; produces the default residual band. The published spec is shown in italics beneath the selector (e.g. `dist=triangular, low=0.02, mode=0.03, high=0.05` or `dist=lognormal, mean=1.0, sigma=0.20`).
- **Customized** — an inline editor, one number input per distribution parameter: triangular → low/mode/high · lognormal → mean/sigma · beta → mean/kappa · truncated_normal → mean/sd/min/max · dirichlet → alpha (comma-separated). Validated live: an invalid spec shows a warning and the page falls back to the published prior until fixed. Selecting *Customized* on any parameter flips the page-level **"All default ranges active"** badge to **No**.

Parameters are grouped in expanders: **Emission-factor ranges** (F03, F04, F05) · **ECAV load-model ranges** (F09, F10, F11 — expanded by default) · **STI load-model ranges** (F15, F16, F17) · **ICECAV conversion range** (F20) · **State weather adjustment factors** (F32–F36). Each shows its physical meaning and a collapsible **Source** with the citation. Three cards summarise: *Default ranges active* (count), *Customized ranges active* (count), *All default ranges active* (Yes / No — "Yes" requires Baseline policy, a CA or OH region, the default or paper-safe bundle, and no customised ranges). **"Reset all to default ranges"** restores every residual parameter to its published prior and discards stashed custom specs.

> **Not here:** the scenario settings F23–F27 and F29, the structural assumptions F18/F19/F22/F28, and the fixed-data anchors F01/F02 are held at central values — they live in the sidebar and the structural-assumptions expander.

### 8.14 Main panel — Data sources and assumptions (full provenance)

A single expandable table listing every factor with its block/category, ID, short label, role in analysis, value-or-range, source, and rationale. Factor IDs in parentheses (`(stock)`, `(intersections)`, `(ramp)`) are derived configuration settings without an F-number.

> **Expected output:** on first load the deterministic trajectory appears immediately; after a brief spinner the live residual band fills in and the green "band updated for current settings" line appears. Every metric card and figure is keyed to the *current* sidebar settings.

---

## 9. Key concepts and glossary

The first line of each technical entry says *what question the concept answers*; the rest is the precise definition.

| If you see… | It means… | §|
|---|---|---|
| CAV / ECAV / ICECAV / STI / ATS | vehicle and infrastructure categories | 9.1 |
| L1 / L2 / L3 | which layer of the model a parameter belongs to | 9.2 |
| Residual band / Scenario envelope | the two uncertainty objects on Figure A | 9.3 |
| Interpretation boundary, IB, τ | where the band stops being a forecast interval | 9.4 |
| Peak year / Turning year | trajectory shape diagnostics | 9.5 |
| Deterministic / Monte Carlo | the line vs the band | 9.6 |
| Fxx | a stable factor ID | 9.7 |

### 9.1 Vehicle / infrastructure categories

- **CAV** — Connected Autonomous Vehicle (autonomy levels L3 / L4 / L5).
- **ECAV** — a battery-electric vehicle that is also a CAV (EV ∩ CAV); autonomy energy drawn from the grid.
- **ICECAV** — an internal-combustion vehicle that is also a CAV (ICE ∩ CAV); autonomy energy supplied via the alternator with a ~1.6× conversion-overhead power factor (F20).
- **STI** — Smart Traffic Infrastructure, tiers Basic / Semi-automated / Highly-automated; energy reflects 24/7 LiDAR, radar, V2X, and edge compute at an equipped intersection or corridor segment.
- **ATS** — the Automated Road Transport System as a whole (ECAV + ICECAV + STI); "ATS energy" / "ATS emissions" are the fleet-level totals plotted in Figure A.
- **Subsystems** — every AV unit's energy decomposes into **Sensing**, **Computing**, **Communication**; propulsion is reported separately on the Utility Phase page.
- **BEV** — battery-electric vehicle. **ICE / ICEV** — internal-combustion-engine vehicle. **STI coverage** — share of *convertible* intersections / corridors that are equipped.

### 9.2 Layers (used in Figures B and C)

*Intuition:* L1/L2 are "things we measured imperfectly" (residual uncertainty); L3 is "choices about the future" (scenario, not uncertainty).

- **L1** — emission-factor parameters: F03 (low-carbon CO₂ intensity), F04 (fossil CO₂ intensity), F05 (gasoline CO₂ intensity).
- **L2** — load-model parameters: the ECAV/STI sensing/computing/communication scale factors F09–F17, and the ICECAV overhead F20.
- **L3** — deployment scenario-setting parameters: the CAV/STI targets and the growth rates F23–F27. L3 *defines the trajectory* and is **not** counted as residual uncertainty; it only enters the *scenario envelope*.

### 9.3 Residual band vs scenario envelope

<!-- VISUAL PLACEHOLDER: a narrow "residual" ribbon nested inside a wider "scenario envelope" ribbon around the same deterministic line. -->

*Intuition:* the **residual band** is "given my plan, how uncertain is the outcome?"; the **scenario envelope** is "the plan itself is uncertain — how wide is the predictive spread?". The envelope is always the wider of the two.

- **Residual band** — p05–p95 from a Monte-Carlo pass that samples only the residual (L1 + L2) input ranges plus the annual weather draw, with all scenario settings and structural assumptions *fixed at the currently selected values*.
- **Scenario envelope** — p05–p95 from a Monte-Carlo pass that *also* samples the deployment targets (F23–F27) over registry MEDIUM priors. Always wider than the residual band.
- **Default / committed bundle** — a pre-computed Monte-Carlo bundle on disk (`results/{region}__policy-baseline__bundle-*_quantiles.csv`) used to populate Figure A before a live band exists; centred on the *baseline* policy and region defaults, *not* re-centred when you change scenario settings — the page computes a fresh live band instead.

### 9.4 Interpretation boundary (IB)

*Intuition:* somewhere out in the future the band gets so wide it stops behaving like a "we're X % confident the value lands here" interval and starts behaving like "this is the range of plausible scenarios". The IB marks that crossover year — formally, the first year after 2027 where the band's relative width `(p95 − p05) / p50` exceeds a threshold τ. The dashboard reports two side by side: **τ = 1.5** (the dashboard / manuscript default) and **τ = 0.5** (a tighter, IPCC-AR6-style threshold — quote this if you need a stricter confidence-interval claim). On Figure A the τ = 1.5 boundary is a dashed vertical line with the year annotated; the region from the IB to 2075 is lightly shaded.

### 9.5 Peak year and turning year

- **Peak year** — the first year of the local maximum in the *median* trajectory.
- **Turning year** — the first year at or after the peak where the median has fallen to ≤ 50 % of the peak value. If the median is still rising or hasn't halved by 2075, the card reads "Not reached by 2075" (the metric is computed on the full internal 2024–2092 simulation, so "After 2075 (20XX)" can appear).

### 9.6 Deterministic vs Monte-Carlo

*Intuition:* the **deterministic** run is "the model's single best guess"; the **Monte-Carlo band** is "the model run many times with the uncertain inputs jiggled, then summarised".

- **Deterministic trajectory** — a single simulator run at the currently selected settings, every distribution collapsed to its central value. The dark solid line on Figure A and the basis of the subsystem-decomposition chart and the peak-year diagnostics.
- **Monte-Carlo band** — `n` runs (the "Monte Carlo runs" slider) with the residual ranges (and, for the envelope, the targets) sampled; percentiled per year — or per cumulative run, for cumulative metrics.

### 9.7 Factor IDs (F-numbers)

Every uncertain or structural quantity has a stable `Fxx` label so it can be cross-referenced between the dashboard, the figures, the manuscript, and the parameter registry. The interaction-relevant ones: **F18/F19** level-mix templates · **F22** service life · **F28** fleet-growth form · **F23/F24** CAV/STI 2075 targets · **F25** BEV growth · **F26** low-carbon electricity growth · **F27** hardware doubling time · **F29** hardware deployment lag · **F32–F35** annual weather-share simplex + concentration · **F36** weather-to-grid CO₂ sensitivity · **F03/F04/F05** emission-factor ranges · **F09–F17** subsystem load-model ranges · **F20** ICECAV overhead. (F06–F08 and F12–F14 are hidden as duplicates of per-level aggregates.)

---

## 10. Practical workflows

Each is a short click-path on the **Scenario Explorer** (unless stated otherwise).

- **"What if California pushes BEV adoption and a clean grid harder?"** Sidebar: Region = California, Policy = Baseline → apply the *CA-Aggressive* policy case, or directly raise *Annual BEV-share growth* (F25) and *Annual low-carbon electricity share growth* (F26) → watch the deterministic line on Figure A drop; the residual band rebuilds automatically → compare the *Peak year* and *Turning year* cards before/after.
- **"How robust is that conclusion to parameter uncertainty?"** Keep Figure A on *Residual* → raise *Monte Carlo runs* to 160–200 → read the p05–p95 spread and the IB (τ = 1.5 / τ = 0.5) cards → check Figure B for the residual parameter driving the remaining spread.
- **"And if the scenario itself is uncertain?"** Switch *Uncertainty object* to *Scenario envelope* — the band widens to include uncertainty in the deployment targets; the IB typically moves earlier.
- **"Where does the energy actually go, and when does compute stop dominating?"** The *State-conditioned subsystem decomposition over time* chart on the Scenario Explorer (fleet scale, over time) and the donuts on the One-Time Energy page (embodied vs operational at a point in time).
- **"Is my custom prior plausible?"** *Residual uncertainty ranges* → set the parameter to *Customized*, edit the spec; an invalid spec is flagged and ignored until corrected. The "All default ranges active" badge reads **No** while any custom spec is active.

---

## 11. Reproducing the manuscript exactly

On the **Scenario Explorer**:

1. **Region** ∈ {California, Ohio} — do **not** use U.S. Average.
2. **Policy** = Baseline.
3. **Default residual band** = Default (or "Alternative reproduction" for the paper-safe bundle).
4. **State weather profile** = Auto (state default).
5. All entries in **Residual uncertainty ranges** = Default.
6. All **Structural assumptions** at their defaults — *Balanced* CAV mix, *Basic-heavy* STI mix, 12-yr service life, *Linear* fleet growth.
7. Confirm the **"All default ranges active = Yes"** badge — that badge *is* the paper-matching check.

You do **not** need to regenerate anything; the `results/*_quantiles.csv` bundles ship with the repo. To rebuild them (e.g. after editing a `scenarios/{region}/scenario.json` parameter), from the repo root:

```bash
python scripts/regenerate_default_bundle_quantiles.py                                                  # rebuilds CA + OH bundle-default (and paper-safe) quantile CSVs
python footprint_model.py --scenarios california ohio --years 68 --policy baseline --mc 200 --seed 42  # raw deterministic / Monte-Carlo engine runs
```

The dashboard picks up updated `results/{region}__policy-baseline__bundle-default_quantiles.csv` next time it loads. *Note:* `*_mc_runs.csv` files can be GB-scale; the dashboard itself only needs the small `*_quantiles.csv` files.

---

## 12. Common errors and troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `streamlit: command not found` | venv not active, or deps never installed | `cd /path/to/CLEAR_ATS && source .venv/bin/activate`, then `pip install -r v9_streamlit_app/requirements.txt`. Fallback: `python -m streamlit run v9_streamlit_app/streamlit_app.py`. |
| `ModuleNotFoundError: No module named 'streamlit'` (or `pandas`, `plotly`, `numpy`, `matplotlib`) | deps not installed into the active interpreter | Re-run the `pip install` with the right env active. Confirm: `python -c "import streamlit, pandas, numpy, plotly, matplotlib; print('ok')"`. |
| `FileNotFoundError` / `ModuleNotFoundError` naming `v4_streamlit_app`, `_v4_core`, `scenarios/…`, `configs/…`, or `core.py` | launched from outside the repo, or `v9_streamlit_app/` copied out on its own | Keep the whole `CLEAR_ATS` repo intact and launch from its root: `cd /path/to/CLEAR_ATS && streamlit run v9_streamlit_app/streamlit_app.py` ([§4](#4-repository-layout--what-the-app-needs-on-disk)). |
| Overview page shows "Uncertainty framework figure not found …" | `assets/clear_ats_uncertainty_figure_v30.png` is missing | Restore the file; the rest of the dashboard is unaffected. |
| Scenario Explorer: yellow "the committed bundle is centred on Baseline …" | Policy ≠ Baseline — expected, not an error; the page still computes a fresh live band | Ignore it, or switch Policy back to Baseline. |
| Scenario Explorer: red "quarantined region" error; figures missing/flagged | U.S. Average is selected (consumption tables diverge 10–30× from CA/OH) | Use California or Ohio for any quantitative reading. |
| `Address already in use` / app opens but is the wrong project | port 8501 is taken | `streamlit run v9_streamlit_app/streamlit_app.py --server.port 8502`. |
| Charts feel slow when dragging "Monte Carlo runs" up | more MC samples = more compute per rebuild | Keep at 60–100 for exploration; 160–200 only for a final read. |
| "All default ranges active" says **No** unexpectedly | a non-Baseline policy / non-CA-OH region / non-default bundle / Custom weather / Customized residual range is active | Click **"Reset all to default ranges"**; set Policy = Baseline, Region ∈ {CA, OH}, weather = Auto, bundle = Default ([§11](#11-reproducing-the-manuscript-exactly)). |
| Browser tab opened but blank / "connecting…" forever | server crashed at startup (check the terminal traceback) or a stale browser session | Fix the underlying error (usually a row above), then reload. `Ctrl-Shift-R` for a hard refresh. |
| Want to verify the install is healthy before launching | — | `python scripts/validate_v9_dashboard_runtime.py` from the repo root; all checks should report `OK`. |

> **Common mistakes:** launching from a copied-out `v9_streamlit_app/` (it needs `../v4_streamlit_app/` and `../scenarios/`); adding a One-Time Energy number to a Scenario Explorer number (different life-cycle phases, never auto-summed); reading the band past the interpretation boundary as a forecast interval.

---

## 13. Caveats to keep in mind

- **U.S. Average is exploratory only** — consumption tables diverge 10–30× from CA/OH; hidden from the region list unless explicitly enabled; every U.S. Average view carries a red warning.
- **Non-baseline policies don't re-centre the committed band** — when Policy ≠ Baseline, the committed bundle still reflects Baseline; the page computes a fresh live band, but the fallback shown before the live band finishes is Baseline-centred.
- **Cumulative views read a per-run cumulative band, not the annual MC band** — deliberate: summing per-year p95 values overstates the cumulative tail because runs are not perfectly rank-correlated across years.
- **One-Time Energy page sliders were removed in v9** — it shows the manuscript baseline; the equivalent assumptions are read-only at the bottom of that page, and one-time uncertainty is documented there as input ranges.
- **Display horizon = 2075** — charts stop at 2075; some diagnostics computed on the internal 2092 horizon will say "After 2075 (20XX)".
- **Operational-phase boundary on the Scenario Explorer / Utility pages** — production, logistics, and end-of-life are *not* included there; they live on the One-Time Energy page and are never auto-summed with the operational figures.

---

## 14. Where the numbers come from (source-of-truth files)

For tracing a value or modifying the model rather than just using the dashboard:

| What | File(s) |
|---|---|
| Dashboard behaviour (entry point + pages) | `v9_streamlit_app/streamlit_app.py`; `v9_streamlit_app/pages/01_One_Time_Energy.py`, `02_Utility_Phase_Energy.py`, `03_Scenario_Explorer.py` |
| Simulation / UI bridge (v9-specific) | `v9_streamlit_app/core.py` (re-exports tested helpers from `v4_streamlit_app/core.py`), `weather_module.py`, `scenario_definitions.py`, `one_time_data.py` |
| Underlying year-by-year simulator | `footprint_model.py` (repository root) |
| Regional model parameters (canonical) | `scenarios/{california,ohio,us_average}/scenario.json` (legacy fallback: `configs/{region}.json`) |
| v9-local config (policies, mitigation defaults, labels, weather priors) | `v9_streamlit_app/configs/policy_scenarios.json`, `mitigation_defaults.json`, `parameter_labels.json`, `configs/weather_v8/` |
| Pre-computed Monte-Carlo bundles shown on Figure A | `results/{region}__policy-baseline__bundle-{default,paper-safe}_quantiles.csv` (+ `_mc_runs.csv`, `_metrics.csv`) |
| Project-wide context, version history, experiment → dashboard pipeline | `CLAUDE.md`, `docs/VERSION_TIMELINE.md`, `docs/EXPERIMENT_TO_DASHBOARD_PIPELINE.md`, `reports/CLEAR_ATS_v8_BRIEFING.md` |
| Pre-flight install check | `scripts/validate_v9_dashboard_runtime.py` |

---

*v9 dashboard guide — detailed walkthrough. Source of truth for behaviour: the files in §14. Companion: `USER_GUIDE.md`.*
