---
name: research-execution-grill
description: Stress-test an approved scientific proposal before implementation or scale-up. Prepare and verify v3 action events; never generate replacement ideas.
---

# Research Execution Grill

Treat the approved proposal as authoritative. Do not generate replacement ideas
or redo proposal admission.

## Required workflow

1. Read project instructions, the authoritative SOP, and the artifact reference.
2. Require `schema_version: 3` and `research-execution-grill-v3`. Treat v1/v2 as matching explicit audit-only protocols; they never authorize.
3. Preserve exact action order `static_acquisition -> human_oracle -> phase0_launch -> scale_launch`. Code Readiness is synthetic and can only support Static Acquisition. Static Acquisition does not need future labels.
4. Keep `bootstrap/evidence_acquisition` separate from `experiment_authorization`. Bootstrap MUST NOT run a subpilot/pilot/experiment, compute scientific metrics, inspect outcomes for adaptation, or emit scientific claims. Validate required artifact IDs, provided artifact IDs, disjointness, and dependency cycle.
5. Validate external source files, exact evidence classes, canonical hashes, and detached OpenSSH attestations against the externally pinned trust policy. Canonical hashes are not signatures.
6. Freeze the complete review plan. Require a complete signed review cycle bound to action, opened event, core, evidence manifest, plan, reviewer identity/role, verdict, normalized findings, and source/semantic/attestation hashes.
7. Use the two-phase authority boundary. Prepare a canonical candidate with `--prepare-event` (or `--prepare-authorization ACTION`), expect exit `5`, and give it to the external `lineage_authority`. Never sign or append the event yourself. The authority owns atomic append under a lock.
8. Run:

   ```sh
   python3 ~/code/agent-sop/scripts/validate_research_execution_grill.py execution-grill.json \
     --required-authorization phase0_launch \
     --trust-policy trust-policy.json \
     --trust-policy-sha256 sha256:<external-policy-pin> \
     --lineage-ledger execution-grill-ledger.json \
     --lineage-tail-sha256 sha256:<external-ledger-tail>
   ```

   Request `static_acquisition` or `human_oracle` for acquisition packages,
   `phase0_launch` before experiments, and `scale_launch` before material scale.
   Missing runtime capability is `operational_blocked`, not
   `scientific_no_go`. Invalid or untrusted evidence is a contract error.
9. Continue only when exit `0` verifies the exact action's signed final event. Use the exact `EMPTY` tail sentinel only for genesis preparation. Treat exits `1`, `2`, `3`, `4`, and `5` as nonauthorizing. A blocked re-review finalizes terminal `architecture_reset_required`, revokes every prior action in the checkpoint, and permits no project-local reset.

## Output

Return proposal/checkpoint/action, candidate or final event hash, observed ledger
tail, review-cycle hash, exit code, and blockers. Route event/schema details to
`sop/tier1-skeleton/references/research-execution-grill-artifact.md`.
