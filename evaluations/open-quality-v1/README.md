# Open Quality v1 — evaluation contract

This directory is an evaluation asset, not a runtime layer. It tests whether a
candidate improves open-ended judgment and real delivery without making
bounded work heavier. Static validation, package hashes, self-tests, a document
diff, or one showcase cannot promote the candidate.

**Current status:** the routing/outcome contracts, four verified starting
bundles, and an unverified-package validator exist. No fresh A/B/C outcome run
has happened. Candidate C remains disabled/unpromoted and quality lift is
`NOT_ESTABLISHED`.

## Goal and routing boundary

The goal is measurable net lift on open product/idea work, approved-research
fidelity, and delivery consistency per WCU and per user correction. Bounded
changes retain the direct edit → focused check → diff path.

| Primary mode | Frozen meaning |
|---|---|
| `fast_path` | Scope and Oracle are bounded: act, run the nearest check, inspect the diff, deliver. |
| `option_search` | A material direction is unresolved: compare genuinely different choices and discriminating evidence. |
| `contract_ready_execution` | Direction and acceptance are frozen: implement faithfully without reopening them. |
| `evidence_closure` | The artifact/run exists; remaining work is claim-matched walkthrough, Oracle, review, and verdict. |
| `re_contract` | A method, claim, benchmark, public behavior, authority, or material budget changed: stop for a HUMAN decision. |

Overlays add only an evidenced need. They cannot change acceptance or turn a
bounded task into ceremony.

## Two separate suites

| Suite | Frozen content | Purpose |
|---|---|---|
| `routing-cases.json` | 24 balanced boundary prompts, six per stratum | Entry mode, overlays, and HUMAN boundary. Twelve marked cases form the pilot; it includes `re_contract`. |
| `outcome-fixtures.json` | 12 task contracts, three per stratum | Prompt, starting-artifact description, Oracle contract, Blind quality rubric, and resource ceiling. Four marked cases—one per stratum—form the pilot. |

The four committed pilot inputs and evaluator-side Oracles live under
`fixtures/`. `verify_fixtures.py` checks their locked trees/deterministic
archives, starting states, and negative controls without supplying a golden
solution. Product browser quality, research Blind quality, and runtime/WCU
remain external study evidence.

The strata are `open_product`, `research_ideation`,
`approved_research_execution`, and `simple_bounded_change`. Pilot is a cheap
screen: one matched repetition of 12 routing cases and four real outcomes for
all three arms. Promotion is three fresh repetitions of all 24 routing cases
and all 12 outcomes. Routing answers are never scored as product or research
outcomes.

## Arms and controls

| Arm | Frozen treatment |
|---|---|
| **A — raw** | Same Codex model/build and prompt with platform instructions only. |
| **B — main** | `main@497b5ba436a1a0392af01db3f2fecd3aa53e95e9` with its normal installed runtime. |
| **C — candidate** | One exact candidate commit/tree branched from B and frozen before results. |

All arms use the same materialized input, model availability, effort,
permissions, Oracle, rubric, and resource ceiling. Runs are isolated and order
is frozen before execution. For each fixture/replicate, a reviewer must score
the concealed A/B/C artifacts in randomized order, or reviewers must be
balanced so reviewer identity is not confounded with an arm. Prior-arm outputs
cannot enter another arm.

## Authority boundary

`study-manifest.schema.json` and `validate_and_score.py` check a closed package:
treatment and static-contract digests, stage-specific exact slots,
materialized-input digests, relative in-root paths, file hashes, unique
run/evidence/assignment identities, budgets, resource ceilings, and unchanged
acceptance/authority. They also derive clearly named `reported_*` summaries.

The result states are deliberately limited:

- `PACKAGE_INVALID`: bytes, slots, contract, or ceilings are missing/drifted;
- `PACKAGE_COMPLETE_UNVERIFIED`: the package is internally consistent, but its
  source claims are not authenticated;
- `PROMOTION_REQUIRES_INDEPENDENT_AUTHORITY`: always true for a locally
  complete package.

Hashes show that referenced bytes have not changed relative to the manifest.
They do **not** prove who generated them, that A/B/C ran the reported treatment,
that the Oracle executed independently, that a review was blind, that the
assignment was random, or that reported token usage agrees with a real trace.
For this reason the local CLI never emits `ADVANCE_TO_PROMOTION` or
`PASS_PROMOTION`; `promotion_eligible` is always false.

