# Open-quality pilot fixtures

These four directories materialize one compact starting bundle for each outcome
class selected for the first controlled pilot. They are evaluation inputs, not
runtime SOP components and not golden solutions.

| Fixture | Agent-visible starting point | Independent evidence |
|---|---|---|
| `out_product_02` | Runnable stdlib experiment tracker with frozen API and intentionally weak UI | API behavior oracle; visual/browser quality remains blind/external |
| `out_idea_01` | Closed-world bundle: 24 literature cards, 12 replay traces, collision map, adapter contract | Full-schema/evidence checker; scientific quality and open-world novelty remain blind/external review |
| `out_research_02` | Immutable proposal, preregistration, results, order and provenance | External checker must recover the planted NO-GO blockers |
| `out_simple_02` | Green typed DTO/serializer repository | Compatibility/minimal-diff oracle plus external process telemetry |

Only each `workspace/` directory is copied to an evaluated Agent. `oracle/`,
`fixture.json`, and `immutable-sha256.json` stay evaluator-side. This physical
separation prevents a submission from approving itself or rewriting the
expected evidence. The pilot runner should make research evidence read-only and
collect submissions outside immutable paths even though the hash oracle will
also reject changes.

`out_idea_01` deliberately measures reasoning over its frozen evidence surface,
not open-world literature retrieval or a claim of globally current novelty.
Its evaluator-side `oracle/controls/` pair proves that a complete valid
submission passes and that deleting one required nested field fails at that
field's schema path.

Create a deterministic materialized input file:

```bash
python3 materialize_fixture.py out_product_02 /tmp/out_product_02.zip
```

Validate all source bundles, deterministic archive hashes, starting states, and
independent oracles:

```bash
python3 -m pip install --requirement ../requirements-ci.txt
python3 verify_fixtures.py
```

The committed bundles contain no dependency directories, model outputs, hidden
answers, screenshots, or binary archives. Browser quality, blind research
judgment, Agent/WCU counts, network use, and unrequested artifacts outside the
candidate root remain study-runner evidence rather than self-reported fixture
checks.
