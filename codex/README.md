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
# Explicitly run the foreground supervisor on Sol (reversible profile choice)
python3 scripts/install_codex_runtime.py --profile sol-supervisor --dry-run
python3 scripts/install_codex_runtime.py --profile sol-supervisor
```

The installer:

- preserves the repository as the source of truth by linking both AGENTS files, eight role TOMLs, the Research Execution Grill, and the router Hook script;
- stages and validates the complete Hook JSON and TOML update before changing runtime files;
- backs up each destination (including the original symlink target), persists a recovery manifest under `~/.codex/install-rollback/`, and automatically restores mutations in reverse order if a later step fails or is interrupted;
- merges the router registrations into `~/.codex/hooks.json` instead of deleting unrelated Hooks;
- sets the default subagent to Luna Medium, concurrency to two, and depth to one under `[agents]`;
- deliberately preserves the top-level foreground `model` and `model_reasoning_effort` by default; `--profile sol-supervisor` explicitly sets them to `gpt-5.6-sol` and `high`.

The resulting `[agents]` settings are:

```toml
[agents]
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "medium"
max_concurrent_threads_per_session = 2
max_depth = 1
```

The foreground profile is selected only at installation time. Start a new task (or restart Codex) after changing it; an existing task keeps its current model configuration.

Codex discovers AGENTS guidance at task startup. After installation, start a new task. The App's `/hooks` trust step still requires exact-hash approval; that trust is not machine-verifiable by the installer, which cannot bypass it. Specialized tool paths may bypass Hooks, so post-run auditing remains mandatory rather than treating the Hook as a security boundary.

Managed installed Hooks embed `CODEX_ROUTER_ENFORCEMENT=strict` before the documented `/usr/bin/python3 "$HOME/.codex/hooks/weighted_cost_router.py"` invocation, so they enforce strict routing even with a clean inherited environment. The router is advisory only when invoked directly or through an unmanaged diagnostic command; that is not the post-install default. Strict mode preserves the fail-closed policy used by the router's contract tests.

The Stop Hook is a delivery guardrail: for a substantial current turn (at least three tool calls or at least 100,000 current-turn tokens) it may continue once when the final message omits outcome, evidence/commands, review disposition, routing/WCU, remaining risks, or repo-relevant Git/delivery state. It accepts semantically complete English or Chinese reports, fails open for missing or malformed evidence or one-shot keys, and never continues when `stop_hook_active` is true.

To verify the installed sources in a new CLI task:

```sh
codex --ask-for-approval never "List the instruction sources, custom agent roles, and Hooks you loaded."
codex --cd <project> --ask-for-approval never "List the instruction sources, custom agent roles, and Hooks you loaded."
```

For behavioral verification, complete the [fresh-task strict acceptance and advisory diagnostics](ROUTING_ACCEPTANCE.md), then audit each captured root task as described below.

Backups are local runtime files named with `.backup-<timestamp>` and must not be committed here. To restore one, copy it back to its original path, compare the result, and start a new task.

## Weighted routing

The optimization target is `WCU = 25*T_sol + 10*T_terra + 1*T_luna`, subject to unchanged acceptance quality. Luna is preferred for labor-heavy bounded execution, Terra for semantic/debugging pressure and ordinary review, and Sol for architecture, research design, ambiguity, and final judgment.

The foreground model remains a user choice. The router does not spawn agents; in direct or unmanaged `advisory` mode it highlights expensive Sol execution, full-context forks, repeated polling, role/model conflicts, and Luna capability failures without blocking the task. Luna unavailability may reroute unchanged work to Terra or another lowest-cost capable role only in that advisory diagnostic mode. Package IDs, phase markers, exact retry signatures, and one-loop budgets remain available as coordination metadata but are not required by the advisory policy.

The managed Hook command selects `CODEX_ROUTER_ENFORCEMENT=strict` for installed Hooks. Strict mode retains the historical package-marker, loop-budget, Sol-write, risk-review, thread-recovery, and Luna fail-closed behavior; its unit tests exercise that mode. Direct router invocations remain advisory unless their caller sets the variable. In a fresh strict task, Luna unavailability fails closed and must be reported; it must not be silently rerouted.

The auditor is process-advisory by default. Model choice, package metadata, loop shape, lifecycle preferences, and direct Sol work are observations rather than exit failures. Evidence-integrity problems—corrupt/truncated logs, missing descendants or outputs, invalid token schemas, unknown model attribution, and incomplete task evidence—remain nonzero because WCU and completion claims would be unreliable. Pass `--strict` when a task explicitly selected strict routing and its process findings must also fail the audit. Live behavior still requires a fresh-task smoke test; synthetic tests establish code behavior, not service-side model availability.

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
~/.codex/agents/{explorer,focused_worker,luna_executor,terra_debugger,worker,verifier,reviewer,risk_reviewer}.toml
~/.codex/skills/research-execution-grill
~/.codex/hooks/{weighted_cost_router.py,weighted_routing_policy.py}
```

## Official references

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents and custom agent files](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex Hooks](https://learn.chatgpt.com/docs/hooks)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
