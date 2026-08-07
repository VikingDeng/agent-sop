# agent-sop repository instructions

## Scope

This file governs maintenance of this repository. It is a dispatcher, not a copy of the SOP library and not a replacement for personal `~/.codex/AGENTS.md` guidance.

## Read and route

1. Read `PRINCIPLES.md` first. P1–P4 are non-negotiable.
2. Read `sop/_METHODOLOGY.md` before creating or materially changing an SOP. Every SOP must satisfy A1–A7.
3. Use `sop/README.md` to select only the SOPs that match the task, then load their declared dependencies. Do not load every SOP for safety theater.
4. Read `PROSE_STANDARD.md` only when producing or reviewing human-facing prose.
5. For project-shaped work, choose a skeleton from `skeletons/README.md`. Treat the three `contestos-*-v1.md` files as provenance-locked source artifacts: do not edit them in place. Express runtime changes through an SOP, README overlay, or a new explicitly versioned skeleton.
6. Treat user-supplied research proposals as approved directions unless idea generation is explicitly requested. Before implementation or material scale-up, route through `sop/tier1-skeleton/research-execution-grill.md`.

## Autonomous execution and checkpoints

Follow `sop/tier0-core/autonomous-supervisor.md`. Classify work as trivial, standard, or high-risk; freeze a task contract before editing; and continue through implementation, verification, review, and bounded repair when the user's goal and acceptance criteria are clear and the work stays inside the authorized workspace.

A HUMAN gate is for a real direction decision: materially different product semantics, public API or compatibility changes, major production dependencies, credentials, production release, destructive or irreversible operations, significant unbounded spend, legal/privacy choices, or a missing requirement that can only be guessed. Do not ask for routine confirmation after presenting a plan. Record whether a checkpoint was interactive, autonomous, or mandatory-human.

## Delegation

Use the lowest-cost role that can reliably complete a bounded work package. Do not delegate trivial work mechanically. A work package must state its objective, allowed and forbidden scope, relevant files, invariants, acceptance criteria, validation commands, escalation conditions, and expected evidence.

Keep the main agent responsible for architecture and final decisions. Prefer a targeted read-only explorer for unfamiliar paths, a worker for bounded implementation, a verifier for real commands, and an independent reviewer for behavior changes. Default to at most two concurrent subagents and one repair-review loop. Only one writer may own a file at a time. An escalation must record the failed role, reason, evidence, new role, scope change, and any acceptance-criteria change; silent role substitution is forbidden.

## Verification and review

- Build independent oracles according to `sop/tier0-core/build-oracle.md`; implementation self-report is not proof.
- Review failure paths with `sop/tier0-core/no-fallback-review.md`. A failed scan, missing reviewer, or unavailable oracle is a reported failure or limitation, never an implicit pass.
- Run `python3 scripts/validate_sop_repo.py` and `git diff --check` for repository changes. Run any additional check required by the changed surface.
- Reviewers are read-only with respect to the object under review. Findings need severity, location, failure path, and a minimal fix. Resolve high-severity findings before delivery.
- Final reports list only commands and reviews that actually ran, with their real results.

## SOP maintenance

- New SOPs use `sop/_TEMPLATE.md`, retain all eight required fields, declare layer/discipline/skeleton/universality/version metadata, and update `sop/README.md` in the same change.
- Discipline declarations must have concrete P1–P4 actions in the SOP body. Dependencies are references, not copied prose.
- Material SOP changes increment the SOP version and keep index metadata synchronized.
- Human-facing text follows `PROSE_STANDARD.md`; do not let style-only findings block an otherwise correct change.

## Git safety and delivery

Preserve user changes. Do not reset, silently stash, force-push, bypass hooks, use `--no-verify`, commit secrets, edit authentication/provider settings, write directly to `main`, or merge a PR automatically. Keep commits single-purpose and traceable to the task. Before commit, confirm the diff contains only intended files; then follow `sop/tier0-core/commit-and-pr.md`.
