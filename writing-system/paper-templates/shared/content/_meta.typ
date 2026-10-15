// ---------------------------------------------------------------------------
//  _meta.typ — single source of truth for title, authors, affiliations,
//  keywords and the abstract.
//
//  Author entries use a NEUTRAL schema; each venue entry file maps it into
//  whatever shape that venue's template wants (see _adapt.typ).
//    name          — display name
//    email         — contact address
//    affil-keys    — keys into `affiliations`
//    equal         — equal-contribution flag (rendered as a star)
// ---------------------------------------------------------------------------

#let title = [Your Paper Title Goes Here]

#let short-title = [Short Running Title]

#let authors = (
  (
    name: "First Author",
    email: "first@example.edu",
    affil-keys: ("primary",),
    equal: true,
  ),
)

#let affiliations = (
  primary: (
    institution: "Your University",
    department: "Your Department",
    location: "City",
    country: "Country",
  ),
)

#let keywords = ("keyword one", "keyword two", "keyword three")

#import "abstract.typ": abstract
