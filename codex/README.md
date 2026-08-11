# Codex adapter

This directory keeps Codex-specific installation, weighted routing, hooks, and agent recipes out of the model-independent SOP layer.

## Instruction scopes

- `AGENTS.global.md` is the personal cross-repository Supervisor source installed at `~/.codex/AGENTS.md`.
- `AGENTS.workspace.md` is the lightweight `/Users/viking` overlay installed at `/Users/viking/AGENTS.md`.
- The repository-root `../AGENTS.md` governs maintenance of this repository. A project-local `AGENTS.md` may narrow the global policy for its own tree.

Do not copy the global template into every project. Keep project commands, architecture, and verification requirements local to that project. Never place secrets, provider credentials, billing data, or private authentication material in instruction files.

## Managed installation

Run the installer from the repository root. A dry run shows every intended action:

```sh
python3 scripts/install_codex_runtime.py --dry-run
python3 scripts/install_codex_runtime.py
# Explicitly install strict routing (advisory is the default)
python3 scripts/install_codex_runtime.py --routing-profile strict --dry-run
python3 scripts/install_codex_runtime.py --routing-profile strict
# Explicitly run the foreground supervisor on Sol (reversible profile choice)
python3 scripts/install_codex_runtime.py --profile sol-supervisor --dry-run
python3 scripts/install_codex_runtime.py --profile sol-supervisor
# Recommended default for development, competition, and approved-proposal engineering execution
python3 scripts/install_codex_runtime.py --profile terra-supervisor --dry-run
python3 scripts/install_codex_runtime.py --profile terra-supervisor
```

The installer:

- preserves the repository as the source of truth by creating a content-addressed immutable generation under `~/.codex/runtime-snapshots/`, then atomically switching `~/.codex/runtime-current` and linking both AGENTS files, 9 role TOMLs, the Research Execution Grill, and the router Hook scripts through that stable path;
- copies the adaptive SOP, its evidence-presentation reference, optional strict reference artifact, and validator/state-machine dependencies into each snapshot so relative Skill references remain readable after the checkout moves or is removed;
- builds and verifies the complete generation before preparing stable links and changing runtime files;
- validates `config.toml` and `hooks.json`, creates collision-resistant timestamped backups, and replaces each file independently with an atomic temporary-file rename;
- merges the router registrations into `~/.codex/hooks.json` instead of deleting unrelated Hooks;
- sets the default subagent to Luna Medium and concurrency to two under `[agents]`;
- deliberately preserves the top-level foreground `model` and `model_reasoning_effort` by default; `--profile sol-supervisor` explicitly sets them to `gpt-5.6-sol` and `high`, while `--profile terra-supervisor` explicitly sets them to `gpt-5.6-terra` and `high`;
- installs advisory routing by default; `--routing-profile strict` explicitly enables fail-closed routing and rejects an incompatible preserved foreground model during preflight.

The foreground profile is selected only at installation time. `preserve` remains the CLI default and does not make Terra the global default. Start a new task (or restart Codex) after changing a profile; an existing task keeps its current model configuration.

Codex discovers AGENTS guidance at task startup. After installation, start a new task. The App's `/hooks` trust step still requires exact-hash approval; that trust is not machine-verifiable by the installer, which cannot bypass it. Specialized tool paths may bypass Hooks, so post-run auditing remains mandatory rather than treating the Hook as a security boundary.

Managed installed Hooks embed the selected `CODEX_ROUTER_ENFORCEMENT=advisory|strict` profile before the documented `/usr/bin/python3 "$HOME/.codex/hooks/weighted_cost_router.py"` invocation, so the selected behavior is deterministic even with a clean inherited environment. Advisory is the normal post-install default; strict mode preserves the fail-closed policy used by the router's contract tests.

The Stop Hook is a delivery guardrail: for a substantial current turn (at least three tool calls or at least 100,000 current-turn tokens) it may continue once when the final message omits outcome, evidence/commands, review disposition, routing/WCU, remaining risks, or repo-relevant Git/delivery state. It accepts semantically complete English or Chinese reports, fails open for missing or malformed evidence or one-shot keys, and never continues when `stop_hook_active` is true.

Model-bound package corrections and re-reviews use a fresh explicit typed spawn; runtime denial of `resume_agent` guarantees a closed role-bound agent cannot be resumed. Hook telemetry does not bind agent IDs to package/phase, requested role, actual model, or open state. Package IDs/phases and the one initial/one correction/one re-review budgets remain unchanged, and changing role/model never resets a budget. Already-open matching-agent reuse and actual-model verification are supervisor policy plus PostToolUse/session audit; once evidence exists, violations fail closed and WCU is `[UNCERTAIN]` rather than accepting the observed role.

To verify the installed sources in a new CLI task:

```sh
codex --ask-for-approval never "List the instruction sources, custom agent roles, and Hooks you loaded."
codex --cd <project> --ask-for-approval never "List the instruction sources, custom agent roles, and Hooks you loaded."
```

For behavioral verification, complete the [fresh-task advisory and strict acceptance](ROUTING_ACCEPTANCE.md), then audit each captured root task as described below.

Backups are local runtime files named with `.backup-<timestamp>` and must not be committed here. If a later write fails, completed atomic writes remain in place and the installer reports the backup paths; manually restore a selected backup if needed, then rerun the installer to converge. Before `runtime-current` is switched, the previous current generation remains active. After the switch, the new generation, stable links, config, and Hooks have already been prepared. This is not a whole-install ACID transaction, and the installer does not claim power-loss `fsync` durability.

