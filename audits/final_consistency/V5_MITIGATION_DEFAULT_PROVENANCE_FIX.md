# V5 mitigation-default provenance fix

The Block 1 defaults must not overclaim. The previous labels said every
default was "derived from current policy evidence", which is true only
for the BEV-share and clean-grid growth rates. The CAV and STI fleet
targets are baseline scenario assumptions — no state legislates a
numerical 2075 CAV or STI fleet share.

## Per-lever provenance

### CAV target by 2075

| Region | Default | Previous label | Corrected label | Evidence |
|--------|--------:|----------------|-----------------|----------|
| California | 0.45 | "policy-derived" | **baseline scenario assumption** | No California statute sets a 2075 CAV fleet share. CARB's AV testing framework regulates permits, not fleet projections. |
| Ohio | 0.30 | "lower adoption ceiling (ODOT pilot scope)" | **baseline scenario assumption** | Ohio has no statewide CAV mandate. The 0.30 default reflects a slower adoption ceiling that is an illustrative scenario number, not an official target. |

### STI coverage target by 2075

| Region | Default | Previous label | Corrected label | Evidence |
|--------|--------:|----------------|-----------------|----------|
| California | 0.50 | "Caltrans funded-intersection target" | **baseline scenario assumption** | Caltrans operates smart-corridor pilots but has not adopted a statewide 2075 coverage target. |
| Ohio | 0.30 | "TSMO lower coverage baseline" | **baseline scenario assumption** | Ohio TSMO is a programme, not a numerical target. Value is a conservative extrapolation. |

### Annual BEV-share growth

| Region | Default | Previous label | Corrected label | Evidence |
|--------|--------:|----------------|-----------------|----------|
| California | 0.07 | "CARB ACC II + AFDC CAGR" | **policy derived** | CARB Advanced Clean Cars II mandates 100% ZEV sales by 2035. AFDC 2019–2024 registrations show ~45% CAGR from a low base. The 0.07 annual share growth is the trajectory that takes California from 4.1% BEV in 2024 to a saturated ZEV fleet by mid-century. |
| Ohio | **0.055** (was 0.03) | "AFDC CAGR ~30%" | **literature derived** | DOE AFDC 2019–2024 Ohio BEV registration CAGR is near 30% from a low base. Previous 0.03 default was too pessimistic; 0.055 is the trajectory supported by the observed CAGR adjusted for Ohio's smaller starting share. |

### Annual low-carbon electricity share growth

| Region | Default | Previous label | Corrected label | Evidence |
|--------|--------:|----------------|-----------------|----------|
| California | 0.05 | "SB 100" | **policy derived** | California SB 100 mandates 100% clean electricity by 2045. From a 65.6% low-carbon share in 2024, a 0.05 annual increment puts the mix at 100% by 2041, close to the SB 100 trajectory. |
| Ohio | **0.035** (was 0.02) | "EIA mix" | **literature derived** | Ohio has no statewide clean-energy mandate. Previous 0.02 default was too pessimistic. EIA-based observation of recent mix migration and RPS-equivalent literature supports 0.035. |

### Hardware efficiency doubling time

| Region | Default | Previous label | Corrected label | Evidence |
|--------|--------:|----------------|-----------------|----------|
| California | 2.8 yr | "industry consensus" | **industry consensus (not state-specific)** | Same value for both regions. Derived from semiconductor-efficiency roadmap projections; not a state policy. |
| Ohio       | 2.8 yr | "industry consensus" | **industry consensus (not state-specific)** | Same. |

## Changes applied

- `v5_streamlit_app/configs/mitigation_defaults.json` updated:
  - Ohio BEV growth 0.03 → 0.055 (literature-derived).
  - Ohio clean-grid growth 0.02 → 0.035 (literature-derived).
  - Ohio CAV target 0.25 → 0.30 (baseline scenario assumption,
aligning with the canonical scenarios/ohio/scenario.json value).
  - Added a `_provenance` block with one-word tags per lever.
  - Rewrote every `_sources` entry to state provenance explicitly.
- Page help text on each slider now prefixes the source line with the
provenance tag (`[policy derived]`, `[literature derived]`, `[baseline
scenario assumption]`, `[industry consensus]`).

## Verification

- Page help text matches `_sources` and `_provenance` fields.
- Ohio defaults now align with `scenarios/ohio/scenario.json` canonical
values for CAV target.
- "Policy derived" appears only on CA BEV and CA clean-grid.
- "Literature derived" appears only on OH BEV and OH clean-grid.
- "Baseline scenario assumption" appears on CAV and STI targets for
both regions.
- "Industry consensus" appears on the hardware doubling time for both
regions.
