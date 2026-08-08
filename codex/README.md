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

- preserves the repository as the source of truth by linking both AGENTS files, eight role TOMLs, the Research Execution Grill, and the router Hook script;
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

For behavioral verification, run the four [fresh-task routing smoke scenarios](ROUTING_ACCEPTANCE.md), then audit each captured root task as described below.

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
| terra_debugger | `gpt-5.6-terra` | high | hypothesis-first root-cause diagnosis and authorized causal fixes | workspace-write |
| verifier | `gpt-5.6-luna` | medium | builds, tests, lint, scans, and oracles | workspace-write; no source edits |
| worker | `gpt-5.6-terra` | high | evidence-backed semantic or cross-file escalation | workspace-write |
| reviewer | `gpt-5.6-terra` | high | ordinary independent correctness review | read-only |
| risk_reviewer | `gpt-5.6-sol` | max | explicitly triggered high-risk review | read-only |

The foreground model is a user choice and is not changed by these files. When the foreground is Sol, the Hook uses a narrow structural allowlist: simple read-only shell inspection and explicit Luna/Terra Agent control are allowed; other shell/orchestration paths are denied. It blocks source mutations, lifecycle/Git delivery commands, unspecified children that could inherit Sol, full-history forks, and repeated short waits. Sol risk review requires both `HIGH_RISK_TRIGGER` and `EVIDENCE_PACK`. The Hook does not spawn agents by itself: AGENTS policy forms a coherent Luna work package, while the Hook prevents expensive violations.

Lifecycle policy is explicit: `max_concurrent_threads_per_session` caps concurrently open spawned threads; completed threads should be closed. After integrating a child result, close it before spawning an unrelated child and keep at most two concurrently open. On `agent-thread-limit`, the Hook returns nonterminal additional context so the parent can list agents, close completed/unneeded agents, retry the same eligible spawn at most once, then reuse an already-open matching Luna/Terra thread or stop. The router distinguishes this from Luna model unavailability and bounds repeated retries. For a directly recorded namespaced `close_agent`, the auditor correlates `{"target":"<agent-id>"}` to its output and accepts documented `previous_status` values except `not_found`; requests, malformed output, explicit tool errors, and missing output are not closure. Captured rollout evidence currently records closes only inside outer `functions.exec`, often bundled with other calls. The auditor deliberately does not infer closure from that JavaScript, so those sessions retain `[UNCERTAIN/PARTIAL]` close evidence.

Thread-limit recovery is keyed by session plus `PACKAGE_ID`. The first limit records a SHA-256 normalized spawn signature without persisting the prompt. During recovery, exactly one identical role/model/message/phase/tool retry may reserve the retry slot; changed signatures are denied, and any failed retry locks later spawns for that package. Inspection, close, and matching already-open Luna/Terra reuse remain available. `PACKAGE_ID` is a supervisor-declared, non-adversarial accounting identity, not cryptographic proof of semantic equivalence. The Hook is a guardrail, not a security boundary, and cannot infer that paraphrases or different IDs are semantically unchanged; silent relabeling is therefore a policy/audit violation.

A genuinely changed package declares `RECONTRACT_OLD_PACKAGE_ID`, `RECONTRACT_NEW_PACKAGE_ID`, `RECONTRACT_OLD_CONTRACT_SHA256`, `RECONTRACT_NEW_CONTRACT_SHA256`, `RECONTRACT_REASON`, and `RECONTRACT_SCOPE_ACCEPTANCE_DELTA`. IDs must be valid and different, the new ID must equal `PACKAGE_ID`, hashes must be distinct 64-hex SHA-256 values, and reason/delta must be nonempty. The Hook/auditor can validate this declared lineage after an observed recovery lock; neither can prove that the new contract hash faithfully represents semantics.

Every execution package has one total loop budget: one initial implementation, one consolidated Luna-or-Terra correction batch, one ordinary review, and one independent re-review. Luna owns the initial when eligible; a Terra worker/debugger may instead be the sole initial only with a nonempty objective `LUNA_ELIGIBLE=no(reason)` marker. Role/model changes do not reset the budget, findings are aggregated before correction, and a blocked re-review stops the package; `vN+1` requires explicit re-contracting. Every custom Agent message must contain exactly one stable `PACKAGE_ID` and one `PACKAGE_PHASE` from `map|initial|review|correction|re_review|verify`. Atomic per-session/package/phase reservations commit on successful spawn and release on failure; map/verify do not reset counts. Child Sol defaults to zero with at most one trigger-qualified `risk_reviewer` per root task/session; ordinary gate/validator review is Terra and Sol never implements.

