// ===========================================================================
//  main-acl.typ — the shared body rendered in the *ACL style (tracl).
//
//  Compile:  typst compile main-acl.typ
//
//  Template: @preview/tracl 0.8.1 — maintained by the Computational
//  Linguistics group at Saarland University (github.com/coli-saar/tracl),
//  Apache-2.0. Community template; ACL does not ship a Typst template.
//
//  Two ACL-specific differences from the other entry files:
//    1. the API is a `#show: doc => acl(doc, ...)` wrapper, not `.with(...)`;
//    2. the bibliography is registered imperatively — `add-bib-resource` must
//       run BEFORE the citations are resolved and `print-acl-bibliography()`
//       decides where the reference list lands.
// ===========================================================================

// Two imports are needed: tracl ships the *ACL look, but the bibliography
// plumbing (`add-bib-resource`) lives in pergamon, which tracl builds on.
#import "@preview/tracl:0.8.1": *
#import "@preview/pergamon:0.7.1": add-bib-resource, cite

// NOTE: `abstract` is aliased because tracl exports a function of that name
// too. Without the alias this import would shadow (or be shadowed by) it.
#import "content/_meta.typ": title, keywords, abstract as abstract-body
#import "content/_adapt.typ": as-acl-authors

#import "content/introduction.typ": introduction
#import "content/related-work.typ": related-work
#import "content/method.typ": method
#import "content/experiments.typ": experiments
#import "content/conclusion.typ": conclusion

// Register the bibliography BEFORE any citation is resolved.
#add-bib-resource(read("references.bib"))

// ---- CITATION SHIM --------------------------------------------------------
// pergamon does not use Typst's native `@key` citation syntax; it has its own
// `cite("key")` function. Rather than rewriting every `@key` in content/ for
// this one venue, translate them here.
//
// The translation is safe because of a naming convention the content obeys:
// internal cross-references always carry a typed prefix (`fig:`, `tbl:`,
// `sec:`, `eq:`), whereas bibliography keys never contain a colon. So any ref
// WITHOUT a colon is a citation.
#show ref: it => {
  let target = str(it.target)
  if target.contains(":") { it } else { cite(target) }
}

// ---- EQUATION NUMBERING ---------------------------------------------------
// The *ACL style does not number equations by default, but the shared body
// cross-references one (@eq:rdloss). Rather than deleting the reference from
// the content — which would weaken every other venue's version — turn
// numbering on for this venue. This is a venue capability difference, and the
// adapter is the right place to absorb it.
#set math.equation(numbering: "(1)")

#show: doc => acl(
  doc,
  anonymous: false,
  title: title,
  authors: make-authors(..as-acl-authors()),
)

#abstract[#abstract-body]

#introduction()
#related-work()
#method()
#experiments()
#conclusion()

#print-acl-bibliography()
