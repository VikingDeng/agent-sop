# Research Execution Grill v3 strict event and artifact contract

This is an optional high-assurance profile, not the default workflow for every
proposal. Use it only when project instructions, an external audit requirement,
or a genuinely high-value authority boundary explicitly selects signed v3.
Otherwise use the adaptive Grill SOP and choose evidence that matches the claim.
Once selected, this profile remains fail-closed for the action it protects.

Within this strict profile, schema `3` with protocol
`research-execution-grill-v3` is the only authorizing contract. Schema v1 and
v2 are historical and require matching `--audit-v1` or
`--audit-v2`; a successful audit exits `4` and never authorizes an action.

## Authority split

`scripts/research_grill_state_machine.py` is the pure lifecycle authority. Its
frozen dataclasses and enums accept already validated events, enforce sequence,
and return explicit `validation_error`, `operational_blocked`, `not_authorized`,
or `authorized` decisions. It performs no filesystem, JSON-file, subprocess,
OpenSSH, or scientific-metric work.

`scripts/validate_research_execution_grill.py` is the external adapter. It
validates artifacts, scientific contracts, trust policy, detached signatures,
reviews, and the signed ledger before passing immutable events to the pure
state machine. Payload `status` and `authorization` fields are informational;
neither is an authorization input.

## Two-phase CLI

Prepare an unsigned canonical candidate:

```sh
python3 scripts/validate_research_execution_grill.py execution-grill.json \
  --prepare-event action_opened \
  --requested-action phase0_launch \
  --candidate-out phase0-open.candidate.json \
  --trust-policy trust-policy.json \
  --trust-policy-sha256 sha256:<external-policy-pin> \
  --lineage-ledger execution-grill-ledger.json \
  --lineage-tail-sha256 sha256:<externally-observed-tail>
```

Preparation exits `5` (`PREPARED_NOT_AUTHORIZED`). `--prepare-authorization
ACTION` is an alias for preparing `action_finalized`. Without `--candidate-out`,
canonical JSON is written to stdout. Candidate files use exclusive creation;
an existing path is never overwritten.

The validator never signs or appends an event. An external lineage authority
must sign the candidate envelope and atomically append the event under its own
ledger lock. Revalidate afterward:

```sh
python3 scripts/validate_research_execution_grill.py execution-grill.json \
  --required-authorization phase0_launch \
  --trust-policy trust-policy.json \
  --trust-policy-sha256 sha256:<external-policy-pin> \
  --lineage-ledger execution-grill-ledger.json \
  --lineage-tail-sha256 sha256:<externally-observed-tail>
```

Exit `0` means the exact action has a valid signed final event. Exit `1` is a
malformed, invalid, stale, untrusted, or contract error. Exit `3` is operational
unavailability or an action not yet authorized. Exit `4` is legacy audit only;
exit `5` is candidate preparation only.

## Canonical signed events

The unsigned body has exact fields:

```json
{
  "seq": 0,
  "previous_event_hash": "EMPTY",
  "event_type": "checkpoint_opened",
  "checkpoint_id": "checkpoint-2026-001",
  "proposal_id": "proposal-001",
  "proposal_hash": "sha256:...",
  "lineage_id": "lineage-001",
  "protocol_version": "research-execution-grill-v3",
  "requested_action": null,
  "signer_principal": "lineage@example",
  "signer_role": "lineage_authority",
  "bindings": {
    "action_order": "static_acquisition,human_oracle,phase0_launch,scale_launch"
  },
  "expected_ledger_tail": "EMPTY",
  "outcome": null
}
```

`event_hash` is the canonical SHA-256 of the body. The detached OpenSSH
signature covers canonical JSON `{"body": body, "event_hash": event_hash}` in
namespace `research-execution-grill-v3-lineage`. Ledger transport is:

```json
{
  "schema_version": 3,
  "protocol_version": "research-execution-grill-v3",
  "events": [
    {"body": {}, "event_hash": "sha256:...", "signature_path": "event.sig"}
  ]
}
```

Signature paths are transport metadata outside the hashed body. A canonical
hash is deterministic content identity, not a signature, role, or permission.
Canonical hash values never substitute for detached signatures.