## Weighted routing

The optimization target is `WCU = 25*T_sol + 10*T_terra + 1*T_luna`, subject to unchanged acceptance quality. `terra-supervisor` is the recommended top-level Terra/high default for development, competition, and approved-proposal engineering execution; this is a task-class recommendation, not a global CLI default. Luna is preferred for labor-heavy bounded execution and Terra for semantic/debugging pressure and ordinary review. Use a compact `sol_architect` only when architecture or research execution design needs stronger judgment, `risk_reviewer` Sol/max for a concrete high-risk review, and a Sol foreground when high-decision-density judgment is sustained across the task.

Routing is flat at the root: the top-level supervisor directly dispatches Luna, Terra, or Sol specialists as needed. Do not depend on a child spawning another child or on an `agents.max_depth` setting; nested delegation is not an acceptance prerequisite. After a spawn, do useful non-overlapping work when available and wait only when the next step depends on the result, using one reasonable bounded wait rather than interval polling. Do not manufacture busywork or promise detached execution or zero waiting.

The foreground model remains a user choice. The router does not spawn agents; in `advisory` mode it highlights expensive Sol execution, full-context forks, repeated polling, role/model conflicts, and Luna capability failures without blocking the task. Luna unavailability may reroute unchanged work to Terra or another lowest-cost capable role only in advisory mode. Package IDs, phase markers, exact retry signatures, and one-loop budgets remain available as coordination metadata but are not required by the advisory policy; changing a role or model never resets the applicable package budget.

The managed Hook command selects the requested routing profile for installed Hooks. Strict mode retains the historical package-marker, loop-budget, Sol-write, risk-review, thread-recovery, and Luna fail-closed behavior; its unit tests exercise that mode. Direct router invocations remain advisory unless their caller sets the variable. In a fresh strict task, Luna unavailability fails closed and must be reported; it must not be silently rerouted.

The auditor is process-advisory by default. Model choice, package metadata, loop shape, lifecycle preferences, and direct Sol work are observations rather than exit failures. Evidence-integrity problems—corrupt/truncated logs, missing descendants or outputs, invalid token schemas, unknown model attribution, and incomplete task evidence—remain nonzero because WCU and completion claims would be unreliable. Pass `--strict` when a task explicitly selected strict routing and its process findings must also fail the audit. Live behavior still requires a fresh-task smoke test; synthetic tests establish code behavior, not service-side model availability.

Use bounded review profiles such as `REVIEW_PROFILE=ordinary|api|security|architecture/data` to keep review proportional. An API correctness review may use Sol risk judgment without invoking the full codex-security workflow; the full workflow is reserved for a concrete adversarial security trigger. Skills remain orthogonal adapters and cannot add frozen stages or acceptance artifacts. Stop review once the verdict is evidence-sufficient; carry nonblocking findings as `[UNCERTAIN]` or backlog items.

For a new project directory, run `git rev-parse --show-toplevel` before the first write, stage, or commit. A directory under `/Users/viking` or ContestOS can inherit a parent repository; use an independent `git init` or worktree when that is the intended root. Run only one full suite at a time, close only your own prior process/session before restarting, and prefer one long bounded wait with compact evidence over short polling/raw transcript loops. Monitoring WCU is part of the cost record.

Research follows the same pattern: the adaptive Grill is the default, while the signed v3 ledger/validator is an opt-in strict profile for externally auditable or high-value authority boundaries.

## Session audit

Audit a completed root task by thread id or parent rollout path:

```sh
python3 scripts/audit_codex_session.py <thread-id>
python3 scripts/audit_codex_session.py <parent-rollout.jsonl> --json > /tmp/codex-wcu.json
python3 scripts/audit_codex_session.py <thread-id> --strict
```

The auditor searches active and archived logs, discovers descendants, attributes cumulative token deltas to the active model, and reports raw tokens, WCU, role usage, large tool outputs, and direct Sol execution. It reconciles successful spawns with child logs and requires valid token snapshots plus `task_complete` for every session. Missing descendants, damaged/truncated logs, incomplete token schemas, unknown models, and routing blockers mark cost as `[UNCERTAIN/PARTIAL]` and return nonzero.

For the captured all-Sol regression task used during development:

```text
Raw tokens: 11,511,651
Weighted cost: 287,791,275 WCU
Subagent roles: risk_reviewer=1
Violation: 67 non-read-only Sol tool calls
Observation: no Terra or Luna tokens were observed
```

Personal rollout logs are not stored in this repository; unit tests use synthetic session trees.

## Uninstall

Remove only destinations owned by this adapter, restore any selected backups, and start a new task. `~/.codex/hooks.json` may contain unrelated registrations, so remove only entries that invoke `weighted_cost_router.py` rather than deleting the entire file.

Managed symlink destinations are:

```text
~/.codex/AGENTS.md
/Users/viking/AGENTS.md
~/.codex/agents/{explorer,focused_worker,luna_executor,sol_architect,terra_debugger,worker,verifier,reviewer,risk_reviewer}.toml
~/.codex/skills/research-execution-grill
~/.codex/hooks/{weighted_cost_router.py,weighted_routing_policy.py}
```

These symlinks target `~/.codex/runtime-current/<entry>`. `runtime-current` targets a verified immutable generation under `~/.codex/runtime-snapshots/`, never the Git checkout. Older generations are retained so an already-running task can continue using its resolved files; recovery is manual backup restoration plus a rerun, not automatic rollback.

## Official references

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents and custom agent files](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex Hooks](https://learn.chatgpt.com/docs/hooks)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
