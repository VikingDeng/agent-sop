// ---------------------------------------------------------------------------
//  _meta.typ — venue-agnostic paper metadata
//
//  This is the SINGLE source of truth for title, authors, affiliations,
//  keywords and the abstract. Every `main-<venue>.typ` entry file imports
//  these values and maps them into the shape its template expects.
//
//  Because author-block APIs differ wildly between venue templates, the
//  author list below is stored in a NEUTRAL schema and adapted per venue
//  in the entry files. That is the whole point of the separation.
// ---------------------------------------------------------------------------

#let title = [Few-Shot Multi-Scenario High-Fidelity Radar Simulation]

#let short-title = [Few-Shot Radar Simulation]

// Neutral author schema. Adapt, do not duplicate:
//   name        — display name
//   email       — contact address
//   affil-keys  — keys into `affiliations`
//   equal       — equal-contribution flag
//   corresponding — corresponding-author flag
#let authors = (
  (
    name: "First Author",
    email: "first.author@example.edu",
    affil-keys: ("beihang",),
    equal: true,
    corresponding: true,
  ),
  (
    name: "Second Author",
    email: "second.author@example.edu",
    affil-keys: ("beihang", "airlab"),
    equal: true,
    corresponding: false,
  ),
  (
    name: "Third Author",
    email: "third.author@example.edu",
    affil-keys: ("airlab",),
    equal: false,
    corresponding: false,
  ),
)

// Structured affiliations. Order here drives numbering in the venues that
// auto-number affiliations.
#let affiliations = (
  beihang: (
    institution: "Beihang University",
    department: "School of Computer Science and Engineering",
    location: "Beijing",
    country: "China",
  ),
  airlab: (
    institution: "AirLab Radar Signal Processing Group",
    department: "Department of Electronic Engineering",
    location: "Beijing",
    country: "China",
  ),
)

#let keywords = (
  "radar simulation",
  "few-shot learning",
  "diffusion models",
  "physics-informed learning",
  "AI4Science",
)

// The abstract body lives with the other content, but is re-exported here
// so venue entry files can grab everything from one import.
#import "abstract.typ": abstract
