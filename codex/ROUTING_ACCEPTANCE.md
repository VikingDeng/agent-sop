# Routing acceptance

Run the managed-hook scenarios in fresh tasks after installing the Codex runtime. Installed managed Hooks use the selected `--routing-profile`; `advisory` is the default and `strict` is explicit. The scenarios below cover both profiles.

## Default advisory scenarios

1. **Bounded implementation**: ask for a multi-file but well-specified change. Expect Luna to receive substantial mechanical work when available, with acceptance based on real tests rather than role compliance.
2. **Luna unavailable**: install or invoke the router in advisory mode, then simulate or observe `Unknown model gpt-5.6-luna`. Expect a concise advisory and a transparent fallback to Terra or another capable role.
3. **Exploratory debugging**: ask for an unknown-root-cause diagnosis. Expect the Agent to revise hypotheses and choose discriminating checks without requiring a fixed package phase sequence.
4. **Small task**: ask for a narrow reversible edit. Expect direct completion when delegation overhead would dominate, even on Sol, with a cost advisory rather than a permission denial.
5. **Research variation**: test one proposal requiring human labels and one simulation/benchmark proposal without them. Expect each to receive claim-matched gates; the second must not invent a human-oracle requirement.
6. **Concise delivery**: complete a tool-using task with a short outcome-and-evidence report. Expect the advisory Stop Hook never to continue or block it, regardless of tool-call count or attributable tokens.
7. **Agent reuse**: invoke `resume_agent` for an existing task. Expect an auditability advisory rather than a denial; explicit strict mode remains the profile that denies unverifiable resume calls.

For each scenario collect the achieved result, actual validation, wall time, Sol/Terra/Luna token share, WCU, unnecessary stops, and any hidden reduction in acceptance quality. Routing succeeds only when outcome quality is preserved and process overhead is proportionate.

## Strict profile

Install with `python3 scripts/install_codex_runtime.py --routing-profile strict`. The managed Hook command embeds `CODEX_ROUTER_ENFORCEMENT=strict` before the documented Python invocation, so this profile is selected per Hook call even with a clean inherited environment. In this mode the historical invariants apply: package markers, phase budgets, Sol mutation denial, trigger-qualified risk review, exact thread-limit recovery, and Luna fail-closed behavior. The App `/hooks` exact-hash trust step remains required and is not machine-verifiable by this installer. A strict install with `--profile preserve` fails preflight when the configured foreground model is outside the Sol/Terra/Luna families; select a named supported foreground profile or use advisory routing.

## Research strict profile

The signed `research-execution-grill-v3` ledger is independently opt-in. When selected, verify exact action authorization using the v3 reference and validator. Do not infer that selecting strict model routing automatically selects strict research authorization, or vice versa.

## Acceptance outcome

Advisory-mode acceptance requires:

- no permission denial caused solely by model choice, missing package metadata, repair count, or recommended stage names;
- no fabricated evidence or silent acceptance downgrade;
- a meaningful preference for lower-WCU execution on labor-heavy work;
- proportional verification and review;
- honest `[UNCERTAIN]` cost or runtime evidence when logs are incomplete.

## Installer crash boundary

The installer holds one non-blocking per-home lock during a real install. It verifies an immutable generation, prepares stable links, validates `config.toml` and `hooks.json`, backs up each changed file, and atomically writes those files before replacing the single `~/.codex/runtime-current` symlink. A failure before that replacement leaves the old current generation active; a failure during a later independent file write leaves completed valid writes and reports their backups. Restore a backup manually when required, then rerun the installer. There is no recovery journal or automatic replay, and this boundary does not claim whole-install ACID or power-loss `fsync` durability.

## Fresh-task strict acceptance

After installation, start a fresh task or restart Codex so the managed Hook is loaded. Verify that the installed command contains the exact `CODEX_ROUTER_ENFORCEMENT=strict /usr/bin/python3` prefix and that strict routing rejects missing package markers, exhausted loop budgets, unauthorized Sol mutation, and unqualified risk review. The App `/hooks` exact-hash trust step must still be completed manually because the installer cannot verify it.