Every candidate binds the observed ledger tail in both `previous_event_hash`
and `expected_ledger_tail`, and the CLI requires the same independently supplied
`--lineage-tail-sha256`. A genesis `checkpoint_opened` candidate uses the exact
`EMPTY` sentinel; `EMPTY`, a zero hash, a stale hash, or a malformed hash is
invalid once any ledger event exists. Any intervening append makes a candidate stale. The external
authority owns locking and atomic append; the validator only re-reads.

## Authoritative lifecycle

One `checkpoint_opened` spans this exact action order:

```text
static_acquisition -> human_oracle -> phase0_launch -> scale_launch
```

Each action has one `action_opened` and one `action_finalized`, with an optional
single `correction_applied` between them. Finalized authorized actions form an
exact prefix. Skips, reopen, duplicate checkpoint, second correction, branching
from the same before-state, stale tails, out-of-order events, and events after a
terminal result are invalid. There is no project-local reset.

`action_opened` binds the initial action core, complete action evidence
manifest, frozen review plan, and current tail. A passing complete initial
review may finalize directly. A blocked initial review may only prepare one
correction binding before/after core and manifest plus the canonical
`initial_review_cycle_hash` of the complete signed blocked initial set. The
blocked set must remain append-only and recompute to that exact hash before a
re-review or final event is accepted. It is followed by one complete
re-review. Passing re-review finalizes `authorized`; blocked re-review finalizes
`architecture_reset_required`, which revokes every earlier authorization in the
checkpoint and after which no v3 event is legal.

## Evidence manifest

The action-specific manifest contains every relevant consumed artifact, sorted
by stable ID. Each row contains ID, kind, exact evidence class, producer stage,
source SHA-256, semantic SHA-256, complete attestation payload, signature
identity, and consumed artifact IDs/semantic hashes. Paths and signature
transport are excluded. Any evidence identity change changes the manifest and
invalidates the review and final event.

Static Acquisition requires a content-bound passed Code Readiness code-test
contract and its complete signed action review; it does not require future
labels. Human Oracle requires a verified static-production source registry and
blinded audit bundle. Phase 0 requires the
designated registry/bundle, sealed human labels and derivation, clean
reproduction, positive finite budget, and signed runtime capability evidence.
Scale requires the exact designated bundle, signed Phase 0 raw and summarized
results, frozen scale conditions and kill gates, and a finite positive scale
budget. Passed stage declarations never substitute for missing evidence.
Another valid bundle is not interchangeable.

Well-formed, correctly signed `runtime_available: false` is
`operational_blocked`/exit `3`. Malformed, unsigned, stale, mismatched, or
wrong-role evidence of any class is a contract error/exit `1`. Exit `3` is
reserved for that signed runtime denial, unavailable required external tools or
trust/lineage infrastructure, and a valid action that is not yet authorized.

## Review-cycle hash

Every review binds requested action, opened-event hash, action core, evidence
manifest, frozen plan, reviewer identity/context/model/role, phase, verdict,
and normalized findings. Reviews are detached-signed by the exact planned
`reviewer` principal.

The frozen plan is injective: every slot has a nonempty unique `reviewer_id`,
unique `signer_identity`, and unique `reviewer_context_id`. These three values
remain a one-to-one correspondence in every signed initial and re-review row.
No signer or context may satisfy two reviewer IDs, and a reviewer ID may not
swap signer or context between phases. A complete current cycle contains
exactly one signed row for every frozen slot.

`review_cycle_hash` canonically projects the complete sorted planned reviewer
set and every signed review identity, verdict, normalized findings,
reviewer context, `source_sha256`, `semantic_sha256`, and
`attestation_sha256`. Signature paths
and other transport are excluded. A final event must reference a retained,
complete cycle whose bindings match exactly.

## Trust boundary

The separately supplied trust policy contains public identities, public keys,
and roles and is pinned outside the Grill artifact with
`--trust-policy-sha256`. Artifact roles remain `acquisition_attestor`,
`human_oracle`, and `runtime_attestor`; review and event roles are `reviewer`
and `lineage_authority`. Missing tools or runtime availability are operational;
untrusted or malformed signed evidence is invalid.

The skill and validator never create, request, store, or use human/reviewer private keys.
Tests may generate ephemeral keys only in temporary directories.
