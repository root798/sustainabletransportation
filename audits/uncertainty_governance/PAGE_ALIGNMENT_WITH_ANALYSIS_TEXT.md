# PAGE_ALIGNMENT_WITH_ANALYSIS_TEXT.md

**Date:** 2026-04-15
**Purpose:** verify the final Scenario Explorer page reflects the current analysis narrative.

---

## 1. Hardware Energy Efficiency Doubling Year

**Analysis text says:** fleet-level effective compute-efficiency proxy, not a vendor-specific roadmap.

**Page treatment:** the slider in Section A carries the help text "Fleet-level effective compute-efficiency proxy: years for the average ECAV computing power per vehicle to halve. Not a vendor-specific roadmap number." This matches.

The uncertainty parameter F27 is one of the five with full LMH and is flagged as the top turning-year destabiliser in the Figure B driver cards. This reflects the analysis finding that efficiency-doubling is the single largest turning-year uncertainty driver (16-year spread in isolated MC).

**Aligned: yes.**

## 2. EAV and STI adoption growth / target assumptions

**Analysis text says:** key policy-design levers that should be prominent.

**Page treatment:** CAV target by 2075 and STI coverage target by 2075 are the first two sliders in Section A ("Scenario design levers"), always visible and labelled as "Key policy-design lever". They carry full LMH uncertainty radios (F23, F24). The annual BEV-share growth and clean-energy growth are immediately below.

**Aligned: yes.**

## 3. Renewable / low-carbon electricity growth

**Analysis text says:** key grid-policy lever that should be prominent.

**Page treatment:** "Annual low-carbon electricity share growth" is the fourth slider in Section A with help "Key grid-policy lever." The uncertainty parameter F26 carries full LMH and is called out as the primary interpretation-boundary driver in the analysis.

**Aligned: yes.**

## 4. Initial measured shares are baseline assumptions, not equal-status scenario design controls

**Analysis text says:** initial shares are regionally measured and should not be presented as equal-status to the policy-design levers.

**Page treatment:** "Initial low-carbon electricity share", "Initial BEV share", "Initial vehicle stock", and "Convertible intersections" are in Section B ("Baseline assumptions"), collapsed by default, with a caption stating "These are fixed-by-default baseline conditions. They are not scenario-design levers." The uncertainty parameters F01, F02 for these are in the {fixed, low} allowed set with default=fixed and a reason text citing measurement-grade EIA/AFDC data.

**Previous page conflicted:** the old page placed all 11 CONTROL_SPECS entries in one flat expander as equally prominent sliders. This has been corrected.

**Aligned: yes.**

## 5. Retire year and fleet growth

**Analysis text says:** these are fleet-demographic assumptions, not scenario-policy levers.

**Page treatment:** retire_year and fleet_growth_rate are in Section B (baseline assumptions), collapsed by default. Retire_year's uncertainty radio (F22) is `{fixed, low, medium}`; fleet growth (F28) is `{fixed, low}`. Neither appears in Section A.

**Aligned: yes.**

## 6. Summary

Every previously identified analysis-text alignment issue is now resolved on the final page:

| Issue | Was | Now |
|---|---|---|
| Efficiency doubling not identified as fleet-level proxy | Generic slider label | "Fleet-level effective compute-efficiency proxy" help text |
| EAV/STI targets not prominent enough | Same-level as baseline | Section A, always visible, first two sliders |
| Renewable electricity not labelled as grid-policy lever | No label | "Key grid-policy lever" help text |
| Initial measured shares as equal-status | Same flat expander | Section B, collapsed, "not scenario-design levers" |

No further page–analysis alignment issues identified.
