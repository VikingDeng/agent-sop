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
```

The installer:

- preserves the repository as the source of truth by linking both AGENTS files, seven role TOMLs, the Research Execution Grill, and the router Hook script;
- stages and validates the complete Hook JSON and TOML update before changing runtime files;
- backs up each destination (including the original symlink target), persists a recovery manifest under `~/.codex/install-rollback/`, and automatically restores mutations in reverse order if a later step fails or is interrupted;
- merges the router registrations into `~/.codex/hooks.json` instead of deleting unrelated Hooks;
- sets the default subagent to Luna Medium, concurrency to two, and depth to one under `[agents]`;
- deliberately preserves the top-level foreground `model` and `model_reasoning_effort`.

The resulting `[agents]` settings are:

```toml
[agents]
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "medium"
max_concurrent_threads_per_session = 2
max_depth = 1
```

Codex discovers AGENTS guidance at task startup. After installation, start a new task. Non-managed Hooks must also be approved by exact hash in the Codex `/hooks` interface; this trust step is intentionally not bypassed by the installer. Specialized tool paths may bypass Hooks, so post-run auditing remains mandatory rather than treating the Hook as a security boundary.

The router fails closed when a `PreToolUse` payload has an unknown schema/model, and appends diagnostics to `~/.codex/router-state/hook-errors.jsonl`. For emergency recovery, remove only the registrations whose nested command invokes `weighted_cost_router.py` from `~/.codex/hooks.json`, then start a new task. This is an operator escape hatch, not a normal fallback.

To verify the installed sources in a new CLI task:

```sh
codex --ask-for-approval never "List the instruction sources, custom agent roles, and Hooks you loaded."
codex --cd <project> --ask-for-approval never "List the instruction sources, custom agent roles, and Hooks you loaded."
```

Backups are local runtime files named with `.backup-<timestamp>` and must not be committed here. To restore one, copy it back to its original path, compare the result, and start a new task.

## Weighted routing

The optimization target is:

```text
WCU = 25 * T_sol + 10 * T_terra + 1 * T_luna
```

WCU is minimized subject to unchanged acceptance criteria, risk gates, and independent verification. Cached tokens still count against the model family that consumed them.

| Role | Model | Effort | Purpose | Sandbox |
|---|---|---|---|---|
| explorer | `gpt-5.6-luna` | medium | targeted repository mapping | read-only |
| focused_worker | `gpt-5.6-luna` | high | narrow mechanical edits | workspace-write |
| luna_executor | `gpt-5.6-luna` | high | bounded labor-heavy code, tests, fixtures, pipelines, and docs | workspace-write |
| verifier | `gpt-5.6-luna` | medium | builds, tests, lint, scans, and oracles | workspace-write; no source edits |
| worker | `gpt-5.6-terra` | high | evidence-backed semantic or cross-file escalation | workspace-write |
| reviewer | `gpt-5.6-terra` | high | ordinary independent correctness review | read-only |
| risk_reviewer | `gpt-5.6-sol` | max | explicitly triggered high-risk review | read-only |

The foreground model is a user choice and is not changed by these files. When the foreground is Sol, the Hook uses a narrow structural allowlist: simple read-only shell inspection and explicit Luna/Terra Agent control are allowed; other shell/orchestration paths are denied. It blocks source mutations, lifecycle/Git delivery commands, unspecified children that could inherit Sol, full-history forks, and repeated short waits. Sol risk review requires both `HIGH_RISK_TRIGGER` and `EVIDENCE_PACK`. The Hook does not spawn agents by itself: AGENTS policy forms a coherent Luna work package, while the Hook prevents expensive violations.

Escalation is Luna -> Terra -> Sol and requires failure evidence. Luna is not restricted to trivial edits: once architecture, scope, invariants, and binary acceptance criteria are frozen, it is the default for ordinary implementation and other execution-heavy work.

## Session audit

Audit a completed root task by thread id or parent rollout path:

```sh
python3 scripts/audit_codex_session.py <thread-id>
python3 scripts/audit_codex_session.py <parent-rollout.jsonl> --json > /tmp/codex-wcu.json
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
~/.codex/agents/{explorer,focused_worker,luna_executor,worker,verifier,reviewer,risk_reviewer}.toml
~/.codex/skills/research-execution-grill
~/.codex/hooks/{weighted_cost_router.py,weighted_routing_policy.py}
```

## Official references

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents and custom agent files](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex Hooks](https://learn.chatgpt.com/docs/hooks)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
