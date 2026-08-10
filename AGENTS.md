# agent-sop repository instructions

## Scope and authority

This file governs maintenance of this repository. Read `PRINCIPLES.md` first and use `sop/_METHODOLOGY.md` as a quality guide. Load only the SOPs and references that support the current decision; do not load the whole library for safety theater.

Treat user-supplied research proposals as approved directions unless idea generation is requested. Route implementation and material scale through the adaptive `sop/tier1-skeleton/research-execution-grill.md`; the signed v3 profile is opt-in, not the universal path.

## Outcome-driven work

Follow `sop/tier0-core/autonomous-supervisor.md`. Freeze the desired outcome, non-goals, scope, quality bar, and observable evidence, then let the agent choose exploration order, tools, models, decomposition, and useful repair loops. Recipe steps and coordination metadata are defaults unless a strict profile is explicitly selected.

SOP 与 Skill/MCP 正交：SOP 负责结果契约、授权/风险边界、证据、停止/re-contract 与交付；Skill/MCP 只提供按需的领域、格式或工具能力，不能改写验收、claim、HUMAN 边界或制造固定阶段。

Use a HUMAN gate only for a real unauthorized direction: materially different semantics or research claim, public API/compatibility, credentials, production/public release, deletion or irreversible migration, significant unbounded spend, legal/privacy choices, or a direct contract conflict. Continue independent safe work when possible.

When a ContestOS v1 skeleton is selected, also apply [`skeletons/contestos-adaptive-overlay-v2.md`](skeletons/contestos-adaptive-overlay-v2.md). The overlay is the active runtime authority for fallback semantics, HUMAN checkpoints, ecosystem parameters, and claim/risk-triggered gates; the v1 source files remain provenance-locked.

## Delegation and verification

Optimize `25*Sol + 10*Terra + 1*Luna` without weakening acceptance. Prefer Luna for bounded mechanical execution, Terra for semantic/debugging pressure and ordinary review, and Sol for architecture, research design, ambiguity, and final judgment. Model unavailability permits a transparent lowest-cost fallback. Avoid tiny command-level delegation, full-context forks, repeated polling, overlapping writers, and unnecessary agent count.

Use real outputs as evidence. Choose verification and review depth according to the claim and failure cost; do not require independent review as ceremony. The universal gate is claim/contract↔evidence closure with no overclaim; reproduction, contamination, statistics, performance, and security checks are triggered by the claim or risk. Never fabricate evidence, hide failed checks, silently lower acceptance, overwrite unrelated user changes, or call internal GPT/Codex review external.

没有具体且合理的失败路径不引入机制；优先 native primitive 和最便宜的 discriminating oracle，guardrail 成本与潜在伤害成比例。Review 不能以品味扩大冻结 acceptance；新的可信失败路径只能触发合并修复或架构重置，不能无限追加门禁。

## Repository checks and delivery

For repository changes, run `python3 scripts/validate_sop_repo.py`, `git diff --check`, and tests relevant to changed executable surfaces. Preserve user changes. Do not reset, force-push, bypass hooks, edit authentication/provider settings, write directly to `main`, merge automatically, or perform irreversible delivery without authorization.

Material SOP changes increment their version and keep index metadata synchronized. Existing skeleton source artifacts marked provenance-locked remain unedited. Final reporting states actual changes, checks, meaningful review findings, remaining risks, and Git state.
