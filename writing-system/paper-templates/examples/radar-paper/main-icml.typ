// ===========================================================================
//  main-icml.typ — the shared body rendered in the ICML style.
//
//  Compile:  typst compile main-icml.typ
//
//  Template: @local/lucky-icml 0.7.1 — vendored from
//  https://github.com/daskol/typst-templates and PATCHED (see
//  ../../typst/icml/PATCHES.md). COMMUNITY template, MIT, by Daniel Bershatsky.
//  NOT an official ICML template.
//
//  The upstream @preview/lucky-icml 0.7.0 does NOT compile on Typst 0.15;
//  that is the only reason a local copy exists. Re-run
//  ../../scripts/install-local-typst-packages.sh after editing it.
// ===========================================================================

#import "@local/lucky-icml:0.7.1": icml2025

// ---- shared metadata and body (venue-agnostic) ----------------------------
#import "content/_meta.typ": title, keywords, abstract, short-title
#import "content/_adapt.typ": as-pairs
#import "content/introduction.typ": introduction
#import "content/related-work.typ": related-work
#import "content/method.typ": method
#import "content/experiments.typ": experiments
#import "content/conclusion.typ": conclusion

#show: icml2025.with(
  title: title,
  authors: as-pairs(),
  keywords: keywords,
  abstract: abstract,
  bibliography: bibliography("references.bib"),
  header: short-title,
  accepted: false, // false => anonymous submission mode
)

#introduction()
#related-work()
#method()
#experiments()
#conclusion()
