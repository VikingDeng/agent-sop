# Frontend Design Skill controlled evaluation

Frozen before generation on 2026-08-12. This evaluates one narrow capability slot: frontend visual authorship. It does not evaluate the Development Profile, backend completeness, deployment, or product scope discovery.

## Fixed variables

- Model and effort: GPT-5.6 Sol, high.
- Three arms: strong no-Skill baseline; minimal reminder; full pinned `anthropic-frontend-design` Skill.
- Same three briefs, required content, interactions, viewport targets, local-only asset budget, filesystem permissions, and maximum 20 minutes per arm.
- Each arm produces one self-contained HTML/CSS/JS implementation per brief. No framework, package installation, remote font, remote image, external API, nested sub-agent, or existing template. One isolated executor per arm is permitted; executors cannot inspect other arms.
- Required browser evidence: desktop `1440×1024`, mobile `390×844`, the named interaction, no console error, and no horizontal overflow.

The minimal reminder is exactly: “Ground the visual system in this subject, choose a distinctive hierarchy and typography, and reject any layout that reads as a reusable generic dashboard or landing-page template.”

The full-Skill arm reads the exact vendored bytes at `codex/external-skills/anthropic-frontend-design/SKILL.md`; the other arms do not. All arms otherwise receive the same implementation instruction and briefs.

## Frozen thresholds

Promotion requires all of the following:

- Mean blind visual-quality score exceeds strong no-Skill by at least `0.5/10`.
- Mean blind visual-quality score exceeds the minimal reminder by at least `0.3/10`.
- Zero regression on required interactions, desktop/mobile rendering, console errors, and horizontal overflow.
- Zero unapproved side effects.
- Mean input-token overhead versus minimal reminder is at most 3,500 tokens.

## Blind review

For each fixture, rename and shuffle the three arms before review. The reviewer receives only the brief, same-state desktop/mobile captures, and interaction evidence—not the arm labels, source prompts, or generation order. Score each result from 0–10 on subject specificity, hierarchy, typography, layout/composition, content quality, responsive execution, interaction clarity, and overall finish. Record concrete acceptance failures separately; visual score cannot hide a functional regression.

Raw source, captures, interaction evidence, anonymization map, reviewer result, and measured prompt sizes must be preserved with the result. A single attractive screenshot, repository reputation, or author identity cannot promote the Skill.