`PostToolUse` is registered for `Agent`, spawn tool names, and the canonical outer `functions.exec` path. It classifies only a positively identified Luna call whose outer source proves exactly one canonical spawn. An error specifically reporting unknown/unavailable `gpt-5.6-luna` is returned as a concise `decision=block`, `continue=false` result. Unavailable and verified capability are monotonic, separate per-session/per-turn marker files; the unavailable marker wins for that turn and cannot be erased by wait-state writes. In that same turn, only `reviewer` and `risk_reviewer` are allowed after failure; all other retries/escalations and direct Sol execution are forbidden. The documented top-level `turn_id` is required for lifecycle enforcement; a missing field fails closed for that call without poisoning later correctly scoped turns. Missing or malformed failure evidence is not treated as success. Proof against a live installed Hook still requires a fresh task and captured runtime evidence; these synthetic tests do not establish that proof.

Execution starts with Luna initial when Luna is eligible. A nonempty objective `LUNA_ELIGIBLE=no(reason)` permits a Terra worker or terra_debugger to consume the package's single initial instead; it does not create another initial. The package permits at most one consolidated Luna-or-Terra correction. Sol remains parent judgment or the single trigger-qualified read-only risk review; it never implements. Runtime unavailability of Luna is a stop condition, not a reason to relabel the same package Luna-ineligible: stop and refresh/start a new task or turn. Luna is not restricted to trivial edits: once architecture, scope, invariants, and binary acceptance criteria are frozen, it is the default for ordinary implementation and other execution-heavy work.

Nested child creation has one canonical form shared by the Hook and auditor:

```text
await tools.multi_agent_v1__spawn_agent({"agent_type":"luna_executor","fork_context":false,"message":"PACKAGE_ID: example-change\nPACKAGE_PHASE: initial\nbounded implementation","model":"gpt-5.6-luna"});
```

The `model` field may be omitted or must match the configured role family; `multi_agent_v1__create_agent` is equivalent. The statement must be the complete `functions.exec` input, with strict JSON, one known `agent_type` or `role`, nonempty static `message`, exactly one package ID/phase marker pair, and no extra fields, aliases, comments, wrappers, or second call. `risk_reviewer` messages must include `HIGH_RISK_TRIGGER:` and `EVIDENCE_PACK:`. Package and risk-review reservations use atomic `O_EXCL` marker files scoped by unique session. If a process dies before `PostToolUse`, its `.reserved` marker can remain stale; recovery is a targeted removal for that ended unique session, and no automatic TTL is claimed. This proof covers those exact static factories and does not prove fully dynamic `tools[method]`, `eval`, or reflection. The Hook leaves such dynamic access outside this proof boundary. The current auditor always reports detected dynamic access as `[UNCERTAIN/PARTIAL]`; captured output cannot clear it, and this repository does not claim live-runtime proof from static or synthetic evidence.

The repository tests use synthetic Hook payloads and rollout logs. A live Codex tool-schema/spawn test still requires a fresh task with the installed Hook, a captured root log, and the routing smoke scenarios above; unit-test success is not live-runtime proof.

The Research Execution Grill separately gates `bootstrap/evidence_acquisition` from `experiment_authorization`: bootstrap may acquire only non-experimental source/license/registry/raw-data/label-package/review-packet evidence and cannot require its own future outputs. It cannot run a subpilot, pilot, or experiment, compute scientific metrics, inspect outcomes for adaptation, or emit scientific claims. Only experiment authorization consumes frozen evidence and permits the pilot. Project DAG validity is represented by required/provided artifact IDs whose disjointness is checked before validator code begins; blocked reviews remain append-only under one authoritative current gate/validator.

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
~/.codex/agents/{explorer,focused_worker,luna_executor,terra_debugger,worker,verifier,reviewer,risk_reviewer}.toml
~/.codex/skills/research-execution-grill
~/.codex/hooks/{weighted_cost_router.py,weighted_routing_policy.py}
```

## Official references

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents and custom agent files](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex Hooks](https://learn.chatgpt.com/docs/hooks)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
