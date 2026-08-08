# Routing acceptance smoke scenarios

These five manual smoke scenarios are behavioral acceptance tests for the routing policy. A prompt can reveal whether the supervisor and Hook choose the intended role, context, fork mode, and handoff, but prompts are not proof by themselves. Proof requires the captured session evidence and the post-session WCU audit.

Run each scenario in a fresh task. Replace bracketed placeholders with a real repository path, bounded change, failing test, or risk contract as appropriate. Keep the substituted work harmless, reversible, and small enough to inspect manually.

For every scenario, preserve the root thread id and run this exact repository audit command after the session:

```sh
python3 scripts/audit_codex_session.py <thread-id> --json > /tmp/codex-wcu.json
```

Replace `<thread-id>` with the completed root task's thread id. Treat a nonzero exit code, `[UNCERTAIN/PARTIAL]` cost status, missing child logs, or routing violations as a failed acceptance result—not as a pass.

Lifecycle and loop invariants apply to every scenario: `max_concurrent_threads_per_session` caps concurrently open spawned threads; completed threads should be closed. After integrating a child result, close it before an unrelated spawn. Count closure only when a directly recorded namespaced `close_agent` request for `{"target":"<agent-id>"}` has an output whose documented `previous_status` is not `not_found`; outer `functions.exec` JavaScript is not closure proof. A thread-limit result is nonterminal context recovered by list → confirmed close of completed/unneeded children → one retry of the same eligible spawn → matching open Luna/Terra reuse or stop; it is never Luna model unavailability. Each package allows one initial, one consolidated Luna-or-Terra correction, one review, and one re-review. Luna is the initial when eligible; Terra may be the sole initial only with nonempty objective `LUNA_ELIGIBLE=no(reason)`. Role/model changes do not reset the budget and Sol never implements. Every custom spawn message includes exactly one stable `PACKAGE_ID` and one valid `PACKAGE_PHASE`.

After thread-limit, the package permits one retry only when its normalized role/model/message/phase/tool signature exactly matches the failed spawn. A changed signature is denied; a failed retry locks later spawns but not inspection, close, or matching open-thread reuse. Static acceptance must also verify the trust wording: `PACKAGE_ID` is supervisor-declared non-adversarial accounting, not cryptographic semantic proof; the Hook is a guardrail, not a security boundary; it cannot infer paraphrased identity; silent relabeling is a policy/audit violation. A real re-contract uses all six `RECONTRACT_*` lineage fields for old/new IDs and hashes, reason, and scope/acceptance delta. Valid markers establish declared lineage only.

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

Expected role: `luna_executor` for the single initial implementation and `reviewer` on Terra for independent ordinary review; after findings are aggregated, at most one consolidated correction may use Luna or evidence-backed Terra under the unchanged package budget.

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

## 5. Luna runtime-unavailable stop

Prompt:

```text
Make this bounded Luna-eligible change in [allowed files]. Use the configured Luna executor and stop immediately if the App reports that gpt-5.6-luna is unknown or unavailable. Do not retry Luna, escalate execution to Terra, or perform the package directly on Sol. Report the blocked result and start a fresh task/turn only after the runtime capability is available.
```

Expected behavior: `PostToolUse` sees the failed `Agent`/spawn result, records the session/turn capability failure, returns `decision=block` with `continue=false`, and prevents same-turn `worker`, `terra_debugger`, or Luna execution retries. A later fresh turn is not blocked by stale state; only an existing read-only `reviewer` or explicit `risk_reviewer` gate may proceed under its contract.

Forbidden behavior: silently treating the error as a normal failed worker, escalating the same package to Terra, direct Sol execution, retrying Luna in the blocked turn, or allowing malformed evidence to clear the gate.

Evidence to collect: spawn request and exact tool response; PostToolUse block result; separate per-session/per-turn capability markers with existing atomic wait state preserved; same-turn PreToolUse deny result; later-turn non-block result; auditor output reporting any failed-Luna-to-Terra/direct-Sol sequence as a routing violation. A live installed-Hook capture remains required; synthetic unit tests do not prove the installed runtime registration or nested hook delivery.
