// ===========================================================================
//  main-cvpr.typ — the shared body rendered in the CVPR style.
//
//  Compile:  typst compile main-cvpr.typ
//
//  Template: @preview/blind-cvpr 0.7.0 (COMMUNITY, MIT, by Daniel Bershatsky)
//  NOT an official CVPR template.
// ===========================================================================

#import "@preview/blind-cvpr:0.7.0": cvpr2025

// ---- shared metadata and body (venue-agnostic) ----------------------------
#import "content/_meta.typ": title, keywords, abstract
#import "content/_adapt.typ": as-pairs
#import "content/introduction.typ": introduction
#import "content/related-work.typ": related-work
#import "content/method.typ": method
#import "content/experiments.typ": experiments
#import "content/conclusion.typ": conclusion

#show: cvpr2025.with(
  title: title,
  authors: as-pairs(),
  keywords: keywords,
  abstract: abstract,
  bibliography: bibliography("references.bib"),
)

#introduction()
#related-work()
#method()
#experiments()
#conclusion()
