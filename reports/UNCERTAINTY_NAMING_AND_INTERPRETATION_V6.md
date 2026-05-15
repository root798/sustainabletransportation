# UNCERTAINTY_NAMING_AND_INTERPRETATION_V6 — naming note

**Audience**: anyone editing v6 dashboard text or paper methods text. Fix the
vocabulary here so the rest of the project stays aligned.
**Hard rule**: do not relabel a layer in a way that contradicts how the v5
code actually computes it. If the math behaves like a mix, name it like a mix.

---

## 1. Mapping decision (final)

| v5 layer | v5 code behaviour | v6 dashboard label | Type | Rationale |
| --- | --- | --- | --- | --- |
| **L1** | Tight evidence-anchored emission-factor priors (`emission_factors.e_clean`, `e_fossil`, `e_gasoline`). Triangular distributions with narrow ranges. The MC band derived from L1-only stays narrow at all horizons; late-horizon narrowing reflects the bounded approach to zero. | *Within-scenario residual / aleatoric-style variability — emission factors* | Aleatoric-style residual | Behaves like short-horizon residual variability that does not scale with horizon. Calling it "aleatoric" pure would be slightly stronger than the math supports (the priors do encode some incomplete knowledge of the central value), so the label says "aleatoric-style". |
| **L2** | Lognormal-ish priors on subsystem scale factors and operational coefficients (cohort decay, ICEV overhead, scale factors per L3/L4/L5 and per Basic/Semi/Highly). σ values were tightened in v5.1.7 after the independent search. | *Within-scenario residual / aleatoric-style variability — load model* | Aleatoric-style residual + small epistemic component | Most contribution behaves residual-like in the existing parameter-contribution audit; a few weakly identified parameters (sti_scale_factors.Highly, ecav_scale_factors.communication) carry an epistemic component. Honesty wins — call it a mix. |
| **L3** | Trajectory and pathway parameters: CAV / STI 2075 targets, BEV growth exponent, clean-grid growth exponent, hardware efficiency doubling, fleet growth, service life. Triangular and normal priors with deliberately moderate σ. | *Pathway / epistemic uncertainty (long-horizon driver)* | Epistemic | The dominant source of long-horizon divergence in every v5 audit. Naming it as epistemic is unambiguously correct because all members are reducible-in-principle if a future commitment to a specific pathway is made. |
| **Scenario** (policy patches `baseline / aggressive / conservative`) | Discrete deep-merged JSON patches; selected by the analyst. | *Scenario uncertainty* (kept as in v5) | Scenario (not probabilized) | v5 already names this correctly. v6 keeps it. |
| **Structural shock** (`scenarios/shocks/*.json`) | Discrete labelled scenario JSONs with onset year, severity, duration. | *Structural-shock uncertainty* (kept as in v5) | Discrete labelled scenario family | v5 already names this correctly. v6 keeps it. |

## 2. Why these labels and not stricter ones

The Puerto Rico paper uses *epistemic* and *aleatoric* with strict optimisation-theory meaning. CLEAR-ATS is a dynamic trajectory model with elicitation-based priors, not a likelihood-calibrated posterior. Adopting the strict labels would imply a methodological purity v5 does not have.

The v6 compromise:

- **L1 / L2** carry the qualifier "*residual / aleatoric-style variability*" rather than "aleatoric uncertainty" alone. This is honest about how the priors were built (elicitation, not measurement of irreducible noise).
- **L3** can be called "*pathway / epistemic*" without qualifier, because every L3 member is genuinely about an unknown future state of the world.
- **Scenario** and **structural shock** stay in v5's existing English — these are already correct.

## 3. Forbidden phrasings

Whenever v6 dashboard or manuscript text describes a band, the following phrasings must be avoided. They imply an interval semantics the priors do not support.

- "Forecast confidence interval"
- "95% predictive interval" (unless the band is a Bayesian posterior — it is not in v5/v6)
- "The model becomes more certain over time"
- "Future certainty improves"
- "Uncertainty has narrowed" (without naming *which* uncertainty — absolute or relative — and explaining the cause)

## 4. Required phrasings

Use these whenever the corresponding object is shown.

- "*Conditional* on the chosen pathway, the within-scenario band ranges from p05 to p95."
- "*Pathway / epistemic* uncertainty (L3) is the dominant driver of long-horizon divergence."
- "*Benchmark-year marginal* at 2035 / 2045 / 2055 / 2075."
- "*Residual annual variability* (L1 / L2)."
- "*Interpretation boundary* of year Y: inside Y, quantitative; beyond Y, conditional only."
- "*Discrete scenario family*" (for structural shocks).
- "*Lower bound to broader long-horizon uncertainty*" — applied to any within-scenario band when scenario or pathway parameters are held fixed.

## 5. Where the v6 dashboard says these things

| Page | Where |
| --- | --- |
| `00_Scenario_Explorer.py` (inherited) | New 7-line caption between `st.info` and the existing scope expander. |
| `03_Uncertainty_Definitions.py` (new) | Compact taxonomy table + per-layer interpretation block + colour mapping. |
| `04_Uncertainty_Architecture.py` (new) | Schematic chips at the bottom of the diagram label L1 / L2 / L3 in v5 colour. |
| `05_Benchmark_Year_Distributions.py` (new) | "How to read this view" footer. |
| `06_Key_Epistemic_Drivers.py` (new) | Honest method label at the top + L3 sub-ranking. |
| `07_Mitigate_Long_Horizon_Uncertainty.py` (new) | Five-rule rubric + absolute-vs-relative panel + manuscript wording cheat sheet. |

## 6. Where the v5 code remains authoritative

- `figure_style.NATURE_LAYER` — colour assignments for L1 / L2 / L3 are unchanged.
- `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv` — the per-layer / per-parameter classifications used by the original v5 contribution experiment are the authoritative source for which factor is in L1, L2, or L3. v6 reads them; v6 does not edit them.

## 7. If a paper reviewer challenges the labels

Two short responses are pre-built:

> *"The L1 and L2 within-scenario bands are conditional on a chosen pathway and behave as residual / aleatoric-style variability over the relevant horizons. They are explicitly not predictive confidence intervals; the dashboard reports them as conditional intervals and surfaces a relative-uncertainty companion view to prevent misreading near-zero saturation as improved predictability."*

> *"The L3 layer aggregates trajectory and pathway parameters whose values would, in principle, be known under a committed future. We label it epistemic in this dashboard. The dominant epistemic drivers and their contribution to long-horizon divergence are reported in `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv` and rendered on dashboard page 06."*

## 8. Cross-references

- `V6_RECONSTRUCTED_FROM_V5.md` — what was inherited / added.
- `V6_RECONSTRUCTED_VALIDATION.md` — proof of v5 preservation.
- `UNCERTAINTY_SOURCES_TABLE_V6.md` and `.csv` — Puerto Rico Table-1-style uncertainty source list.
- v5 master reference: `reports/summaries/CLEAR_ATS_V5_MASTER_REFERENCE.md`.
