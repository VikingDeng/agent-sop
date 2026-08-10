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
6. **Resume routing defect** — runtime denial of the resume primitive guarantees a closed role-bound agent cannot be resumed, but telemetry does not bind agent IDs to package/phase/requested role/actual model/open state. Correction/re-review uses a fresh explicit typed spawn; package IDs/phases and one initial/one correction/one re-review budgets remain unchanged, and role/model changes never reset budget. Already-open matching-agent reuse and actual-model verification are supervisor policy plus PostToolUse/session audit; once evidence exists, violations fail closed and WCU is [UNCERTAIN].
7. **Supervisor monitoring tax** — use one bounded long wait per decision point, compact evidence, and fresh top-level execution tasks for heavy projects when the user can start them. This reduces avoidable polling tax but does not remove the app's need for progress updates.

The adaptive/outcome-first architecture remains in force: these are proportional practices, not fixed gate/hash/signature/validator requirements. Unresolved items remain [UNCERTAIN]; nonblocking hardening is backlog, not a silent acceptance change.
