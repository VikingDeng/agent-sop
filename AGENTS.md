# agent-sop repository instructions

## Scope and authority

This file governs maintenance of this repository. Read `PRINCIPLES.md`, then use `sop/_METHODOLOGY.md` to evaluate SOP document quality. `sop/tier0-core/autonomous-supervisor.md` is the single runtime kernel; `codex/CODEX-ADAPTER.md` contains Codex-specific routing and telemetry. Do not duplicate either policy in a Domain Profile, Skill, test, or README.

Load only files needed for the current decision. The three ContestOS v1 skeletons are provenance-locked legacy sources. Do not edit them and do not place them in the default runtime path; their compatibility overlay is used only when a project explicitly selects a legacy skeleton.

## Layer boundaries

- Kernel: outcome contract, contextual-intent evidence routing, scoped preference semantics, authority/risk, evidence strength, re-contract, stopping, and delivery truth.
- Domain Profile: only invariants that are necessary across the named class of tasks.
- Codex Adapter: models, WCU, roles, sub-agent lifecycle, native HUMAN interaction, Hooks, installer, and session audit.
- Skill: external, optional, replaceable capability; it cannot route work or modify acceptance.
- Oracle: independent evidence from real execution, checker, browser, profiler, evaluator, or justified analysis.

Treat user-supplied research proposals as approved directions unless idea generation is requested. Implementation and material scale use `sop/tier1-skeleton/research-execution-grill.md`; the signed v3 protocol is an opt-in high-assurance profile, not the normal path.

## Repository work

Before the first write, confirm this repository root and preserve all existing user changes. Use `apply_patch` for edits. Material SOP changes increment their version and keep `sop/README.md`, root documentation, runtime snapshots, and semantic tests synchronized.

Tests should verify meaningful layer and evidence invariants, not exact prose copied across files. A passing structural validator does not establish end-to-end quality; do not encode product-specific checklists into the universal Kernel merely to make a failed fixture pass.

For repository changes run `python3 scripts/validate_sop_repo.py`, `python3 -m unittest discover -s tests -p 'test_*.py'`, and `git diff --check`. Add a focused behavioral or E2E check when executable behavior changes.

## Delivery

Do not reset, force-push, bypass hooks, change provider authentication, or write directly to the default branch. Commit and merge only when the user authorizes them. Report the actual diff, validation, remaining empirical gaps, and Git/PR state.
