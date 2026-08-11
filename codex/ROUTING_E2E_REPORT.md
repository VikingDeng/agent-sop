# SOP consistency hardening — E2E evidence report

## Scope and sources

This report records the three supplied real traces: Codeforces 2236F2, the CDC controlled pilot, and GitHub issue #97, plus the runtime/root/process evidence observed around them. It follows the existing routing-evaluation documentation convention; it is not a new framework. Fresh project directories and commits were local only; no external submission, push, merge, or deployment occurred.

## Results and routing

| Trace | First result / elapsed | Routing observed | Reviewer outcome |
|---|---|---|---|
| Competition | Luna produced a fast plausible solution; exact elapsed is [UNCERTAIN] | Luna initial → Terra review → one correction/re-review; the resumed correction and re-review actually ran on Sol high, which is a routing defect | Terra found the n=100000, x=2, a_i=4 overflow/wrong-answer case; one consolidated correction converged and passed sample, 2280 brute, sanitizer, and stress checks |
| Research | CDC pilot started and ran quickly; exact elapsed/first-result timestamps are [UNCERTAIN] | Self-check and Terra review; exact child WCU is [UNCERTAIN] | Self-check caught budget overrun and reported-vs-actual continuation mismatch. Terra instrumented exactly 172800 continuations / 345600 calls and approved the frozen synthetic claim; three configurable-runner medium issues moved to pre-scale backlog |
| Development | Initial Luna worker captured/reported `2809 passed` for the full suite; exact elapsed/first-result timestamps are [UNCERTAIN] | Luna initial worker → independent Sol risk review | The Sol risk reviewer reran 10 focused tests, including real SQLite and dead-embedder coverage, and returned LOW-only findings; full-suite rerun is [UNCERTAIN]. A focused five-file API review was unnecessarily expanded by the full security-scan skill, so a timebox is required |

Child-reported WCU was [UNCERTAIN]; raw session logs proved the actual models. Cached input counts toward WCU, and monitoring/polling WCU is also real cost. This report does not infer zero cost from missing child-reported data.

## Evidence-to-policy changes

1. **Competition correctness** — preserve Luna execution, Terra semantic review, one consolidated correction, and one re-review without adding fixed gates, hashes, or signatures; triage findings by impact on frozen acceptance.
2. **Research integrity** — require self-checks to compare budget/report/actual continuation counts; accept frozen-claim evidence while moving nonblocking configurable-runner issues to pre-scale backlog.
3. **Development review scope** — add bounded REVIEW_PROFILE=ordinary|api|security|architecture/data; API correctness may use Sol risk judgment, while full codex-security workflow requires a concrete adversarial trigger.
4. **Git-root hazard** — check git rev-parse --show-toplevel before the first write, stage, or commit in a new project; use an independent git init or worktree when intended.
5. **Suite contention** — allow one full suite at a time; before restart inspect/close only the worker's own prior process/session and do not launch duplicate heavy suites.
6. **Resume routing defect** — telemetry does not bind agent IDs to package/phase/requested role/actual model/open state, but a global resume ban also forces unnecessary respawns. Advisory mode therefore allows `resume_agent` with an auditability warning; strict mode denies it. Correction/re-review uses a matching live agent only when identity evidence exists and otherwise uses a fresh explicit typed spawn; reuse or role/model changes never reset an applicable budget, and evidenced mismatches keep WCU [UNCERTAIN].
7. **Supervisor monitoring tax** — use one bounded long wait per decision point, compact evidence, and fresh top-level execution tasks for heavy projects when the user can start them. This reduces avoidable polling tax but does not remove the app's need for progress updates.

The adaptive/outcome-first architecture remains in force: these are proportional practices, not fixed gate/hash/signature/validator requirements. Unresolved items remain [UNCERTAIN]; nonblocking hardening is backlog, not a silent acceptance change.

## Newly observed flat-routing evidence

The real App E2E added three observations. That same Terra child owned the real semantica #859 project end to end and reported both the normal-order and reverse-order task runs as `58 passed`; this was one child report, not two independent traces. That child had no available tool for continuing delegation, so child-nested routing was not a viable prerequisite. Its parent Sol supervisor performed eleven synchronous 60-second waits, creating a substantial monitoring/waiting WCU tax. A fresh Terra-root run has not been verified.

These observations motivate, but do not yet prove, flat root routing in the App: start the foreground on Terra for the relevant task classes, let it dispatch Luna/Terra/Sol specialists directly, and use bounded waits only at dependency points. This report does not fabricate an App-root pass or nested-delegation success.

## Fresh CLI flat-routing smoke

After installing the Terra supervisor profile with Codex CLI 0.147.0, fresh task `019fecd8-df39-7250-bb5f-dacc8605982d` ran a read-only routing smoke. The root actually used Terra, directly spawned one typed `sol_architect` on Sol and one typed `luna_executor` on Luna, and issued one wait. All three sessions completed. The audit attributed 138,207 Terra tokens, 48,195 Sol tokens, and 70,370 Luna tokens: 256,772 raw tokens and 2,657,315 WCU.

Cost remains `[UNCERTAIN/PARTIAL]`: encrypted spawn messages hid optional package metadata, the root did not record successful child closes, and the conservative shell classifier reported the Sol architect's read-only `rg` alternation pattern as non-read-only because the quoted search expression contained `|`. Inspection of the raw call showed no mutation. This validates role registration and flat dispatch in a fresh CLI task, not a fresh App foreground; the next App task remains the App-specific acceptance point.
