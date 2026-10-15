// ===========================================================================
//  example.typ — demonstration document for the modern-technical template.
//
//  Compile standalone:  typst compile example.typ
//
//  This file shows every component the template offers: callouts, the
//  key-findings box, tables, figures, code, numbered equations and a TOC.
//  Copy it as the starting point for a new report.
// ===========================================================================

#import "modern-technical.typ": report, key-findings, callout

#show: report.with(
  title: [Retrieval-Augmented Agent Memory: A Design Review],
  subtitle: [What actually breaks when an agent remembers across sessions],
  doc-kind: "Technical Report",
  organization: "Research Engineering",
  date: "September 2026",
  authors: (
    (name: "First Author", affiliation: "Research Engineering"),
    (name: "Second Author", affiliation: "Platform"),
  ),
  summary: [
    This report reviews the design space for retrieval-augmented memory in
    long-running agents. We separate three concerns that are usually conflated
    --- what to store, when to retrieve, and how to forget --- and argue that
    most reported failures trace to the third. We close with a short checklist.
  ],
  toc: true,
)

#key-findings[
  + Storing more is not the same as remembering more; unbounded growth degrades
    retrieval precision faster than it improves recall.
  + The dominant failure mode in production is stale memory, not missing memory.
  + A cheap recency-and-usage decay beats a sophisticated relevance model when
    the corpus is small.
]

#callout(kind: "info", title: [Scope])[
  The review covers single-agent systems with a persistent store. Multi-agent
  shared memory raises consistency questions that we only flag in @sec:open.
]

= Design Space

== What to store

The literature broadly agrees that raw transcripts are a poor unit of storage:
they are redundant, they embed the agent's own errors, and they retrieve
badly. The disagreement is about the right replacement.

#callout(kind: "tip", title: [Practical rule])[
  Store the smallest unit that a human could act on without the surrounding
  conversation. Prose summaries usually qualify; individual turns usually do not.
]

== When to retrieve

Retrieval has a cost that is easy to hide: it consumes context window, and it
consumes it *before* the model knows whether it needed it. A retrieval that
fires unnecessarily is worse than no retrieval at all.

== How to forget

This is the least studied and, we argue, the most consequential. A memory
store that only grows develops a distribution shift: entries written by an
early, less capable version of the agent remain retrievable forever.

$ "score"(m, t) = "sim"(m, q) dot e^(-lambda (t - t_m)) dot u(m) $ <eq:decay>

@eq:decay is the standard shape: similarity, down-weighted by age and by how
often the entry has actually been used.

= Observed Failure Modes

#figure(
  table(
    columns: 4,
    align: (left, left, center, left),
    stroke: none,
    table.hline(stroke: 1pt),
    table.header([*Mode*], [*Symptom*], [*Frequency*], [*Mitigation*]),
    table.hline(stroke: 0.5pt),
    [Stale entry], [Confident wrong answer], [Common], [Age decay],
    [Redundancy], [Context bloat], [Common], [Dedup on write],
    [Silent conflict], [Two answers, no flag], [Occasional], [Contradiction check],
    [Over-retrieval], [Slow, shallow answers], [Occasional], [Retrieval budget],
    table.hline(stroke: 0.5pt),
    table.hline(stroke: 1pt),
  ),
  caption: [Failure modes ranked by how often they were observed in the systems reviewed.],
  kind: table,
) <tbl:failures>

@tbl:failures is ordered by frequency, not severity. Silent conflict is the
rarest and the most damaging.

#callout(kind: "warn", title: [Watch for this])[
  A memory system that never contradicts itself is usually a system that
  never stored anything interesting.
]

= Open Questions
<sec:open>

+ *Consistency across agents.* When two agents write to a shared store, which
  one owns a contradicting fact?
+ *Evaluation.* There is still no accepted benchmark for memory, only for
  retrieval, which measures the wrong thing.
+ *Privacy.* Forgetting is a correctness property in some deployments and a
  legal requirement in others; the mechanisms differ.

```python
def should_retrieve(query, store, budget):
    """Cheap gate: skip retrieval when the store cannot help."""
    if store.is_empty():
        return False
    if budget.remaining < MIN_USEFUL_CONTEXT:
        return False
    return store.top_score(query) > SIMILARITY_FLOOR
```

#callout(kind: "alert", title: [Not a benchmark])[
  The numbers in this document are illustrative of the format, not measurements.
]
