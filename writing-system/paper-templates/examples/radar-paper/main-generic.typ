// ===========================================================================
//  main-generic.typ — the shared body in the library's own generic template.
//
//  Compile:  typst compile main-generic.typ
//
//  Template: @local/generic-paper 0.1.0 — original work in this library
//  (../../typst/generic/generic.typ). Not a venue template; the "no decision
//  made yet" default. Because it lives in the library, edit it once and every
//  project that uses it picks the change up after re-running
//  ../../scripts/install-local-typst-packages.sh.
//
//  Note this entry needs no adapter at all: generic-paper was written against
//  the same neutral author schema that content/_meta.typ uses.
// ===========================================================================

#import "@local/generic-paper:0.1.0": generic-paper

// ---- shared metadata and body (venue-agnostic) ----------------------------
#import "content/_meta.typ": title, authors, affiliations, keywords, abstract
#import "content/introduction.typ": introduction
#import "content/related-work.typ": related-work
#import "content/method.typ": method
#import "content/experiments.typ": experiments
#import "content/conclusion.typ": conclusion

#show: generic-paper.with(
  title: title,
  authors: authors,
  affiliations: affiliations,
  keywords: keywords,
  abstract: abstract,
  bib: bibliography("references.bib"),
)

#introduction()
#related-work()
#method()
#experiments()
#conclusion()
