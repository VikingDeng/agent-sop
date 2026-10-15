// ===========================================================================
//  main-report.typ — the SAME body, rendered as an internal technical report.
//
//  Compile:  typst compile main-report.typ
//
//  This file exists to prove the point of the whole design. The content/ tree
//  was written for a conference submission — two-column, anonymous, terse.
//  Here it is dropped into a report template with a cover block, a table of
//  contents, callouts and a key-findings box, and NOT ONE WORD of prose
//  changed. Only this adapter file differs.
//
//  Template: @local/modern-technical 0.1.0 (reports/modern-technical/)
// ===========================================================================

#import "@local/modern-technical:0.1.0": report, key-findings, callout

// ---- shared metadata and body (venue-agnostic) ----------------------------
#import "content/_meta.typ": title, authors, affiliations, keywords, abstract
#import "content/introduction.typ": introduction
#import "content/related-work.typ": related-work
#import "content/method.typ": method
#import "content/experiments.typ": experiments
#import "content/conclusion.typ": conclusion

#show: report.with(
  title: title,
  subtitle: [Internal technical report — few-shot transfer of a physics-based radar simulator],
  doc-kind: "Technical Report",
  organization: "AirLab Radar Signal Processing Group",
  date: "September 2026",
  // The report template wants a flat (name, affiliation) author list, which
  // is a THIRD author shape again — mapped here rather than in the content.
  authors: authors.map(a => (
    name: a.name,
    affiliation: affiliations.at(a.affil-keys.first()).institution,
  )),
  summary: abstract,
  toc: true,
  bib: bibliography("references.bib"),
)

#key-findings[
  + A differentiable physics prior plus a learned residual transfers a radar
    simulator to a new scene from as few as five measured frames.
  + The range--Doppler consistency loss is what stops the drift that
    unconstrained generative baselines show.
  + $Delta theta$ is the interpretable part: when it grows, the scenario is
    outside the prior's validity and the operator can see that.

]

#callout(kind: "info", title: [How to read this report])[
  This document is generated from the same `content/` tree as the conference
  versions in `main-neurips.typ`, `main-icml.typ` and friends. If you change
  the prose there, this report changes too — nothing is duplicated.
]

#introduction()
#related-work()
#method()
#experiments()
#conclusion()

#callout(kind: "warn", title: [Placeholder numbers])[
  Every quantitative value in this example is illustrative. `@tbl:results` in
  particular is a formatting demonstration, not a measurement.
]
