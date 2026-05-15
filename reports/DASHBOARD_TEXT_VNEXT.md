# DASHBOARD_TEXT_VNEXT — v6 dashboard copy

Exact wording used on every v6 dashboard page. Kept here so copy can be
reviewed / edited without opening a Streamlit process.

---

## Landing page (`streamlit_app.py`)

**Title**: CLEAR-ATS v6 — Layered Uncertainty Architecture
**Subtitle**: Non-destructive upgrade to v5. Inspired by the 2025 Nature Communications Puerto Rico energy-transition paper. v3, v4, v5 remain runnable and unchanged.

**Opening paragraph**:

> v6 re-frames CLEAR-ATS uncertainty into four explicit layers and presents each as its own object with a named interpretation. The default view is intentionally not a single long-horizon band. You must pick which object you want to see.

**Four-layer table**: same as the main taxonomy in `UNCERTAINTY_ARCHITECTURE_VNEXT.md §2`.

**Info strip**: *The sidebar holds the seven uncertainty-object pages. Pick one to inspect. Every page names its category and states what the reader must not infer.*

---

## Page 00 · Taxonomy & Interpretation Discipline

**Purpose**: educate before visualise. No numerical plots.

**Content**:

- The four categories table.
- A collapsible list of every parameter routed to the outer loop.
- A collapsible list of every parameter routed to the inner loop.
- The "What each uncertainty object is / is not" table.
- The "Interpretation discipline across horizons" table.

**Closing info strip**: *Pages 01-07 each carry a one-line subtitle stating which uncertainty category the view belongs to and what must not be inferred from it.*

---

## Page 01 · Deterministic Reference Path

**Subtitle**: *Stage 1. Central trajectory under median / mode inputs. This is not a forecast and not the median of the MC distribution.*

**Controls**: region, policy, horizon.

**Metrics**: peak year, peak emissions (Mt), cumulative (Mt CO₂e), 2024 baseline (kt CO₂).

**What this plot is / is not**:

- Is: the ATS annual-emissions trajectory computed by `TransportModel` when every distribution spec is replaced by its central value (mode for triangular, mean for normal / lognormal, α/(α+β) for beta, equal-share for Dirichlet).
- Is not: a forecast.
- Is not: the median of the Monte Carlo distribution. Non-linearities mean the MC median differs from the central-input run by a small amount.

---

## Page 02 · Within-Scenario Conditional Band

**Subtitle**: *Conditional: on a chosen outer epistemic world OR on a named scenario. Not total uncertainty. Lower bound to broader uncertainty when outer pathways are fixed.*

**Controls**: region, policy, metric, conditioning mode.

**Conditioning options**:
- *Aleatoric only (one outer world)* — inner-loop spread at a single frozen pathway world.
- *All outer × inner draws* — full within-scenario set.

**What this plot is / is not**:
- Is: pointwise p05 / p50 / p95 of the chosen metric across the conditioning set.
- Is not: total uncertainty.
- Is not: a probabilistic predictive interval unless the draws are probabilized.

---

## Page 03 · Scenario Envelope (outer-loop spread)

**Subtitle**: *Spread across outer epistemic draws. Answers what if the world is different. Not a confidence interval unless the outer draws are probabilized.*

**Plot content**: grey thin lines = per-outer-world inner-median trajectory; red filled band = envelope p05–p95 across outer worlds; red dashed = envelope p50.

**What this plot is / is not**:
- Is: per-outer-draw inner-median central path, with an envelope across outer draws.
- Is not: a probabilistic confidence interval.
- Is not: the within-scenario band (page 02).

---

## Page 04 · Benchmark-Year Distributions

**Subtitle**: *Conditional marginal distribution at a named milestone year. Not a time-evolution claim. Use instead of trying to read values off a band.*

**Benchmark years**: 2030, 2035, 2045, 2055, 2075 (see `config/benchmark_years.json`).

**Plot content**: violins with box + all points at each benchmark year.

**Quantile table columns**: `year, n, p05, p25, p50, p75, p95, mean, std`.

**What this plot is / is not**:
- Is: marginal distribution at each named year across all outer × inner draws.
- Is not: a claim about years between benchmarks.
- Preferred for the paper: "2045 annual emissions p05-p95 range: [X, Y]" rather than reading values off a band.

---

## Page 05 · Sensitivity Analysis

**Subtitle**: *Which epistemic driver controls each output's variance? Not a claim about how big the uncertainty is — only which parameters produced it.*

**Target scalars**: `cum_emis_mean`, `peak_emis_mean`, `peak_year_mean`, `turning_year_mean`.

**Plot content**: horizontal bar chart of top-12 features sorted by score column (`ST` preferred, `importance_rf` fallback, `variance_explained` deterministic fallback).

**What this plot is / is not**:
- Is: ranking of which outer-epistemic parameters explain the variance of the chosen scalar output.
- Score column: `ST` is total-order Sobol (SALib). Fallback is RF feature importance.
- Is not: a claim about the absolute size of the uncertainty.
- Is not: a causal claim.

---

## Page 06 · Structural Shocks

**Subtitle**: *Discrete named regime breaks. Not probabilized. Compared visually vs baseline.*

**Registry files listed**:
- `grid_stall.json`
- `ev_slowdown.json`
- `hardware_supply_shock.json`
- `policy_freeze.json`
- `geopolitical_disruption.json`

**Plot content**: black deterministic baseline; coloured shock trajectories.

**What this plot is / is not**:
- Is: deterministic baseline vs pre-specified discrete shock simulations.
- Is not: an ensemble or a probabilistic mixture.
- Shock runs are never merged into baseline quantile CSVs.

---

## Page 07 · Relative Uncertainty

**Subtitle**: *Absolute p05-p95 width and the relative ratio (p95−p05)/|p50|, side by side. Narrowing of the absolute band near zero emissions is not improved predictability.*

**Two-panel layout**: left = absolute band; right = relative width with τ=1.5 (dashed) and τ=0.5 (dotted) reference lines.

**What this plot is / is not**:
- Is: pointwise absolute band (left) and the relative band width (p95−p05)/|p50| as a function of year (right).
- Is not: a claim that narrowing of the absolute band represents stronger predictability.
- Use: whenever someone says "look — uncertainty gets smaller at 2090!"

---

## Tooltips / warnings used across pages

- *Missing runs CSV*: `Missing results/<region>__<policy>__runs.csv. Run scripts/run_nested_mc.py.`
- *Missing sensitivity CSV*: `Missing results/<region>__<policy>__sensitivity__<target>.csv. Run scripts/run_sensitivity.py.`
- *No shock CSV*: `No shock output CSV found for <shock>. Run python footprint_model.py --shock <shock> --scenarios <region>.`

## Shared copy blocks

**What this page shows (layer active)** — on every page:
- Page 01: scenario layer only.
- Page 02: scenario + (aleatoric only OR scenario + epistemic + aleatoric).
- Page 03: scenario + epistemic (aleatoric medianed out).
- Page 04: scenario + epistemic + aleatoric, projected to benchmark years.
- Page 05: epistemic attribution under fixed scenario.
- Page 06: scenario + structural-shock discrete comparison.
- Page 07: same layer as page 02 or 03 depending on upstream config.

**Interpretation-boundary reminder** — appears next to any time-series band:
*"The interpretation-boundary year is the first year after 2027 where (p95−p05)/|p50| ≥ τ. Paper default τ=1.5; stricter τ=0.5 reported alongside. Inside the boundary, quantitative claims are allowed. Outside it, only conditional scenario / envelope claims are allowed."*
