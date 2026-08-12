# Blind visual review

The reviewer received only the frozen briefs, anonymous desktop/mobile captures, and functional evidence. Candidate labels were shuffled independently per fixture; the mapping was opened only after this review completed.

| Fixture / candidate | Specificity | Hierarchy | Type | Layout | Content | Responsive | Interaction | Finish | Mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Cold chain A | 9.7 | 9.7 | 9.6 | 9.5 | 9.5 | 9.4 | 9.4 | 9.6 | 9.6 |
| Cold chain B | 7.6 | 7.8 | 7.4 | 7.9 | 7.8 | 7.3 | 8.0 | 7.4 | 7.7 |
| Cold chain C | 8.7 | 9.0 | 8.6 | 8.9 | 9.0 | 5.8 | 9.0 | 8.8 | 8.5 |
| Cinema A | 9.6 | 9.2 | 9.5 | 9.1 | 9.5 | 9.0 | 9.1 | 9.4 | 9.3 |
| Cinema B | 9.4 | 9.0 | 9.4 | 9.5 | 9.4 | 9.4 | 8.9 | 9.5 | 9.3 |
| Cinema C | 7.8 | 8.5 | 8.0 | 8.3 | 8.6 | 7.0 | 8.7 | 7.9 | 8.1 |
| Roastery A | 9.7 | 9.1 | 9.5 | 9.4 | 9.3 | 9.0 | 8.8 | 9.5 | 9.3 |
| Roastery B | 8.9 | 8.6 | 8.6 | 8.8 | 9.4 | 8.9 | 8.5 | 8.8 | 8.8 |
| Roastery C | 9.5 | 9.4 | 9.0 | 9.3 | 9.6 | 9.3 | 9.0 | 9.4 | 9.3 |

## Evidence notes

- **Cold chain A:** The editorial incident-desk treatment makes the intervention decision unmistakably primary. Temperature, safe band, exposure window, and the CTA read in a strong sequence; mobile preserves that clarity.
- **Cold chain B:** The shipment and temperature gauge are clear, but muted gray type and pale panels reduce urgency. It reads more like a reusable monitoring dashboard than a high-stakes incident tool.
- **Cold chain C:** The alert treatment, temperature-band visualization, and local-review CTA are strong. Mobile shipment cards visibly extend horizontally, compromising responsive execution.
- **Cinema A:** The dark palette, program typography, time-led listing, and itinerary rail feel rooted in independent-film culture. Metadata, capacity, content note, and add affordances remain clear on mobile.
- **Cinema B:** The theatrical headline, calendar tabs, halftone field, and distinct evening state give this excellent festival character. Desktop is particularly accomplished and mobile remains coherent.
- **Cinema C:** The schedule, actions, and itinerary are clear, but the surface is comparatively generic. Mobile has cramped time/title joins such as `18:30Salt Letters`.
- **Roastery A:** Calibration-sheet styling, coffee notes, profile chart, and tabs make this purpose-built for roasting. Desktop is balanced and mobile preserves hierarchy.
- **Roastery B:** Agtron target and measured color give the decision factual grounding. The layout is competent but uses a more familiar dashboard/workbench composition.
- **Roastery C:** The hold callout frames the release decision immediately; the paired curve and milestones reinforce production context. The chart scales credibly to mobile.

## Anonymous ranking

1. Cold chain: A, C, B.
2. Cinema: B, A, C.
3. Roastery: C, A, B.

Cold chain C had the only acceptance regression: horizontal overflow at 390 px. Because anonymous labels were reshuffled per fixture, they are not aggregated across fixtures; arm-level means are computed only after unblinding.

## Unblinded result

| Arm | Cold chain | Cinema | Roastery | Exact dimension mean |
|---|---:|---:|---:|---:|
| Strong no-Skill | 8.4750 | 9.3125 | 8.8125 | **8.8667** |
| Minimal reminder | 9.5500 | 9.3000 | 9.2875 | **9.3792** |
| Full pinned Skill | 7.6500 | 8.1000 | 9.3125 | **8.3542** |

The full Skill scored `-0.5125` versus strong no-Skill and `-1.0250` versus the minimal reminder, so it failed both pre-frozen quality thresholds. The minimal reminder scored `+0.5125` over strong no-Skill and had no acceptance regression; its core constraint is therefore encoded in Development Profile v2 rather than installing the larger Skill.
