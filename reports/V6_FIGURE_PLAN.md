# V6_FIGURE_PLAN — manuscript and dashboard figure inventory

v6 introduces six new figure types and re-labels two existing v5 figures. This
inventory lists every figure v6 produces or plans, its manuscript-facing
status, its source data, and the script that regenerates it.

---

## A. Manuscript-facing figures

These are the figures v6 would add to the paper or SI. Do not render until
manuscript text is aligned.

### A.1 Nested-MC four-panel overview (v6 main-text candidate)

- Two regions × two metrics (ATS emissions, ATS total power).
- Panel contents: outer-world central paths (grey) + scenario envelope (coloured band).
- Caption names: scenario, outer draws count, inner draws count, metric, that shaded band represents spread across outer epistemic draws, not a probabilistic interval.
- Source: `v6_uncertainty_rearchitecture/results/<region>__<policy>__runs.csv` via page 03 logic.
- Regeneration script: `v6_uncertainty_rearchitecture/scripts/run_nested_mc.py` then a new `scripts/build_v6_figures.py` (manuscript-grade run needs `n_outer=200, n_inner=20`).
- Status: **not rendered yet**. Awaiting manuscript-text alignment.

### A.2 Benchmark-year violin matrix (v6 main-text candidate)

- Two regions × five years (2030, 2035, 2045, 2055, 2075) = ten violins per metric.
- Caption names: metric, conditioning (outer × inner), and states that this is a marginal not a trajectory.
- Source: `<region>__<policy>__benchmark__*.csv`.
- Regeneration: `scripts/run_nested_mc.py`.
- Status: **not rendered yet**.

### A.3 Sobol-ranking horizontal bars (v6 SI candidate)

- Four panels (one per target scalar): cum_emis, peak_emis, peak_year, turning_year.
- Source: `<region>__<policy>__sensitivity__<target>.csv`.
- Caption names: method (Sobol total-order OR random-forest fallback), surrogate R².
- Regeneration: `scripts/run_sensitivity.py`.
- Status: **demo rendered in dashboard**; publication figure not rendered.

### A.4 Relative-uncertainty dual panel (v6 SI candidate)

- Absolute band vs (p95−p05)/|p50| ratio, two-column.
- Horizontal dashed lines at τ=1.5 and τ=0.5.
- Source: `<region>__<policy>__relative__*.csv`.
- Regeneration: `scripts/run_nested_mc.py`.
- Status: **not rendered yet**.

### A.5 Structural-shock comparison (existing v5 figure, v6 re-labelled)

- Five shocks + baseline, two regions (CA, OH).
- Caption updated to match v6 taxonomy: "discrete labelled scenario family; not probabilized".
- Source: `results/shocks/*_results.csv` (reused from v5).
- Regeneration: `python footprint_model.py --shock all --scenarios california ohio --mc 0`.
- Status: **existing v5 figure**; v6 adds caption text only.

### A.6 Deterministic reference path (existing v5 figure, v6 re-labelled)

- One panel per region.
- Caption updated: "central trajectory under median inputs; not a forecast; not the MC median".
- Source: v5 deterministic CSVs OR v6 `compute_reference_path`.
- Status: **existing v5 figure**; v6 adds caption text only.

---

## B. Dashboard-only figures

Rendered live by Streamlit. Not exported.

### B.1 Per-outer-world spaghetti (page 03)
### B.2 Within-scenario aleatoric fan (page 02, aleatoric-only mode)
### B.3 Benchmark-year violin selector (page 04 live)
### B.4 Shock overlay selector (page 06 live)
### B.5 Relative-width curve (page 07 live)

---

## C. How to generate the manuscript figures (once text is aligned)

Until manuscript alignment is done, these remain unrendered. The regeneration
command when ready:

```bash
# Step 1: manuscript-grade nested MC (≈ 200 outer × 20 inner × 2 regions ≈ 8000 runs; ~1-2 hours).
python v6_uncertainty_rearchitecture/scripts/run_nested_mc.py \
    --regions california ohio --policy baseline \
    --n-outer 200 --n-inner 20 --years 68 --seed 42 --verbose

# Step 2: sensitivity on the manuscript-grade design.
python v6_uncertainty_rearchitecture/scripts/run_sensitivity.py --regions california ohio

# Step 3: static-figure build (to be written as v6_uncertainty_rearchitecture/scripts/build_v6_figures.py).
python v6_uncertainty_rearchitecture/scripts/build_v6_figures.py
```

---

## D. What v6 does NOT add to the manuscript figure set

- Does not replace v5 Figure 3a (component-level one-time energy) or v5 Figure 3b (unit-level stacking). Those are one-time-phase figures; v6 is utility-phase.
- Does not introduce separate CA and OH Nature-quality two-column figures yet; those are drafted only once manuscript text references them.
- Does not introduce any figures that depend on a surrogate with R² < 0.8. Page 05's fallback currently reports R² ≥ 0.86 on the 40-outer demo — acceptable for dashboard; the manuscript version should re-run with n_outer = 200 and re-verify R².

---

## E. Figure-legend policy

Every v6 figure must display, in its caption:

1. Which uncertainty layers are active (scenario only / epistemic only / scenario + epistemic + aleatoric).
2. Whether the object is conditional.
3. Whether the band is a probabilistic interval (it usually is not; v6 priors are elicitation-based).
4. The number of outer and inner draws used.
5. The seed used.
6. The relevant interpretation-boundary year if the plot spans the full horizon.

If any of the above cannot be stated, do not ship the figure.
