# Frozen long-horizon agent evidence bundle

This directory is the complete offline evidence surface for `out_idea_01`.
It contains 24 structured literature cards, 12 deterministic benchmark replay
traces, a collision map, and the public adapter contract. Literature summaries
are short fixture annotations; use each card's arXiv URL to verify the primary
source. The replay traces are purpose-built evaluation records, not reported
scores from the cited papers.

Write the proposed candidate set to `submission.json` following
`submission.schema.json`. The schema constrains evidence and falsifiability,
not the scientific answer: no candidate, operation, or final selection is
pre-filled. Network access is not part of this fixture, so unsupported external
claims must be labelled as uncertainty rather than invented citations.