An independent collector/evaluator—or an explicit HUMAN decision using its raw
evidence—must derive Git treatment identity, arm isolation, token/WCU from the
platform trace, Oracle execution, and blind assignments. That authority must be
outside the candidate repository/runner. Adding another self-signed receipt or
an in-repository signature verifier does not close this boundary.

## Metrics and preregistered decision policy

1. **Oracle:** task-specific executable or independent checks. Routing gold is
   only the entry Oracle.
2. **Blind quality:** 0–10 against a frozen rubric; arm identity concealed.
3. **WCU:** independently derived
   `25*T_sol + 10*T_terra + 1*T_luna`, including cached input/monitoring where
   the trace exposes them. Missing attribution is uncertain, never zero.
4. **Rework:** user corrections plus agent repair cycles under unchanged
   acceptance.
5. **Elapsed:** per-run wall time; summed values are aggregate run-seconds, not
   study wall-clock when runs overlap.
6. **Variance:** within-fixture quality dispersion across fresh repetitions.

The numeric gates below are a frozen decision policy, not a statistical
significance claim. Reports retain class-level results; aggregate gain cannot
hide damage to simple tasks or approved-method fidelity.

Pilot may be authorized to advance only when the package is independently
authenticated, no hard kill is present, C routing exactness and Option Search
precision/recall are each at least 0.80, C open-quality mean is at least B
+0.15, C Oracle success is no lower than either control, and total WCU is at
most 2.0× B. Pilot is intentionally underpowered and can only reject or justify
a confirmatory run.

Promotion may be approved only when independent authority confirms all of:

- C Oracle success is 1.00 and no class is below either control;
- routing exactness and Option Search precision/recall are each at least 0.90,
  with zero heavy-flow false triggers on gold fast paths;
- open-strata Blind quality is at least +0.50 over the stronger A/B control and
  wins at least 65% of paired fixtures against each; no class regresses by more
  than 0.25;
- user corrections are at most 0.70× B, total rework at most 0.90× B, and
  within-fixture quality SD at most 0.90× B (or at most 0.05 when B ≤0.05);
- total WCU is at most 1.35× B and Blind-quality/WCU at least 0.80× the best
  control;
- simple-task Oracle success is 100%, heavy false triggers are zero, median WCU
  is at most 1.10× the stronger-quality control, median elapsed at most 1.25×,
  and unrequested artifacts/agents are zero.

Changed acceptance, unauthorized effects, missing/contaminated evidence,
candidate Oracle below a control, class quality regression over 0.25, a heavy
simple-task trigger, or an unrequested simple-task artifact/agent is a hard
kill. A failed/no-lift treatment stays disabled. Delete it when it cannot
justify its cost or makes bounded work heavier; a materially changed v2 needs a
new preregistration.

## Commands

Protocol checks exercise the real package path but are not evaluation evidence:

```bash
python3 evaluations/open-quality-v1/validate_and_score.py --validate-only
python3 evaluations/open-quality-v1/validate_and_score.py --self-test
python3 evaluations/open-quality-v1/validate_and_score.py --manifest-template
PYTHONDONTWRITEBYTECODE=1 \
  python3 evaluations/open-quality-v1/fixtures/verify_fixtures.py
```

Routing-only diagnostics remain unverified and promotion-ineligible:

```bash
python3 evaluations/open-quality-v1/validate_and_score.py \
  --stage routing --routing-results routing-results.jsonl
```

A pilot/promotion package has no single-file or self-reported promotion
shortcut:

```bash
python3 evaluations/open-quality-v1/validate_and_score.py \
  --stage pilot \
  --study-manifest evidence/study-manifest.json \
  --evidence-root evidence \
  --routing-results evidence/routing-results.jsonl \
  --outcome-results evidence/outcome-results.jsonl
```

Exit `0` means only that a package is internally complete/unverified; exit `1`
means invalid. `--manifest-template` contains deliberate placeholders.

## Existing evidence and non-evidence

[PR #24](https://github.com/VikingDeng/agent-sop/pull/24) contains one positive
complete-product E2E and one frontend-design three-arm no-go: full Skill
`8.3542 <` raw `8.8667 <` minimal reminder `9.3792`. Those draft observations
are useful prior evidence but are not this study and do not promote a new SOP.
