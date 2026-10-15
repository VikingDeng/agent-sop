// ---------------------------------------------------------------------------
//  _adapt.typ — venue adaptation layer
//
//  THE POINT OF THIS FILE
//  ----------------------
//  The venue templates do not share an author-block API:
//
//    * daskol/typst-templates family (NeurIPS, ICML, ICLR, CVPR)
//        authors: (author-array, affiliation-dict)
//    * Typst official `charged-ieee`
//        authors: ( (name:, department:, organization:, location:, email:), ... )
//    * `tracl` (ACL)
//        authors: make-authors( (name:, affiliation: content), ... )
//
//  So instead of duplicating the metadata into each entry file, every
//  adaptation lives here, in one place, next to the neutral schema it adapts
//  FROM. If a template changes its API, you fix one function here and every
//  entry file that uses it keeps working.
// ---------------------------------------------------------------------------

#import "_meta.typ": authors, affiliations

// ---------------------------------------------------------------------------
//  Format A — daskol/typst-templates family, and the Typst official
//  `charged-ieee`-style pair form:  (authors, affls)
// ---------------------------------------------------------------------------
#let as-pairs() = (
  authors.map(a => (
    name: a.name,
    affl: a.affil-keys,
    email: a.email,
    equal: a.equal,
  )),
  // The templates accept either a plain array or a structured dictionary per
  // affiliation; our neutral schema is already in the structured form.
  affiliations,
)

// ---------------------------------------------------------------------------
//  Format B — flat author list (Typst official `charged-ieee`)
//  IEEE style wants ONE entry per author carrying a single organisation.
// ---------------------------------------------------------------------------
#let as-flat-authors() = authors.map(a => {
  let a0 = affiliations.at(a.affil-keys.first())
  (
    name: a.name,
    department: a0.department,
    organization: a0.institution,
    location: a0.location + ", " + a0.country,
    email: a.email,
  )
})

// ---------------------------------------------------------------------------
//  Format C — tracl / ACL
//  Each author carries a content block for the affiliation footnote.
// ---------------------------------------------------------------------------
#let as-acl-authors() = authors.map(a => (
  name: a.name,
  affiliation: {
    let lines = a.affil-keys.map(k => affiliations.at(k))
    lines.map(l => [#l.institution\ #l.location]).join()
    // Plain text, not a helper like `email(...)`: this module has its own
    // import scope, so it cannot rely on anything the ENTRY FILE imported
    // from its venue template.
    [#a.email]
  },
))
