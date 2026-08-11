---
name: research-execution-grill
description: Stress-test and operationalize an approved scientific proposal before implementation, meaningful experiments, or material scale. Use adaptive evidence and gates by default; use the signed v3 authorization profile only when explicitly required. Never replace the approved idea unless asked.
---

# Research Execution Grill

Treat the proposal as an approved direction. Improve its execution and evidential quality; do not restart idea generation or admission review.

1. Read the closest project instructions and the authoritative adaptive SOP at [`../../../sop/tier1-skeleton/research-execution-grill.md`](../../../sop/tier1-skeleton/research-execution-grill.md).
2. State the claim being tested, the smallest informative outcome, failure/kill criteria, budget, and the oracle that can distinguish success from implementation error.
3. Freeze the original claim, primary estimand, method semantics, baseline, data/split, analysis method, success criterion, and formal budget. Map claim-critical equations/pseudocode/loss/gradient/mask/state/trajectory/reward semantics to implementation locations and independent deterministic/naive/property oracles.
4. Identify the few plausible failure modes that could invalidate the result: leakage, unfair baselines, weak measurement, confounding, hidden adaptation, irreproducibility, or an incorrect implementation.
5. Choose checks and stages that fit this proposal. Freely combine, skip, reorder, or add code readiness, acquisition, oracle validation, pilot, and scale work. Do not require human labels, registries, blinded bundles, or fixed stage names when the claim does not need them.
6. Let the agent explore and revise tactics while preserving the frozen contract. A weaker secondary finding never replaces the original verdict. Require a HUMAN decision only when the contract materially changes or a credential/privacy/irreversible/public boundary is crossed.
7. Run the cheapest discriminating check. Synthetic, mock/stub, smoke, and code-readiness outputs are `paper_eligible=false` and cannot trigger scientific GO. Evidence-bearing code fails fast; automatic runtime fallback across method/model/backend/device/data/metric/analysis is forbidden. An equivalent alternative uses a new explicit run ID and the original acceptance.
8. Use independent review when it can test a credible residual failure path. Do not require review as ceremony, move the acceptance line mid-review, or continue successor gates without new evidence.
9. Accept only real outputs and reproducible evidence. Never fabricate or proxy human judgments, hide failed checks, leak evaluation data, or weaken the claim to declare success. Present intermediate and final evidence using [`../../../sop/tier1-skeleton/references/research-evidence-presentation.md`](../../../sop/tier1-skeleton/references/research-evidence-presentation.md).

Use the signed v3 profile only when project instructions or an external/high-assurance boundary explicitly require it. In that case, read [`../../../sop/tier1-skeleton/references/research-execution-grill-artifact.md`](../../../sop/tier1-skeleton/references/research-execution-grill-artifact.md) and run [`../../../scripts/validate_research_execution_grill.py`](../../../scripts/validate_research_execution_grill.py) exactly; partial v3 evidence never authorizes.

Return the frozen execution/method-fidelity contract, checks actually performed, key evidence and eligibility, original claim verdict, unresolved failure modes, pilot/scale decision, and the next executable step.
