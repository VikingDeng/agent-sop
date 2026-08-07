# Workspace overlay

## Workflow authority

- `/Users/viking/code/agent-sop` is the source of truth for reusable workflow, project skeletons, SOP gates, prose rules, Codex agent recipes, and the Research Execution Grill.
- `/Users/viking/ops` remains the source of truth for workstation automation only. Do not treat old Claude or deleted Research OS material there as active workflow authority.
- `~/.codex` is installed runtime output; edit the corresponding source in `agent-sop` first when one exists.

## Codex-only routing

- Use Codex and GPT models only. Do not route work through Claude, local `claude` CLI, DeepSeek compatibility harnesses, or retired Research OS agents.
- Use an isolated GPT/Codex reviewer when independent scrutiny is required. Same-provider independent review is an internal blind review, not external review.
- Keep routine bounded work on Luna/Terra roles and reserve Sol Max for main-control, execution Grill, high-risk reasoning, and independent critical review.

## Approved research proposals

- Treat a proposal supplied or selected by the user as an approved research direction unless the user explicitly asks for idea generation or proposal admission.
- Before implementing an approved proposal, and again before materially scaling experiments, follow `/Users/viking/code/agent-sop/sop/tier1-skeleton/research-execution-grill.md`.
- The Grill may block on ambiguity, invalid experimental design, unfair baselines, weak oracle, missing budget, or missing scale criteria. It must not replace the proposal with a new idea.

## Workspace layout

- Use `/Users/viking/code` for projects, `/Users/viking/runs` for worktree runs, `/Users/viking/notes` for notes, and `/Users/viking/papers` for literature assets.
- There is no active `/Users/viking/research` workspace. Do not recreate or route into it unless the user explicitly requests a new project there.
- Preserve user changes, secrets, and recoverable data. Follow the closest project-level `AGENTS.md` for repository-specific rules.
