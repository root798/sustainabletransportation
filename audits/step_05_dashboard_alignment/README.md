# step_05_dashboard_alignment

Interpretation-boundary formalization, saturation-caveat evidence, figure-support requirements, reviewer-response support, and Phase-2 dashboard implementation.

## Files

| file | purpose |
| --- | --- |
| `CA_OH_INTERPRETATION_BOUNDARY.md` | Exact boundary definition, why CA moved 2033→2030, why OH moved 2035→2031, wording for Methods and Results. |
| `CA_OH_SATURATION_EVIDENCE.md` | Saturation-collapse inventory from the metadata sidecars, wording for figure captions and Methods caveats. |
| `CA_OH_FIGURE_SUPPORT.md` | Plotting requirements for CA/OH paper figures; what must be annotated. |
| `CA_OH_REVIEWER_RESPONSE_SUPPORT.md` | Draft response language for the long-term-predictability criticism. |
| `STEP_05B_DASHBOARD_IMPLEMENTATION.md` | Implementation log for Phase-2 dashboard edits (post-boundary shading, saturation markers, modelled-peak labels, Ohio "Not reached in horizon", US avg quarantine banners). |
| `FRONTEND_VALIDATION_PHASE2.md` | Validation of the Phase-2 dashboard edits: boundary consistency, saturation consistency, turning-year consistency, overlay honesty, US avg restriction, human-verification checklist. |

## Key outcomes

- Single backend source of truth for the interpretation boundary; both dashboards import it.
- Saturation sidecar JSON is consumed by v4 dashboard pages; figure captions auto-include the cap-artefact clause.
- Ohio turning year renders as "Not reached in horizon" across all codepaths; never numeric, never blank.
- U.S. Average quarantine banner is unmissable on every page that renders US avg data.
- Paper-figure export CLI emits PDF + PNG + caption `.txt` for CA and OH only.
