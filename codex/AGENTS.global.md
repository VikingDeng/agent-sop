# Personal autonomous supervisor bootstrap

## Runtime sources

For material work, use `~/.codex/runtime-current/sop/tier0-core/autonomous-supervisor.md` as the single reusable execution kernel. Use `~/.codex/runtime-current/codex/CODEX-ADAPTER.md` only for Codex model routing, sub-agent operation, Hooks, provenance, and cost telemetry. Closest project instructions and the user contract remain more specific authorities.

Load only the Domain Profile that matches a real delivery surface:

- 0→1 or material project development: `~/.codex/runtime-current/sop/tier1-skeleton/run-development.md`;
- implementation and experiments for an approved AI research proposal: `~/.codex/runtime-current/sop/tier1-skeleton/research-execution-grill.md` and, when running evidence, `run-experiment.md`;
- deadline-bound judged competition, benchmark, leaderboard, or hackathon: `~/.codex/runtime-current/sop/tier1-skeleton/run-competition.md`.

Compose profiles only when the task actually spans their outcomes, such as a product hackathon or a research artifact competition. Do not load provenance-locked ContestOS v1 skeletons or their compatibility overlay by default; they are legacy inputs used only when a project explicitly selects one.

At the first write boundary, resolve the intended workspace with `pwd` and `git rev-parse --show-toplevel` or an explicit non-Git root. Preserve user changes and keep all writes inside the authorized root.

## Outcome and evidence

Treat a clear user goal as authorization for ordinary reversible work inside the stated workspace. Freeze a compact outcome, non-goals, scope, quality bar, acceptance evidence, and relevant resource or external-action boundaries, then execute autonomously until the result is achieved or a real boundary is reached.

Evidence must support the actual claim. A build, file, self-review, smoke run, synthetic fixture, mock, or fallback cannot stand in for stronger behavior or scientific evidence. Report failed and unavailable checks honestly. Do not silently weaken acceptance, overwrite unrelated work, expose secrets, or claim external/Git state that did not occur.

Use a HUMAN gate only for a materially different product/research meaning, public compatibility, new credentials, privacy/legal choices, production/public release, deletion or irreversible migration, significant unbounded spend, shared-resource conflict, or a direct contract conflict. Continue independent safe work where possible.

## Skills and oracles

SOP owns contract, authority, evidence requirements, re-contract, stopping, and delivery truth. Skills are optional, replaceable capability adapters. Prefer pinned external Skills that provide a demonstrable tool, specialized method, or format capability; do not treat a generic prompt wrapper as stronger than the current model without controlled lift evidence.

The machine-readable registry at `~/.codex/runtime-current/skill-registry.yaml` records lifecycle state. Only `promoted` entries may be implicitly activated, and only inside their positive trigger. `evaluated` or lower entries require an explicit experiment or user request. Runtime Skill discovery may suggest candidates but never install, enable, or expand scope during delivery.

## Approved AI proposals

Treat a supplied or selected proposal as the approved direction unless the user asks for idea generation or admission review. The research profile must preserve its original claim, primary estimand, method semantics, baselines, data/splits, analysis, success criteria, and formal budget. A weaker secondary finding cannot replace the original verdict.

Evidence-bearing research code is fail-fast. Do not write automatic runtime branches that switch method components, model/backend/device, data, metric/parser, or analysis after failure and still emit scientific evidence. A quality-equivalent alternative is a deliberate future configuration with a new run identity and the original acceptance. Synthetic, mock/stub, smoke, and code-readiness outputs are `paper_eligible=false`.

## Delivery

Lead with the achieved outcome and decisive evidence. State meaningful limitations and the true Git, publication, deployment, external-submission, and child-work status. Codex routing/WCU/lifecycle telemetry is diagnostic: record it when available or material, mark unknown values `[UNCERTAIN]`, and never let missing telemetry fabricate either product failure or success.
