// ===========================================================================
//  main-ieee.typ — the shared body rendered in IEEE style.
//
//  Compile:  typst compile main-ieee.typ
//
//  Template: @preview/charged-ieee 0.1.4 — published by the Typst project
//  itself (github.com/typst/templates), MIT-0. This is the closest thing to a
//  maintained "IEEE-style" Typst template, but it is still NOT an IEEE
//  template and IEEE does not accept it. See TEMPLATE_CATALOG.md.
//
//  Note the adapter difference: charged-ieee wants a FLAT author list with one
//  organisation per author, whereas the daskol family wants a
//  (authors, affiliations) pair — hence `as-flat-authors` instead of
//  `as-pairs`. Same content, different adapter. That is the whole design.
// ===========================================================================

#import "@preview/charged-ieee:0.1.4": ieee

// ---- shared metadata and body (venue-agnostic) ----------------------------
#import "content/_meta.typ": title, abstract, keywords
#import "content/_adapt.typ": as-flat-authors
#import "content/introduction.typ": introduction
#import "content/related-work.typ": related-work
#import "content/method.typ": method
#import "content/experiments.typ": experiments
#import "content/conclusion.typ": conclusion

#show: ieee.with(
  title: title,
  authors: as-flat-authors(),
  abstract: abstract,
  index-terms: keywords,
  bibliography: bibliography("references.bib"),
  figure-supplement: [Fig.],
)

#introduction()
#related-work()
#method()
#experiments()
#conclusion()
