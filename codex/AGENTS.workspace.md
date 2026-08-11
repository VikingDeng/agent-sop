# Workspace overlay

## Workflow authority

- `/Users/viking/code/agent-sop` is the source of truth for reusable workflow, project skeletons, Codex agent recipes, and the Research Execution Grill.
- `/Users/viking/ops` is workstation automation only. Old Claude and retired Research OS material are not active workflow authority.
- `~/.codex` is installed runtime output; edit the corresponding source in `agent-sop` first when one exists.
- When a ContestOS v1 skeleton is selected, `~/.codex/runtime-current/skeletons/contestos-adaptive-overlay-v2.md` is the active runtime overlay; preserve the v1 provenance-locked files.

## Local operating preferences

- Use Codex and GPT models only.
- Optimize `25*Sol + 10*Terra + 1*Luna` while preserving the requested quality. Prefer Luna for substantial mechanical work, Terra for semantic/debugging pressure and ordinary independent review, and Sol for architecture, research design, ambiguity, and final judgment. Codex role-model unavailability permits a transparent lowest-cost routing fallback; this does not authorize model/backend fallback inside evidence-bearing research code and is not by itself a project gate.
- Treat workflow steps, role recipes, package markers, and review counts as adaptive defaults unless the closest project instructions explicitly select a strict profile.
- Skills are optional and replaceable adapters; their presence, version, or hash is not a normal completion gate, and they cannot change SOP authorization, acceptance, claims, HUMAN boundaries, or required stages.
- Treat “zero fallback” in a selected v1 skeleton as the overlay’s prohibition on silent semantic degradation, fabricated success, and altered acceptance—not as a ban on explicit, quality-equivalent alternatives.
- Treat a user-supplied proposal as approved. Use the adaptive Research Execution Grill before implementation and material scale; do not generate replacement ideas unless requested. Select only gates relevant to the proposal. The signed v3 event-ledger profile is opt-in for projects that need externally auditable authorization.

## Workspace layout

- Use `/Users/viking/code` for projects, `/Users/viking/runs` for worktree runs, `/Users/viking/notes` for notes, and `/Users/viking/papers` for literature assets.
- There is no active `/Users/viking/research` workspace. Do not recreate it unless explicitly requested.
- Preserve user changes, secrets, and recoverable data. Follow the closest project-level `AGENTS.md` for repository-specific rules.

## Research compute profile

- The current default research compute target is the Ubuntu server at `156.236.73.44`. Resolve its alias, user, key, workspace root, GPU inventory, and current availability through SSH config plus `/Users/viking/ops`; never put credentials or private-key material in this repository or logs.
- When a project contract already authorizes this host, a bounded GPU/resource budget, and a project workspace, resource inspection and ordinary execution use an `AUTONOMOUS_CHECKPOINT`; do not ask for ritual confirmation of host/card/path. A new host, new credentials, shared-resource conflict, unbounded/materially larger spend, destructive cleanup, or production/public action remains a HUMAN boundary.
- Keep code in Git, build the locked compute environment and download pinned models/data on the server, and write only inside the authorized remote workspace/data root. Local Mac work is control-plane editing and lightweight code-readiness validation, not a silent CPU substitute for a failed remote scientific run.
- Evidence-bearing remote runs are fail-fast and retain immutable raw artifacts, logs, command, PID/session, host/GPU identity, repo state, environment, cost, status, and output location. Do not auto-switch to local/CPU/another backend or host; any equivalent alternative is a new explicit run.
