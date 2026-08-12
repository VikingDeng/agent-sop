# Frozen frontend authorship fixtures

Each implementation must use the supplied domain facts and visible copy. It may reorganize them but may not invent a new feature, remote asset, or backend claim.

## Cold chain

Build the primary desktop surface for **Relay North**, used by a regional clinic coordinator during a vaccine cold-chain incident. The single job is to decide which shipment needs intervention now.

Required facts: `12 Aug 2026 · 14:32`; shipment `RN-2841`; route `Baguio hub → Sagada Clinic`; contents `MMR · 240 doses`; current temperature `9.4°C`; safe band `2–8°C`; excursion began `14:18`; remaining validated exposure `37 min`; courier `Mara V.`; cooler seal `C-771`; the other shipments `RN-2838 / 4.1°C / stable` and `RN-2844 / 7.6°C / watch`.

Required interaction: selecting a shipment changes the decision detail; `Start intervention` reveals the next three operational actions without pretending an external dispatch occurred. Show stable, warning, selected, and disclosed local-only states. Prioritize the incident over feature inventory.

## Cinema

Build the public program-planning surface for **Afterimage 16**, a three-night independent cinema festival in Iloilo. The single job is to assemble one evening without schedule conflicts.

Required facts: festival dates `28–30 Aug 2026`; venues `Cinematheque Iloilo`, `Casa Real Courtyard`, `Studio B`; films `Salt Letters · 82 min · Ana Rivera`, `The Last Ferry · 104 min · Jo Tan`, `Static Bloom · 67 min · Mika Reyes`; live program `Director Q&A · 21:40`; one explicit content note `strobing light`; limited seat count `18 left` for The Last Ferry.

Required interaction: adding two non-conflicting events produces a visible evening itinerary and total duration; attempting a supplied overlapping event shows a useful conflict message and recovery action. The design must feel rooted in film-program culture without using remote posters or decorative fake film stills.

## Roastery

Build the calibration workbench for **Tide Table Coffee**, used by a production roaster comparing today’s roast against an approved profile. The single job is to decide whether batch `TT-260812-B` can be released.

Required facts: coffee `Ethiopia · Hamasho · natural`; batch mass `24.0 kg`; charge `198°C`; first crack `08:42`; drop `10:31`; development ratio `16.9%`; approved band `15.5–17.0%`; color target `Agtron 63 ± 2`; measured color `66`; notes `jasmine / peach / black tea`; reference batch `TT-260805-A`; operator `Lio`; one finding `color is 1 point outside release band`.

Required interaction: switching between `Curve`, `Milestones`, and `Release check` changes the working view; the release action is blocked until the operator records a disposition, after which the UI states that the decision is only stored locally. Use believable production language and data hierarchy rather than generic KPI cards.