When `gpt-5.6-luna` is unavailable in a strict managed Hook, fail closed: report the unavailable capability and do not silently reroute or execute the unchanged package under another role. Any fallback behavior belongs only to the explicitly direct-router or unmanaged advisory diagnostic above.

## Fresh-task Sol-supervisor acceptance

After installing with `python3 scripts/install_codex_runtime.py --profile sol-supervisor`, start a new task/restart so the model configuration is loaded. For one substantial, heavy task, acceptance evidence must show nonzero Sol planning/judgment, meaningful Luna execution, Terra review when a second view is useful, compact tool-output summaries, and a complete final report covering evidence/commands, review disposition, routing/model/WCU, remaining risks/blockers, and Git/delivery state when relevant. These are outcome evidence, not a fixed stage recipe: trivial tasks may remain single-model and skip review ceremony.

## Fresh-task flat Terra routing acceptance

After installing with `python3 scripts/install_codex_runtime.py --profile terra-supervisor`, start a new task/restart so the model configuration is loaded. Verify top-level `model = "gpt-5.6-terra"` and `model_reasoning_effort = "high"`; `[agents]` must still select Luna/medium with concurrency two. Do not check or assume a `max_depth` setting: the public configuration does not expose one. With `terra-supervisor`, managed Hooks use advisory routing by default; strict requires the separate `--routing-profile strict` option. For a smoke task that is explicitly selected and suitable for decomposition, evidence may show the top-level Terra directly dispatching Luna for bounded work, a Terra reviewer when an ordinary second view is useful, and `sol_architect` when decision density justifies it. Other tasks may complete directly or use the documented advisory fallback. Acceptance must not require a child to spawn another child or treat nested delegation success as evidence.

## Low-wait evidence

Capture enough task evidence to show that the supervisor waited only when the next step depended on the result, used one reasonable bounded wait rather than interval polling, and counted actual monitoring/polling cost in WCU. The wait bound must be proportional to the package; a timeout is incomplete status, not evidence that the child has no result. A supervisor must receive, intentionally cancel, or explicitly preserve an incomplete required child before ending. After spawning, it should do useful non-overlapping work when such work exists; do not manufacture busywork merely to avoid waiting. Do not claim detached execution, zero waiting, or child-nested delegation when the trace does not show it.

For high-judgment tasks, also inspect whether delegation reduced uncertainty. Repeated Terra/Luna reasoning over the same unresolved invariant without a discriminating experiment or artifact is a routing failure even when the spawns were technically correct. The adaptive recovery is one compact `sol_architect` query with an explicit required output (construction, counterexample, tradeoff, or proof obligation), followed by a falsifiable path or an honest `[UNCERTAIN]` stop. Acceptance does not require Sol when Terra or an oracle is already converging.

Inspect critical-path order and context transfer as cost evidence. An implementation worker should receive a sufficiently stable construction; an ordinary reviewer should receive an artifact/evidence packet or a narrow pre-mortem hypothesis. Spawning both before the core invariant exists is duplicate architecture search, not useful parallelism. Child prompts should be self-contained and use no inherited turns, or the smallest supported history, unless a named dependency requires more; a long-history fork needs a concrete justification in the trace.

## Terra/Sol A/B procedure

Use this procedure to measure the Terra candidate without changing the task contract:

1. Write one self-contained task prompt with fixed acceptance tests, repository state, allowed scope, and a stop condition. Do not rewrite it between runs.
2. In a disposable runtime home, install `--profile terra-supervisor`, start a fresh task with that exact prompt, and capture the result, commands, validation, wall time, model token totals, review disposition, and remaining risks.
3. Reset only the disposable runtime home to the same pre-run state, install `--profile sol-supervisor`, start a fresh task with the identical prompt, and capture the same evidence fields. Do not compare runs with different code, tools, or hidden follow-up work.
4. Compute each run as `WCU = 25*T_sol + 10*T_terra + 1*T_luna`, using cumulative attributed tokens from the session audit. Mark WCU `[UNCERTAIN]` if logs, descendants, or token attribution are incomplete.
5. Prefer Terra for this task class only when it preserves the same acceptance outcome and evidence quality at a lower measured WCU; record any quality loss, extra retries, or review gap rather than selecting on cost alone. Keep `preserve` as the normal CLI default unless an explicit profile choice is made.
