# Codex adapter

This directory implements Codex-specific model routing, roles, Hooks, installation, provenance, and session audit. The platform-independent result contract lives in the [execution Kernel](../sop/tier0-core/autonomous-supervisor.md); the architectural boundary is [CODEX-ADAPTER.md](CODEX-ADAPTER.md).

## Instruction scopes

- `AGENTS.global.md` is installed at `~/.codex/AGENTS.md` as a thin bootstrap.
- `AGENTS.workspace.md` is installed at the selected workspace root as a resource-discovery overlay.
- The closest project `AGENTS.md` supplies project commands, architecture, acceptance, and local resource contracts.

Do not copy the global bootstrap into projects. Do not put credentials, private host identities, billing data, or secrets in reusable instructions.

## Managed installation

From the repository root:

```sh
python3 scripts/install_codex_runtime.py --dry-run
python3 scripts/install_codex_runtime.py --workspace <workspace-root>

# Explicit foreground choice; preserve is the CLI default
python3 scripts/install_codex_runtime.py --profile terra-supervisor --dry-run
python3 scripts/install_codex_runtime.py --profile sol-supervisor --dry-run

# Strict process-routing experiment; advisory is the default
python3 scripts/install_codex_runtime.py --routing-profile strict --dry-run
```

The installer:

- builds a content-addressed, read-only generation under `~/.codex/runtime-snapshots/` and atomically switches `~/.codex/runtime-current`;
- snapshots the Kernel, three current Domain Profiles, their direct runtime references, the Skill registry, Codex Adapter, role files, Hooks, and optional legacy compatibility material;
- records component version and content identity in `snapshot-manifest.json`;
- links the global/workspace AGENTS files, role TOMLs, and Hook scripts through `runtime-current`;
- merges only its own Hook registrations into existing `~/.codex/hooks.json`;
- resolves and verifies the base Python interpreter running the installer, then writes that executable's absolute path into managed Hook commands instead of assuming `/usr/bin/python3`;
- preserves the foreground model by default; explicit profiles set Terra/high or Sol/high;
- installs advisory routing by default and keeps strict routing opt-in;
- relocates the old internal `research-execution-grill` Skill link and recognized historical backup copies outside Codex Skill discovery when exact path or content evidence proves they were adapter-managed. Unknown same-named user content is preserved. The Research Grill remains a Domain Profile, not a Skill.

The default `--workspace` is the current home directory; pass the actual workspace root when it differs. The reusable repository and runtime snapshots never hard-code a server, IP, GPU, remote username, or project directory.

Each destination is backed up before replacement and written atomically. The installer does not claim a whole-install ACID transaction or power-loss durability; rerun it to converge after a reported partial failure. Existing immutable generations are retained for running sessions.

The verified Python launcher is an external runtime dependency and must remain executable. The installer rejects a launcher that resolves inside the removable source checkout; rerun installation after moving or replacing the system Python.

## Runtime provenance

The SessionStart Hook emits one compact `SOP_RUNTIME` envelope containing the content-addressed generation, Kernel/Adapter/profile versions, selected routing profile, reported foreground model/effort, and session identity. The domain profile can be supplied through `SOP_DOMAIN_PROFILE`; otherwise it is explicitly `UNRESOLVED_BY_SESSIONSTART` and the Agent selects the profile from closest instructions.

The session auditor reads this marker when it appears in the captured trace, but treats it as an unverified trace observation because arbitrary task text can contain the same shape. The report keeps the recorded startup profile separate from the selected audit policy. `--strict` cannot rewrite the historical field, and an injected marker cannot weaken strict auditing. Old logs without a marker remain auditable, but their runtime generation/profile is unknown.

Provenance is process evidence, not product acceptance. Missing or damaged provenance makes routing/model/WCU claims uncertain; it does not negate a result independently proven by project tests or external Oracle.

## Weighted routing

The current diagnostic objective is:

```text
WCU = 25 * T_sol + 10 * T_terra + 1 * T_luna
```

At unchanged acceptance, prefer Luna for bounded labor with a direct Oracle, Terra for cross-module semantics, debugging, ordinary review and common top-level execution, and Sol for unresolved architecture/research design, high ambiguity, or concrete high-risk judgment. These are evidence-adjustable platform preferences, not quality or permission gates.

Use coherent result packages and flat root routing. Avoid one-command delegation, full-history forks, repeated polling, overlapping writers, and multiple agents rediscovering the same unresolved invariant. A completed child should be consumed and explicitly closed; unavailable lifecycle proof is reported as `OPEN/UNKNOWN` rather than fabricated closure.

Role and model telemetry cannot prove independent review or product correctness. Model unavailability may be handled transparently in advisory mode while keeping the same acceptance. Strict mode retains the separately tested fail-closed package/routing experiment and must not silently change product or research semantics.

## Hooks

`advisory` is the normal profile. SessionStart injects provenance and compact routing context; lifecycle-related Pre/PostToolUse events provide recommendations without changing the result verdict. Stop does not block in advisory mode.

`strict` is explicit-only. It may deny process operations that violate its declared model/package policy, but a Hook denial is an execution fact, not proof that the product or scientific claim failed. Specialized paths can bypass Hooks and the App may require manual trust, so Hooks are not a security boundary.

## Session audit

Audit a completed root session by thread ID or rollout path:

```sh
python3 scripts/audit_codex_session.py <thread-id>
python3 scripts/audit_codex_session.py <rollout.jsonl> --json
python3 scripts/audit_codex_session.py <thread-id> --strict
```

The auditor reports separately:

- outcome-evidence integrity that can actually affect a completion claim;
- process/routing observations;
- model/token/WCU and provenance confidence;
- child lifecycle and system/guardian overhead.

Corrupt logs, missing descendants, invalid token schemas, or unknown attribution keep affected cost/process claims `[UNCERTAIN/PARTIAL]`. Regex matches, role names, package markers and report fields do not prove user outcomes.

Personal rollout logs are not stored in this repository; unit tests use synthetic session trees. Behavioral confidence still requires fresh-task execution because unit tests cannot prove service-side model availability or App Hook behavior.

## Managed links

```text
~/.codex/AGENTS.md
<workspace-root>/AGENTS.md
~/.codex/agents/{explorer,focused_worker,luna_executor,sol_architect,terra_debugger,worker,verifier,reviewer,risk_reviewer}.toml
~/.codex/hooks/{weighted_cost_router.py,weighted_routing_policy.py}
```

To uninstall, remove only links and Hook registrations owned by this adapter and restore a chosen backup if needed. Do not delete an entire shared `hooks.json`.

## Official references

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents and custom agent files](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex Hooks](https://learn.chatgpt.com/docs/hooks)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
