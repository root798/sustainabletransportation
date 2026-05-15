# V5 page-copy final alignment

The page's user-visible text now makes the four-block framework
explicit everywhere, and the band-status distinction (committed vs
live) is stated in multiple places so a reader cannot miss it.

## Top copy

Title. `Scenario Explorer`.
Sub-caption. "Residual uncertainty projections for California and Ohio
under user-chosen mitigation levers. Utility-phase energy and emissions
only."

## Sidebar copy

Scope section. "California and Ohio are paper-safe. U.S. Average is
quarantined from paper-facing quantitative comparison."

Block 1 header. "Mitigation levers."
Block 1 caption. "Adjust a lever to change the scenario. The
deterministic trajectory updates instantly; the committed residual
band does not re-centre. Use the Recompute button in the main panel to
rebuild the band for your current settings."

Every mitigation slider's `help` kwarg begins with a provenance tag in
square brackets (`[policy derived]`, `[literature derived]`, `[baseline
scenario assumption]`, `[industry consensus]`) so a hover always shows
the provenance before the prose citation.

## Main-panel copy

Block 2 expander heading. "Block 2. Fixed data (measured 2024 starting
values)."

Block 3 expander heading. "Block 3. Modeling assumptions (structural
choices)."

Block 4 header. "Block 4. Residual uncertainty priors."
Block 4 intro. "The truly residual uncertainty factors. These are L1
and L2 parameters only. The trajectory parameters F23 to F27 are in
Block 1 and define the scenario. The level-mix parameters F18 and F19,
and the structural parameters F22 and F28, are in Block 3. Block 4
radios drive the on-demand live-band recompute in the Figure A panel
below."

Block 4 footnote. "The Block 4 radios above control the live-band
recompute. The committed band shown in Figure A uses the
recommended-default or paper-safe radio bundle as committed at release
time and is independent of this session."

## Figure A copy

Status pill. One of
- `:white_check_mark: Live recomputed residual band`
- `:information_source: Committed default band`
- `:warning: Committed default band — does NOT match current settings`

Caption (committed state).
> "Figure A. Annual ATS CO₂ emissions for {region} under the {policy}
> policy, {bundle_display} bundle. Shaded envelope: committed p05 to
> p95. Dotted line: committed Monte Carlo median. Solid red line: live
> deterministic trajectory under your current Block 1 and Block 3
> settings. Dashed vertical line: first year after 2027 where the
> committed band width exceeds 1.5 times the median."

Caption (stale state, added on top of committed caption):
> "The band shown is the committed default and does NOT match your
> current Block 1, 3, or 4 settings. Click Recompute residual band to
> rebuild it."

Caption (live state):
> "Figure A. Annual ATS CO₂ emissions for {region}. Live
> {n_samples}-sample residual band recomputed at {timestamp} against
> the current Block 1, 3, and 4 settings. Central trajectory (red,
> solid) is the live deterministic run under the same settings."

## Figure B copy

Title. "Figure B. Top residual-uncertainty drivers."
Caption. "Residual-uncertainty width over median at {year}. Each bar
reports the Monte Carlo band width divided by the median when only that
single parameter is sampled and every other parameter is fixed. Colour
encodes layer: L1 teal, L2 rust. Block 1 mitigation levers (F23 to
F27), Block 3 assumption parameters (F18, F19, F22, F28), and the
fixed-data anchors (F01, F02) are filtered out because they are not
residual uncertainty."

## Figure C copy

Title. "Figure C. Layer contribution summary (residual layers)."
Reader toggle. "Include L3 for reference (conditional on
target-setting)."
Caption (L3 excluded). "Residual-layer band widths (L1 and L2 only). L3
(mitigation-lever layer) is excluded because L3 parameters are in
Block 1 and define the scenario, not residual uncertainty. Enable the
L3 toggle above to see the mitigation-conditional contribution."

## Outside-the-band table

| Source | In band? |
|--------|----------|
| Mitigation lever positions (Block 1) | No. These define the scenario. |
| Modeling assumptions (Block 3) | No. These are discrete structural choices. |
| Structural shocks | No. Separate labelled scenarios. |
| Missing life-cycle phases (manufacturing, end-of-life) | No. Utility phase only. |
| Residual L1 and L2 priors (Block 4) | Yes, when you click Recompute residual band. |

## Editorial rules applied

- No contractions in body prose.
- Vague qualifiers removed ("roughly", "about", "somewhat").
- Body-prose em-dashes replaced by periods or commas.
- Acronyms spelled on first use: CAV, STI, ATS, BEV, MC (Monte Carlo),
LCA, CARB, CAGR, ZEV, SB, EIA, AFDC, ODOT, TSMO.
- Numbers under 10 as words in body prose; ≥10 as numerals.
- Units typeset with unicode superscripts and subscripts (CO₂,
Mt CO₂ yr⁻¹).

No sentence was flagged as unrewritable.
