# agent-sop repository instructions

## Scope and authority

This file governs maintenance of this repository. Read `PRINCIPLES.md` first and use `sop/_METHODOLOGY.md` as a quality guide. Load only the SOPs and references that support the current decision; do not load the whole library for safety theater.

Treat user-supplied research proposals as approved directions unless idea generation is requested. Route implementation and material scale through the adaptive `sop/tier1-skeleton/research-execution-grill.md`; the signed v3 profile is opt-in, not the universal path.

## Outcome-driven work

Follow `sop/tier0-core/autonomous-supervisor.md`. Freeze the desired outcome, non-goals, scope, quality bar, and observable evidence, then let the agent choose exploration order, tools, models, decomposition, and useful repair loops. Recipe steps and coordination metadata are defaults unless a strict profile is explicitly selected.

Use a HUMAN gate only for a real unauthorized direction: materially different semantics or research claim, public API/compatibility, credentials, production/public release, deletion or irreversible migration, significant unbounded spend, legal/privacy choices, or a direct contract conflict. Continue independent safe work when possible.

## Delegation and verification

Optimize `25*Sol + 10*Terra + 1*Luna` without weakening acceptance. Prefer Luna for bounded mechanical execution, Terra for semantic/debugging pressure and ordinary review, and Sol for architecture, research design, ambiguity, and final judgment. Model unavailability permits a transparent lowest-cost fallback. Avoid tiny command-level delegation, full-context forks, repeated polling, overlapping writers, and unnecessary agent count.

Use real outputs as evidence. Choose verification and review depth according to the claim and failure cost; do not require independent review as ceremony. Never fabricate evidence, hide failed checks, silently lower acceptance, overwrite unrelated user changes, or call internal GPT/Codex review external.

## Repository checks and delivery

For repository changes, run `python3 scripts/validate_sop_repo.py`, `git diff --check`, and tests relevant to changed executable surfaces. Preserve user changes. Do not reset, force-push, bypass hooks, edit authentication/provider settings, write directly to `main`, merge automatically, or perform irreversible delivery without authorization.

Material SOP changes increment their version and keep index metadata synchronized. Existing skeleton source artifacts marked provenance-locked remain unedited. Final reporting states actual changes, checks, meaningful review findings, remaining risks, and Git state.
