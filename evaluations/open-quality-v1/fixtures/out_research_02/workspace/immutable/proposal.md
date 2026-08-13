# Signed Phase 0 proposal: causal-delta replay

- Proposal ID: `cdr-phase0-2026-06-11`
- Frozen at: `2026-06-11T14:00:00Z`
- Signature: `principal-investigator/72f49d06`
- Claim boundary: Phase 0 can only decide whether to allocate a larger run.

## Method invariant

After a failed long-horizon attempt, the approved method locates the earliest
observable state delta that contradicts the task invariant, constructs one
counterfactual action at that point, and supplies the verified delta pair to
the next attempt. It does not replace the benchmark evaluator, change the base
model, add search branches, or train model weights.

## Frozen comparison

The baseline is the same ReAct-style policy, model, task inputs, tool budget,
and retry budget without causal-delta replay. Six paired real tasks are run in
the preregistered interleaved order. The primary metric is task success. Cost
and collateral damage are guardrails, not substitutes for success.

## Claim and exclusions

Phase 0 is `GO` only when every validity gate passes and the method improves
mean task success by at least 0.10 over baseline without worse collateral
damage or more than 1.20x tool cost. A wiring smoke, replay, code-readiness
check, or invalid run cannot satisfy this claim.
