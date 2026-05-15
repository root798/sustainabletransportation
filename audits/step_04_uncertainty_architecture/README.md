# step_04_uncertainty_architecture

Checkpoint audit before the CA/OH L2 redesign, full CA/OH L2 backend implementation, U.S. Average forensic trace, and mechanical source-of-truth back-door fixes.

## Files

| file | purpose |
| --- | --- |
| `CHECKPOINT_SOURCE_OF_TRUTH_AUDIT.md` | Verifies that `scenarios/{region}/scenario.json` is genuinely the primary read path; enumerates remaining back-doors. |
| `CHECKPOINT_REMAINING_NUMBERS_AUDIT.md` | Re-audit of the three unresolved concerns: US avg anomaly, deferred L2, saturation behaviour. |
| `CHECKPOINT_REMAINING_NUMBERS.csv` | Machine-readable tally of remaining suspect numbers. |
| `CHECKPOINT_DESIGN_CONSTRAINTS.md` | Constraints the next redesign must respect. |
| `CA_OH_L2_REVIEW.md` | Review of deterministic vs uncertain items for CA and OH only. |
| `CA_OH_L2_DESIGN.md` | Final L2 design (per-level × per-subsystem scale factors, Dirichlet level mixes, cohort decay). |
| `CA_OH_L2_VALIDATION.md` | Evidence of bit-reproducible baseline, bit-reproducible MC, widened bands, saturation sidecar. |
| `US_AVERAGE_SOURCE_TRACE.md` | Per-cell forensic trace of the 18 U.S. Average consumption cells. |
| `SOURCE_OF_TRUTH_BACKDOOR_FIXES.md` | Mechanical fixes to the four active loaders / region-discovery paths. |
| `US_AVERAGE_TRACE_VALIDATION.md` | End-to-end verification of loader priority and quarantine status. |

## Key outcomes

- California and Ohio gain 12 new L2 priors per region (per-level × per-subsystem lognormals), Dirichlet level mixes, cohort-decay prior.
- Post-L2 bands widen 9 – 28 % across every CA/OH metric sampled.
- Interpretation boundary moves to **2030 (California)** and **2031 (Ohio)**.
- U.S. Average consumption-rate anomaly is documented cell-by-cell and quarantined from paper-facing comparison.
- Every active loader (CLI + v3 dashboard core + v4 core + v3 data_contracts) prefers `scenarios/` over `configs/`.
