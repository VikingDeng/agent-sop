---
name: research-execution-grill
description: Stress-test an already approved scientific proposal before implementation or before scaling experiments. Use when Codex is asked to implement a research proposal, design its experiment plan, launch an expensive pilot, or expand seeds/models/data/compute. Convert proposal claims into a blocked-or-ready execution contract; do not generate ideas or redo proposal admission unless the user explicitly asks.
---

# Research Execution Grill

Treat the user's proposal as the authoritative approved direction. Challenge execution ambiguity and scientific validity, not whether a different idea would be more exciting.

## Authority

1. Read the applicable project instructions.
2. Read the authoritative SOP completely at `~/code/agent-sop/sop/tier1-skeleton/research-execution-grill.md`.
3. Read its artifact contract at `~/code/agent-sop/sop/tier1-skeleton/references/research-execution-grill-artifact.md`.
4. Follow project-local overrides when they are more specific, but never weaken the SOP's fail-closed gates.

## Workflow

1. Identify the proposal source, stable ID, content hash, and checkpoint: `pre_implementation` or `pre_scale`.
2. Create or update the project-local `execution-grill.json` using the artifact contract.
3. Interrogate only implementation and experiment risks: semantic ambiguity, claim–experiment coverage, baseline parity, experimental unit and replication, holdout access, metric/oracle shortcuts, pilot→scale criteria, reproducibility, and budget.
4. Split `bootstrap/evidence_acquisition` from `experiment_authorization`. Bootstrap may acquire only non-experimental source, license, registry, raw-data, label-package, or review-packet evidence and must not require its own future outputs. It MUST NOT run a subpilot, pilot, or experiment; compute scientific metrics; inspect outcomes for adaptation; or emit scientific claims. Only `experiment_authorization` consumes frozen, hash-bound evidence and permits the pilot. Represent each project-specific DAG with required artifact IDs and provided artifact IDs, check their disjointness before validator code begins, detect any dependency cycle, and repair the contract once. Keep one authoritative current gate/validator; preserve blocked reviews append-only without cloning whole Grill/validator versions.
5. Use `scientific-critical-thinking` for bias/confounding/claim pressure and `experimental-design` for assignment, blocking, replication, and sequential-design questions when those skills are available and relevant.
6. Mark unresolved proposal-semantic questions as human gates. Do not resolve them by inventing a conventional default.
7. Before requesting reviews, freeze the complete `review_plan` in the Grill core. Then build the strict JSON review packet and obtain every planned read-only review from an isolated GPT/Codex context. Store each result as a distinct strict JSON artifact. Record both file hashes, controller/reviewer context IDs, allowlisted reviewer model, proposal hash, checkpoint, and canonical Grill core hash; context IDs must differ and every duplicated field must agree. Label GPT/Codex reviews `internal_blind_gpt`; never represent them as external review or delete a planned blocked review.
8. Run:

   ```sh
   python3 ~/code/agent-sop/scripts/validate_research_execution_grill.py execution-grill.json --required-checkpoint pre_implementation
   ```

   Use `pre_implementation` for implementation/pilot and `pre_scale` for material expansion.

9. Continue to the matching action only on exit code `0`. Exit `1`, `2`, or `3`, an unavailable reviewer, an unavailable validator, or a wrong checkpoint is blocking evidence, not permission to continue.

## Output

Return the artifact path, checkpoint, ready/blocked status, unresolved human gates, validator command and exit code, and review artifact. Keep the user-facing summary concise. Do not generate alternative research ideas unless explicitly requested.
