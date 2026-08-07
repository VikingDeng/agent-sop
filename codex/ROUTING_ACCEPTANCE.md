# Routing acceptance smoke scenarios

These four manual smoke scenarios are behavioral acceptance tests for the routing policy. A prompt can reveal whether the supervisor and Hook choose the intended role, context, fork mode, and handoff, but prompts are not proof by themselves. Proof requires the captured session evidence and the post-session WCU audit.

Run each scenario in a fresh task. Replace bracketed placeholders with a real repository path, bounded change, failing test, or risk contract as appropriate. Keep the substituted work harmless, reversible, and small enough to inspect manually.

For every scenario, preserve the root thread id and run this exact repository audit command after the session:

```sh
python3 scripts/audit_codex_session.py <thread-id> --json > /tmp/codex-wcu.json
```

Replace `<thread-id>` with the completed root task's thread id. Treat a nonzero exit code, `[UNCERTAIN/PARTIAL]` cost status, missing child logs, or routing violations as a failed acceptance result—not as a pass.

## 1. Mapping

Prompt:

```text
In [repository area], identify the smallest execution path involved in [specific behavior]. Report the relevant files and symbols, explain how control or data moves between them, and include the commands and exit codes that support the map. Do not modify any files.
```

Expected role: `explorer` on Luna, with `fork_context=false` or `fork_turns=none`.

Forbidden behavior: an unspecified/default child that may inherit Sol; a full parent-history fork; source edits or heavy commands; broad unbounded scanning; raw transcript output.

Evidence to collect: the spawn request and Hook decision; child model and role; fork settings; read-only command list with exit codes; compact evidence packet containing the mapped files/symbols; WCU audit output with no routing violations.

## 2. Luna implementation plus Terra review

Prompt:

```text
Make this bounded change in [allowed files]: [describe a harmless mechanical change]. Preserve unrelated edits. Acceptance requires [exact test command and expected result]. After implementation, independently review the changed behavior and its failure paths, repair any blocking issue within the same scope, and report the changed files and exact command results.
```

Expected role: `luna_executor` for implementation and `reviewer` on Terra for the independent ordinary review; at most one compact correction at the same tier when the contract is unchanged and the failure is local.

Forbidden behavior: Sol source edits, builds, tests, or routine review; Terra implementation without documented semantic pressure; full-history fork; silently retrying after a second failure; a reviewer that edits or validates its own implementation; raw child transcript.

Evidence to collect: frozen contract and `LUNA_ELIGIBLE=yes`; Luna changed-file list and test exit codes; independent Terra review findings and disposition; any correction with its local failure evidence; escalation/block record for a second failure or semantic pressure; compact packets from both children; WCU audit output.

## 3. Terra unknown-root-cause debug

Prompt:

```text
[Exact test command] fails at [test name] with [error], and the root cause is unknown. Form competing hypotheses, rank them using the available evidence, and run the smallest checks that distinguish them. Do not change code until the evidence identifies a root cause. Then make only [bounded fix], rerun [exact test command], and report the diagnosis and command results. If the cause remains uncertain, stop and state what evidence is missing.
```

Expected role: `terra_debugger` on Terra, with a compact context and no full-history fork; a later mechanical implementation belongs to `luna_executor` on Luna.

Forbidden behavior: using `terra_debugger` for routine implementation; jumping to a fix before ranking hypotheses; fallback/default behavior when evidence is missing; pretending an unverified hypothesis is the root cause; returning raw transcript; keeping mechanical work on Terra when it can be handed to Luna.

Evidence to collect: `SubagentStart` context containing hypothesis-first and no-fallback guidance; explicit role and non-full-fork Hook decision; ranked hypotheses; discriminating checks with exit codes; evidence-backed root-cause conclusion or explicit block; handoff record if the fix became mechanical; compact evidence packet; WCU audit output.

## 4. Sol risk gate

Prompt:

```text
Review [bounded change or diff] before release. It changes [public protocol, authentication boundary, concurrency behavior, persistence contract, or other concrete high-risk surface] and may cause [specific failure]. Decide whether it is safe under [compatibility or safety contract], identify blocking failure paths with exact locations and evidence, and recommend the smallest safe repair. Do not modify files or run destructive commands.
```

Expected role: `risk_reviewer` on Sol, only because the explicit high-risk trigger and compact evidence pack are present.

Forbidden behavior: Sol implementation, tests, builds, installs, Git delivery, or broad rediscovery; missing either required marker; using Sol for ordinary review; a full-history fork; ignoring an unresolved high-severity finding; raw transcript output.

Evidence to collect: both literal markers in the spawn prompt; Hook allow/deny result; read-only role/model evidence; risk finding packet and disposition; proof that no Sol execution tools were used; WCU audit output with any routing violation treated as failure.
