# CLEAR-ATS Dashboard (v9)

*Clean Energy Automated Road Transport System — an interactive explorer for the energy demand and CO₂ emissions of road transport, 2024 onward.*

CLEAR-ATS projects how **Connected Autonomous Vehicles (CAVs)** and **Smart Traffic Infrastructure (STI)** reshape fleet-level energy use in California and Ohio. The v9 Streamlit dashboard is the active front end: pick a region, policy, and deployment scenario, and the simulator re-runs live with a Monte-Carlo uncertainty band.

> **Built for** researchers, reviewers, and external collaborators who want to explore the model and reproduce the manuscript figures without reading the simulation code.

<!-- TODO: add a hero screenshot here — e.g. ![Scenario Explorer](assets/screenshot_scenario_explorer.png) -->

---

## Contents

- [Quick start](#quick-start) — get the app running in 4 commands
- [First-time tour](#first-time-tour) — what to click in the first 5 minutes
- [The four screens](#the-four-screens) — a one-line guide to each page
- [Concepts at a glance](#concepts-at-a-glance) — the 5 terms you need before exploring
- [Installation details](#installation-details) — when the Quick start isn't enough
- [Repository structure](#repository-structure) — what files the app needs
- [Reproducing the manuscript](#reproducing-the-manuscript) — paper-matching checklist
- [Troubleshooting](#troubleshooting) — common failures and fixes
- [Where to go deeper](#where-to-go-deeper) — links to the full technical docs

---

## Quick start

> **Prerequisites:** Python 3.10+ and a checkout of the **full** `CLEAR_ATS` repository. The dashboard reads sibling and parent folders — see [Repository structure](#repository-structure).

```bash
cd /path/to/CLEAR_ATS                                  # the repo root (contains v9_streamlit_app/, v4_streamlit_app/, scenarios/, configs/, results/)
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r v9_streamlit_app/requirements.txt
streamlit run v9_streamlit_app/streamlit_app.py
```

**Expected output**

```
You can now view your Streamlit app in your browser.

  Local URL:   http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Your browser opens at the Local URL automatically. Press **`Ctrl-C`** in the terminal to stop the server.

> ⚠️ **Run from the repository root.** The v9 app imports tested helpers from `v4_streamlit_app/` and reads `scenarios/`, `configs/`, and `results/` from the repo root. A `ModuleNotFoundError` or `FileNotFoundError` on launch almost always means you launched from the wrong place — see [Troubleshooting](#troubleshooting).

---

## First-time tour

Once the app is open, do this to get oriented:

1. **Start on the Overview page** (loads first). Read the three-column key at the bottom — it tells you what each of the other pages is for.
2. **Jump to the Scenario Explorer** (sidebar → last page). This is the main interactive screen.
3. In the sidebar, leave **Region = California**, **Policy = Baseline**, **Default residual band = Default**. You'll see Figure A draw the deterministic trajectory immediately, then (after a short spinner) fill in the live residual uncertainty band.
4. Try moving the **"Annual BEV-share growth"** slider up. Watch the dark trajectory line and the *Peak year* / *Turning year* metric cards change.
5. Toggle the **Uncertainty object** radio above Figure A from *Residual* to *Scenario envelope* — the band widens to include uncertainty in the deployment targets themselves.

> **Key takeaway.** The dashboard re-runs the model on every interaction; there is no "Recompute" button. Everything you see is keyed to the current sidebar settings.

→ For the full page-by-page walkthrough of every control, chart, and metric card, see [USER_GUIDE.md](USER_GUIDE.md).

---

## The four screens

| Screen | Question it answers | Interactive? |
|---|---|---|
| **Overview** | What is CLEAR-ATS and how is its uncertainty structured? | No (static) |
| **One-Time Energy** | Energy embodied in *producing, shipping, retiring* the autonomy hardware. | One view toggle |
| **Utility Phase Energy** | Annual *running* energy per vehicle or per roadside asset, split into propulsion + sensing + computing + communication. | Propulsion inputs + rate-region selector |
| **Scenario Explorer** | State-scale annual & cumulative ATS energy and CO₂ under chosen deployment, electrification, grid, weather, and hardware-efficiency settings. | **Yes — the main screen** |

**Three scope rules apply everywhere:**

- **Operational and one-time phases are reported separately and never auto-summed.** Scenario Explorer + Utility Phase = operational only; One-Time Energy = production + logistics + end-of-life only.
- **California and Ohio are full-resolution.** *U.S. Average* is a synthetic midpoint, quarantined, exploratory only, and flagged in red wherever it appears.
- **Charts stop at 2075.** The simulator runs internally to 2092, but predictive validity is not claimed beyond 2075.

---

## Concepts at a glance

The five terms you need before opening the Scenario Explorer. Full definitions and the F-number registry: [USER_GUIDE.md → Key concepts and glossary](USER_GUIDE.md#7-key-concepts-and-glossary).

| Term | Plain meaning |
|---|---|
| **ATS** | Automated Road Transport System = fleet-level total (ECAV + ICECAV + STI). |
| **CAV / ECAV / ICECAV / STI** | Autonomous vehicle / its electric subset / its internal-combustion subset / Smart Traffic Infrastructure. |
| **Residual band** | Uncertainty *around your chosen scenario* — the L1 emission-factor + L2 load-model priors only. Decision-focused. |
| **Scenario envelope** | The residual band *plus* uncertainty in the deployment targets themselves. Always wider; reviewer-facing. |
| **Interpretation boundary (IB)** | The first year after 2027 where the band's relative width exceeds threshold τ. Beyond the IB, read the band as a scenario envelope, not a frequentist forecast interval. The dashboard reports **τ = 1.5** (manuscript default) and **τ = 0.5** (IPCC-AR6-style tighter convention) side by side. |

---

## Installation details

**For most users**, the [Quick start](#quick-start) is all you need. The notes below cover platform-specific details and optional validation.

### Requirements

| Item | Notes |
|---|---|
| Python | **3.10 or newer** (tested on 3.10 and 3.13). Check: `python3 --version`. |
| Dependencies | `streamlit ≥ 1.32`, `pandas ≥ 2.0`, `numpy ≥ 1.24`, `plotly ≥ 5.18`, `matplotlib ≥ 3.7`. |
| Disk | ~1–2 GB if the large `results/*_mc_runs.csv` files are present. The dashboard itself only needs the much smaller `*_quantiles.csv` files, which ship with the repo. |
| Internet | Only for `pip install`. The dashboard runs fully offline afterward. |

### Activating the environment on subsequent sessions

```bash
cd /path/to/CLEAR_ATS
source .venv/bin/activate                              # Windows (PowerShell): .venv\Scripts\Activate.ps1
streamlit run v9_streamlit_app/streamlit_app.py
```

### Optional pre-flight validator

Catches UI-breaking regressions without starting a server:

```bash
python scripts/validate_v9_dashboard_runtime.py        # run from the repo root
```

**Expected output:** a series of `[ OK ]`/`[FAIL]` lines ending in a pass summary.

### Useful launch options

```bash
streamlit run v9_streamlit_app/streamlit_app.py --server.port 8502      # use a different port
streamlit run v9_streamlit_app/streamlit_app.py --server.headless true  # don't auto-open a browser (e.g. on a remote machine)
```

---

## Repository structure

The v9 dashboard is **not** a self-contained folder. It depends on siblings and parents inside the `CLEAR_ATS` repository:

```
CLEAR_ATS/                         ← run all commands from here ("repository root")
├── v9_streamlit_app/               ← the active dashboard (this folder)
│   ├── streamlit_app.py             ← Overview page + entry point — launch THIS
│   ├── requirements.txt
│   ├── core.py                      ← simulation/UI bridge (re-exports v4 helpers + v8/v9 additions)
│   ├── pages/                       ← 01_One_Time_Energy.py, 02_Utility_Phase_Energy.py, 03_Scenario_Explorer.py
│   ├── configs/                     ← policy_scenarios.json, mitigation_defaults.json, parameter_labels.json, weather_v8/
│   ├── assets/                      ← clear_ats_uncertainty_figure_v30.png (shown on the Overview page)
│   └── USER_GUIDE.md                ← full technical reference
│
├── v4_streamlit_app/core.py         ← REQUIRED: v9's core.py imports tested helpers from here
├── scenarios/{california,ohio,us_average}/scenario.json   ← canonical regional model parameters
├── configs/{california,ohio,us_average}.json             ← legacy fallback for the above
└── results/                         ← pre-computed Monte-Carlo bundles the dashboard displays
    └── {region}__policy-baseline__bundle-{default,paper-safe}_quantiles.csv  (+ _mc_runs.csv, _metrics.csv)
```

> **Advanced note.** The app tries `scenarios/{region}/scenario.json` first and falls back to `configs/{region}.json`. The committed `results/*_quantiles.csv` bundles only seed Figure A before a live band finishes computing; the dashboard never writes to `results/`. Full layout: [USER_GUIDE.md](USER_GUIDE.md); project-wide architecture: [../CLAUDE.md](../CLAUDE.md).

<!-- TODO: optionally replace the tree above with a repository-structure diagram. -->

---

## Reproducing the manuscript

To put the dashboard in a paper-matching configuration, set the **Scenario Explorer** as follows:

1. **Region** ∈ {California, Ohio} — *not* U.S. Average.
2. **Policy** = Baseline.
3. **Default residual band** = Default (or *Alternative reproduction* for the paper-safe bundle).
4. **State weather profile** = Auto (state default).
5. All **Residual uncertainty ranges** = Default.
6. All **Structural assumptions** at defaults — *Balanced* CAV mix, *Basic-heavy* STI mix, 12-yr service life, *Linear* fleet growth.
7. Confirm the **"All default ranges active = Yes"** badge.

> **Key takeaway.** You do **not** need to regenerate anything to reproduce the manuscript — the `results/*_quantiles.csv` bundles ship with the repo.

If you do want to rebuild the bundles (e.g. after editing a `scenarios/{region}/scenario.json` parameter), run from the repo root:

```bash
python scripts/regenerate_default_bundle_quantiles.py                                  # rebuild CA + OH bundles
python footprint_model.py --scenarios california ohio --years 68 --policy baseline --mc 200 --seed 42   # raw engine runs
```

→ Full caveats on what is and isn't inside the uncertainty band: [USER_GUIDE.md → Caveats](USER_GUIDE.md#9-caveats-to-keep-in-mind).

---

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `streamlit: command not found` | Virtual environment not active, or dependencies not installed. → Activate the env, then `pip install -r v9_streamlit_app/requirements.txt`. Fallback: `python -m streamlit run …`. |
| `ModuleNotFoundError` / `FileNotFoundError` naming `v4_streamlit_app`, `_v4_core`, `scenarios/`, `configs/`, or `core.py` | Launched from outside the repo, or `v9_streamlit_app/` copied out alone. → Keep the whole repo intact and `cd` to its root before launching. |
| Overview page shows *"Uncertainty framework figure not found …"* | `assets/clear_ats_uncertainty_figure_v30.png` is missing. → Restore the file; the rest of the dashboard is unaffected. |
| Red *"quarantined region"* error, or yellow *"committed bundle is centred on Baseline"* warning | Expected, not a bug. → Use CA/OH for quantitative reads; the page still computes a fresh live band when Policy ≠ Baseline. |
| `Address already in use` | Port 8501 taken. → `streamlit run v9_streamlit_app/streamlit_app.py --server.port 8502`. |
| Charts feel slow when dragging the **Monte Carlo runs** slider | More samples = more compute per rebuild. → Keep at 60–100 for exploration; raise to 160–200 only for a final read. |
| **"All default ranges active"** badge says **No** but you didn't change anything | A non-Baseline policy, non-CA/OH region, non-default bundle, Custom weather, or Customized residual range is active. → Click **"Reset all to default ranges"** and set Policy = Baseline, Region ∈ {CA, OH}, weather = Auto, bundle = Default. |
| Blank tab / *"connecting…"* forever | Server crashed at startup (read the terminal traceback) or the browser cached a stale session. → Fix the underlying error, then `Ctrl-Shift-R` for a hard refresh. |

> **Common mistakes**
> - Launching `streamlit_app.py` from inside `v9_streamlit_app/` after moving the folder. The app needs `../v4_streamlit_app/` and `../scenarios/` to exist.
> - Comparing Scenario Explorer numbers to One-Time Energy numbers directly. They are different life-cycle phases and are never auto-summed.
> - Reading the band beyond the **interpretation boundary** as a forecast interval. Past the IB it's a scenario envelope.

---

## Where to go deeper

| Topic | Where |
|---|---|
| Every page, control, chart, and metric card; full glossary; the residual-band / scenario-envelope distinction; worked workflows | **[USER_GUIDE.md](USER_GUIDE.md)** |
| Project-wide architecture, version history (legacy Flask → v9), and the experiment → dashboard data pipeline | **[../CLAUDE.md](../CLAUDE.md)**, `../docs/VERSION_TIMELINE.md`, `../docs/EXPERIMENT_TO_DASHBOARD_PIPELINE.md` |
| Underlying year-by-year simulator and the model equations | `../footprint_model.py`, the repository-root `../README.md` |
| Pre-computed Monte-Carlo bundles shown on Figure A | `../results/{region}__policy-baseline__bundle-{default,paper-safe}_quantiles.csv` |
| Pre-flight install check | `../scripts/validate_v9_dashboard_runtime.py` |

---

## Citation & license

<!-- TODO: add the manuscript citation and license once finalized. -->

This dashboard accompanies the CLEAR-ATS manuscript. See the repository root for the full project README and the model definition (`footprint_model.py`).
