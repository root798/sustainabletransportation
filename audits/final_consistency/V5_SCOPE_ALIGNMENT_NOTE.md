# Scope alignment note — v5.1.1

## Why this note exists

The Scenario Explorer is **utility-phase only**. That scope is correct
and matches the Methods M9, M10, and M11 paragraphs in the manuscript.
But the Scenario Explorer does not carry a top-of-page disclosure of
the scope, so a reviewer arriving at the page could read the peak and
turning-year numbers as if they were full life-cycle totals.

## Change applied

A **"Scope note — read this first"** expander now sits directly below
the Scenario Explorer title and subtitle. It contains the following
text.

> This dashboard visualises **utility-phase (operational)** energy and
> emissions of the autonomy stack. It does so because that is the phase
> in which scenario dependence is strongest and in which the mitigation
> levers in Block 1 directly act.
>
> The **full life-cycle** comparison that supports the manuscript's
> central claim — including one-time production burdens for vehicles,
> sensors, batteries, and roadside infrastructure — is presented in
> the manuscript's main figures and in the System Boundary page. The
> Scenario Explorer does not carry those one-time terms. A reader who
> wants a life-cycle total must add an external one-time contribution
> before comparing these outputs to a cradle-to-grave number.
>
> Two uncertainty objects are exposed in Figure A below and must be
> read differently.
>
> - **Residual band.** Conditional on the Block 1 levers and Block 3
> assumptions the reader has chosen. Answers the decision-focused
> question: given my scenario, how tightly does the current evidence
> base pin the outcome?
> - **Scenario envelope.** Also samples Block 1 trajectory levers
> (F23 to F27) over evidence-based MEDIUM priors. Answers the
> reviewer-facing question: how wide is the predictive uncertainty if
> the scenario targets are themselves uncertain?

The expander defaults to collapsed so the page opens with figures
above the fold, but the notice is prominent and always visible at
the top.

## Why an expander and not a banner

A full banner would push the Block 2, Block 3, Block 4 expanders, and
Figure A below the fold on a standard laptop screen. A single
collapsed expander uses one line at the top and still serves as a
scope disclosure. The page title subtitle ("utility-phase energy and
emissions only") continues to announce the scope in-line.

## Why not add a static life-cycle context panel

The manuscript's life-cycle figure depends on external one-time LCA
values that are not in the dashboard's simulation pipeline. Embedding
those one-time values on the page would either duplicate manuscript
content (risking drift) or pull a static snapshot that is already
available on the System Boundary page. Keeping the scope disclosure as
text plus a pointer to the System Boundary page is the lighter,
lower-risk choice.

## Cross-reference

The System Boundary page (`v5_streamlit_app/pages/01_System_Boundary.py`)
covers the full phase-by-phase scope, the conceptual-only treatment of
manufacturing and end-of-life, and the external LCA literature
pointers. The new Scope note on the Scenario Explorer links the reader
there.
