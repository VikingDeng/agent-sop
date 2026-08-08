# Workspace overlay

## Workflow authority

- `/Users/viking/code/agent-sop` is the source of truth for reusable workflow, project skeletons, SOP gates, prose rules, Codex agent recipes, and the Research Execution Grill.
- `/Users/viking/ops` remains the source of truth for workstation automation only. Do not treat old Claude or deleted Research OS material there as active workflow authority.
- `~/.codex` is installed runtime output; edit the corresponding source in `agent-sop` first when one exists.

## Codex-only routing

- Use Codex and GPT models only. Do not route work through Claude, local `claude` CLI, DeepSeek compatibility harnesses, or retired Research OS agents.
- Use an isolated GPT/Codex reviewer when independent scrutiny is required. Same-provider independent review is an internal blind review, not external review.
- Minimize `25*Sol + 10*Terra + 1*Luna` weighted token cost without weakening acceptance criteria. Send bounded labor-heavy code, tests, experiment plumbing, logs, data work, and commands to Luna first; use Terra for semantic escalation and ordinary review; use `terra_debugger` directly only for unknown-root-cause, hypothesis-driven diagnosis, then return mechanical execution to Luna where practical; reserve Sol Max for main-control, execution Grill decisions, high-risk reasoning, and explicitly triggered critical review.
- Use Luna for the sole initial when `LUNA_ELIGIBLE=yes`. A Terra worker or terra_debugger may be the sole initial only with a nonempty objective `LUNA_ELIGIBLE=no(reason)` marker. The unchanged package permits at most one consolidated Luna-or-Terra correction after reviewer findings are aggregated; role/model changes do not reset the budget and Sol never implements. Every custom Agent message carries exactly one stable nonempty `PACKAGE_ID` and one `PACKAGE_PHASE` from `map|initial|review|correction|re_review|verify`. Every child returns a compact evidence packet, not a raw transcript.

## Approved research proposals

- Treat a proposal supplied or selected by the user as an approved research direction unless the user explicitly asks for idea generation or proposal admission.
- Before implementing an approved proposal, and again before materially scaling experiments, follow `/Users/viking/code/agent-sop/sop/tier1-skeleton/research-execution-grill.md`.
- The Grill may block on ambiguity, invalid experimental design, unfair baselines, weak oracle, missing budget, or missing scale criteria. It must not replace the proposal with a new idea.

## Workspace layout

- Use `/Users/viking/code` for projects, `/Users/viking/runs` for worktree runs, `/Users/viking/notes` for notes, and `/Users/viking/papers` for literature assets.
- There is no active `/Users/viking/research` workspace. Do not recreate or route into it unless the user explicitly requests a new project there.
- Preserve user changes, secrets, and recoverable data. Follow the closest project-level `AGENTS.md` for repository-specific rules.

## Lifecycle and package budgets

- `max_concurrent_threads_per_session` caps concurrently open spawned threads; completed threads should be closed. After integrating a child result, close it before spawning an unrelated child; keep at most two concurrently open.
- On `agent-thread-limit`, list agents, close completed/unneeded agents, retry the same eligible spawn at most once, then reuse an already-open eligible Luna/Terra thread only when contract and role match; otherwise stop. This is distinct from Luna model unavailability, token exhaustion, and compute exhaustion.
- Recovery is package-scoped: permit one exact normalized-signature retry, deny changed role/model/message/phase/tool input under that `PACKAGE_ID`, and lock later spawns if the retry fails. Inspection, confirmed close, and matching open-thread reuse remain allowed. `PACKAGE_ID` is trusted supervisor accounting, not cryptographic semantic proof; the Hook is a guardrail and cannot infer paraphrased identity. Silent relabeling is a policy/audit violation.
- Genuine re-contract evidence records old/new package IDs, distinct old/new contract SHA-256 values, a nonempty reason, and a nonempty scope/acceptance delta using the `RECONTRACT_*` markers defined in the supervisor. The markers prove declared lineage only.
- Per execution package, allow only one initial implementation, one consolidated correction batch, and one independent re-review total. Escalation does not reset the budget; a blocked re-review stops the package and preserves evidence. `vN+1` requires explicit re-contracting.
- Child Sol budget defaults to zero; at most one trigger-qualified `risk_reviewer` may be spawned per root task/session. Ordinary gate/validator review is Terra and Sol never implements.
