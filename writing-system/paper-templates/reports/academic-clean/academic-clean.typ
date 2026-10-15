// ---------------------------------------------------------------------------
//  academic-clean.typ — restrained academic report template
//
//  AUTHORSHIP: original work for this template library. Not derived from any
//  conference or publisher template, and not submission material for a venue.
//
//  Intended use: formal research reports, literature surveys, paper drafts
//  that are not yet aimed at a specific venue.
//
//  Design intent: black / grey only, no colour fills at all. Everything is
//  carried by type size, weight and horizontal rules — so it prints cleanly
//  on a mono laser printer and photocopies without turning to mud.
// ---------------------------------------------------------------------------

#let ink = rgb("#000000")
#let muted = rgb("#3d3d3d")
#let faint = rgb("#6b6b6b")
#let rule = rgb("#9a9a9a")
#let hair = rgb("#c4c4c4")

#let serif = ("New Computer Modern", "Libertinus Serif", "TeX Gyre Termes")
#let sans = ("Noto Sans", "Libertinus Sans", "TeX Gyre Heros", "DejaVu Sans")
#let mono = ("DejaVu Sans Mono", "TeX Gyre Cursor")

// A note that survives greyscale printing: rule on the left, no fill.
#let note(title: "Note", body) = {
  block(width: 100%, breakable: false)[
    #rect(width: 100%, stroke: (left: 1.6pt + faint), inset: (x: 0.9em, y: 0.15em))[
      #set text(size: 9.5pt)
      #set par(justify: true, leading: 0.62em)
      #block(below: 0.25em)[#text(weight: "bold", size: 9pt)[#title]]
      #body
    ]
  ]
  v(0.5em)
}

#let abstract-block(body) = {
  block(width: 100%, above: 0.4em, below: 0.9em)[
    #set text(size: 9.5pt)
    #set par(justify: true, leading: 0.62em, first-line-indent: 0em)
    #block(below: 0.35em)[#text(weight: "bold", size: 10pt)[Abstract]]
    #block(inset: (left: 1.6em, right: 1.6em))[#body]
  ]
}

#let report(
  title: [],
  subtitle: none,
  authors: (),
  date: none,
  organization: none,
  doc-kind: "Research Report",
  abstract: none,
  toc: true,
  numbering: "1",
  bib: none,
  body,
) = {
  set document(title: title, author: authors.map(a => a.name))

  set page(
    paper: "a4",
    margin: (x: 2.5cm, top: 2.6cm, bottom: 2.6cm),
    numbering: numbering,
    number-align: center,
    header: context {
      let pg = counter(page).get().first()
      if pg > 1 {
        set text(font: serif, size: 8.5pt, fill: faint)
        line(length: 100%, stroke: 0.4pt + hair)
        v(-0.85em)
        grid(
          columns: (1fr, auto),
          align: (left, right),
          [#doc-kind],
          [#pg],
        )
      }
    },
  )

  set text(font: serif, size: 10.5pt, fill: ink, lang: "en")
  set par(justify: true, leading: 0.7em, spacing: 0.85em)

  // Number equations: a report that cross-references one needs numbers.
  set math.equation(numbering: "(1)")

  set heading(numbering: "1.1")
  show heading: it => {
    let lvl = it.level
    if lvl == 1 {
      block(above: 1.5em, below: 0.7em, sticky: true)[
        #set text(font: serif, size: 14pt, weight: "bold")
        #it.body
      ]
    } else if lvl == 2 {
      block(above: 1.2em, below: 0.55em, sticky: true)[
        #set text(font: serif, size: 11.5pt, weight: "bold")
        #it.body
      ]
    } else {
      block(above: 1em, below: 0.45em, sticky: true)[
        #set text(font: serif, size: 10.5pt, weight: "bold", style: "italic")
        #it.body
      ]
    }
  }
  // Section numbers in the margin-style academic layout: number, then text.
  show heading.where(level: 1): it => block(above: 1.5em, below: 0.7em, sticky: true)[
    #set text(font: serif, size: 14pt, weight: "bold")
    #counter(heading).display("1.")
    #h(0.6em)
    #it.body
  ]
  show heading.where(level: 2): it => block(above: 1.2em, below: 0.55em, sticky: true)[
    #set text(font: serif, size: 11.5pt, weight: "bold")
    #counter(heading).display("1.1")
    #h(0.55em)
    #it.body
  ]
  show heading.where(level: 3): it => block(above: 1em, below: 0.45em, sticky: true)[
    #set text(font: serif, size: 10.5pt, weight: "bold", style: "italic")
    #counter(heading).display("1.1.1")
    #h(0.5em)
    #it.body
  ]

  // -------------------------------------------------------------- code
  show raw: set text(font: mono, size: 8.5pt)
  show raw.where(block: true): it => block(
    width: 100%,
    inset: (x: 0.7em, y: 0.6em),
    stroke: 0.4pt + hair,
    it,
  )

  // ------------------------------------------------------------ tables
  set table(stroke: none, inset: (x: 0.55em, y: 0.4em), align: horizon)
  show table: it => block(above: 0.5em, below: 0.5em, it)
  show table.cell.where(y: 0): set text(weight: "bold", size: 9.5pt)
  show table.cell: set text(size: 9.5pt)

  // ----------------------------------------------------------- figures
  show figure.caption: set text(size: 9pt, fill: muted)
  show figure.caption: it => block(width: 94%)[
    #set align(left)
    #it
  ]

  set list(indent: 1.15em, body-indent: 0.6em)
  set enum(indent: 1.15em, body-indent: 0.6em)

  // ========================================================= title block
  block(width: 100%)[
    #set align(left)
    #set par(justify: false)
    #text(size: 8.5pt, fill: faint, upper(doc-kind))
    #v(0.7em)
    #block[
      #set text(size: 19pt, weight: "bold")
      #set par(leading: 1.14em)
      #title
    ]
    #if subtitle != none [
      #v(0.4em)
      #block[
        #set text(size: 12pt, style: "italic", fill: muted)
        #set par(leading: 1.2em)
        #subtitle
      ]
    ]
    #v(0.8em)
    #line(length: 100%, stroke: 1pt + ink)
    #v(0.5em)
    #set text(size: 10pt, fill: muted)
    #grid(
      columns: (1fr, auto),
      align: (left, right),
      {
        set par(justify: false)
        if authors.len() > 0 [
          #authors.map(a => {
            let aff = a.at("affiliation", default: none)
            if aff == none { a.name } else { [#a.name\ #text(size: 9pt, fill: faint, style: "italic")[#aff]] }
          }).join([ #h(1.2em) ])
        ]
      },
      {
        set align(right)
        [#organization #if date != none [\ #date]]
      },
    )
    #v(0.3em)
  ]

  if abstract != none { abstract-block(abstract) }

  if toc {
    show outline.entry.where(level: 1): it => { v(0.3em, weak: true); strong(it) }
    block(above: 1.1em, below: 0.9em)[
      #set text(size: 12pt, weight: "bold")
      #block(below: 0.5em)[Contents]
      #set text(size: 9.5pt)
      #outline(title: none, depth: 2, indent: 1em)
    ]
    pagebreak(weak: true)
  }

  body

  if bib != none {
    show bibliography: set heading(numbering: none)
    set heading(outlined: false)
    bib
  }
}
