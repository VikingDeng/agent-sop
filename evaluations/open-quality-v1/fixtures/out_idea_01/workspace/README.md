# Frozen long-horizon agent evidence bundle

This directory is the complete offline evidence surface for `out_idea_01`.
It contains 24 structured literature cards, 12 deterministic benchmark replay
traces, a collision map, and the public adapter contract. Literature summaries
are short fixture annotations. Each arXiv URL is a frozen provenance identifier,
not an instruction to access or re-verify the source in this offline fixture.
The replay traces are purpose-built evaluation records, not reported scores
from the cited papers.

This frozen fixture tests **closed-world reasoning only**. Every admissible
evidence reference, benchmark split, metric, and probe budget must come from
this directory. A passing submission can show coherent reasoning over this
frozen surface; it cannot establish an exhaustive current literature search,
global novelty, or benchmark prevalence. Those claims remain outside the
fixture and require separate external evidence.

Write the proposed candidate set to `submission.json` following
`submission.schema.json`. The schema constrains evidence and falsifiability,
not the scientific answer: no candidate, operation, or final selection is
pre-filled. Network access is not part of this fixture, so unsupported external
claims must be labelled as uncertainty rather than invented citations.
