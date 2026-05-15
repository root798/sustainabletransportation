# Figure B defensive caption and leverage text

## Risk

Figure B previously could be misread as claiming that the top-ranked
parameter (for example F09, ECAV sensing scale factor) is the single
largest contributor to ATS-emission uncertainty. The top mitigation
levers (F23 to F27) are no longer in the ranking because the v5.1
page filters the residual-only view, but a reviewer skimming the
ranking without the caption could easily miss that context.

## Mitigation

Two belt-and-suspenders copy changes applied to the v5.1.1 page.

### 1. New yellow-bulb caption directly under the Figure B subheader

> "**Read this ranking carefully.** This chart shows only the
> residual uncertainty that remains **after Block 1 mitigation levers
> are fixed at the reader's chosen target values and after Block 3
> assumption parameters are held at their structural choices**. The
> top-ranked parameter here is not a new empirical finding that
> displaces the known dominance of the mitigation levers; it is the
> largest residual contributor *conditional on having already made
> scenario and structural decisions*. To see the predictive
> uncertainty when the scenario itself is uncertain, switch Figure A
> to Scenario envelope."

This text appears above the bar chart and cannot be collapsed.

### 2. Existing Figure B caption under the chart (already present)

> "Residual-uncertainty width over median at {year}. ... Block 1
> mitigation levers (F23 to F27), Block 3 assumption parameters
> (F18, F19, F22, F28), and the fixed-data anchors (F01, F02) are
> filtered out because they are not residual uncertainty."

### 3. Mitigation leverage block now distinguishes the two rankings

The "Mitigation leverage" section below the figures now says:

> "Adjust any lever in the sidebar, then click Recompute residual band
> in Figure A to see the band conditional on the new scenario. Block
> 1 leverage is separate from Figure B's residual ranking. Figure B
> answers: given a scenario, which residual parameter is the biggest
> remaining uncertainty? The lever ranking below answers: which Block
> 1 lever moves the central trajectory the most when you change it?"

## Effect on reviewer reading

A reviewer who reads Figure B now sees three reinforcing signals:

1. The in-caption disclaimer (always visible).
2. The below-chart caption naming every filtered-out class.
3. The mitigation-leverage text calling out that Block 1 leverage is a
separate ranking.

The "F09 top driver" line is therefore not misreadable as an empirical
claim about the dominance of ECAV sensing scale factor in absolute
terms.

## No code bug to fix

Figure B's data pipeline already uses the dual-region
`PARAMETER_CONTRIBUTION_EXPERIMENT.csv` filtered to the residual-only
parameter set. The only change is copy.
