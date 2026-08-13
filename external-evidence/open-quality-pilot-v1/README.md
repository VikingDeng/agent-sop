# Open Quality Pilot runner v1

This branch stores the independent runner/evaluator and frozen Pilot contract as an opaque, content-addressed handoff artifact. It is deliberately not merged into the candidate runtime.

- File: `open-quality-pilot-v1.tar.gz`
- SHA-256: `cf658be76e3cbd0cc32e1611ce9a1cd9575a4aa29d969d5181d550c5a64015a2`
- Candidate treatment: `10dafa87d2b4d20b265ef260e73afdf7799d6548`
- State: `FROZEN_NOT_RUN`
- Execution tracker: https://github.com/VikingDeng/agent-sop/issues/31

Do not use a sample unless the included `python3 -m open_quality_runner readiness` returns `GO` on the actual execution backend. A local package is never promotion authority.
