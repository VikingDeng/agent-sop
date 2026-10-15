// ===========================================================================
//  main-neurips.typ — the shared body rendered in the NeurIPS style.
//
//  Compile:  typst compile main-neurips.typ
//
//  Template: @preview/bloated-neurips 0.8.0 (COMMUNITY, MIT, by Daniel Bershatsky)
//  NOT an official NeurIPS template. See TEMPLATE_CATALOG.md.
//
//  Everything below the `#show` rule is a call into content/ — there is no
//  prose in this file, on purpose. Compare with main-icml.typ: the body is
//  identical, only the adapter differs.
// ===========================================================================

#import "@preview/bloated-neurips:0.8.0": neurips2026

// ---- shared metadata and body (venue-agnostic) ----------------------------
#import "content/_meta.typ": title, keywords, abstract
#import "content/_adapt.typ": as-pairs
#import "content/introduction.typ": introduction
#import "content/related-work.typ": related-work
#import "content/method.typ": method
#import "content/experiments.typ": experiments
#import "content/conclusion.typ": conclusion

#show: neurips2026.with(
  title: title,
  authors: as-pairs(),
  keywords: keywords,
  abstract: abstract,
  bibliography: bibliography("references.bib"),
  accepted: false, // false => anonymous submission mode
)

#introduction()
#related-work()
#method()
#experiments()
#conclusion()
