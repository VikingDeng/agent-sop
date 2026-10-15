// ===========================================================================
//  main-iclr.typ — the shared body rendered in the ICLR style.
//
//  Compile:  typst compile main-iclr.typ
//
//  Template: @local/clear-iclr 0.7.1 — vendored from
//  https://github.com/daskol/typst-templates and PATCHED (see
//  ../../typst/iclr/PATCHES.md). COMMUNITY template, MIT, by Daniel Bershatsky.
//  NOT an official ICLR template.
// ===========================================================================

#import "@local/clear-iclr:0.7.1": iclr2026

// ---- shared metadata and body (venue-agnostic) ----------------------------
#import "content/_meta.typ": title, keywords, abstract
#import "content/_adapt.typ": as-pairs
#import "content/introduction.typ": introduction
#import "content/related-work.typ": related-work
#import "content/method.typ": method
#import "content/experiments.typ": experiments
#import "content/conclusion.typ": conclusion

#show: iclr2026.with(
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
