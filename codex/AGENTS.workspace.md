# Workspace overlay

## Workflow authority

- `/Users/viking/code/agent-sop` is the source of truth for reusable workflow, project skeletons, Codex agent recipes, and the Research Execution Grill.
- `/Users/viking/ops` is workstation automation only. Old Claude and retired Research OS material are not active workflow authority.
- `~/.codex` is installed runtime output; edit the corresponding source in `agent-sop` first when one exists.

## Local operating preferences

- Use Codex and GPT models only.
- Optimize `25*Sol + 10*Terra + 1*Luna` while preserving the requested quality. Prefer Luna for substantial mechanical work, Terra for semantic/debugging pressure and ordinary independent review, and Sol for architecture, research design, ambiguity, and final judgment. Model unavailability permits a transparent lowest-cost fallback; it is not by itself a project gate.
- Treat workflow steps, role recipes, package markers, and review counts as adaptive defaults unless the closest project instructions explicitly select a strict profile.
- Treat a user-supplied proposal as approved. Use the adaptive Research Execution Grill before implementation and material scale; do not generate replacement ideas unless requested. Select only gates relevant to the proposal. The signed v3 event-ledger profile is opt-in for projects that need externally auditable authorization.

## Workspace layout

- Use `/Users/viking/code` for projects, `/Users/viking/runs` for worktree runs, `/Users/viking/notes` for notes, and `/Users/viking/papers` for literature assets.
- There is no active `/Users/viking/research` workspace. Do not recreate it unless explicitly requested.
- Preserve user changes, secrets, and recoverable data. Follow the closest project-level `AGENTS.md` for repository-specific rules.
