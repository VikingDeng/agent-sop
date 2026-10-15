// ---------------------------------------------------------------------------
//  modern-technical.typ — technical report / whitepaper template
//
//  AUTHORSHIP: original work for this template library. Not derived from any
//  conference or publisher template, and not submission material for a venue.
//
//  Intended use: AI / Agent / Radar / AI4Science technical reports, design
//  documents, literature surveys, internal whitepapers. This is the library's
//  default entry for an engineering / technical document (doc-kind=工程技术文档).
//
//  Language, fonts and labels are template parameters (`lang`, `font`,
//  `heading-font`, `toc-title`). `lang: "zh"` alone selects the CJK-first font
//  stack and the Chinese label defaults: Typst's automatic fallback picks
//  Japanese CJK fonts and mixed families, which is wrong for Simplified
//  Chinese, so the choice is made HERE (in lang-defaults) rather than in the
//  caller's main.typ. `lang: "en"` (the default) keeps the original stacks and
//  labels, and an explicit `font` / `heading-font` / `toc-title` still wins.
//
//  Body conventions wired by the starter:
//    * semantic cite + bibliography: superscript [1] in the prose, baseline
//      [1] in the bibliography; no hand-written numbers, no regex rewriting.
//    * table captions above the table, figure captions below the image.
//
//  Design intent: modern but restrained. Sans headings over a serif body,
//  a single accent colour used only for structure (never for large fills),
//  and callout boxes that earn their place. It should look like a well-made
//  whitepaper, not a slide deck.
// ---------------------------------------------------------------------------

#let ink = rgb("#16181d")
#let muted = rgb("#5b6270")
#let faint = rgb("#8a9099")
#let rule = rgb("#d8dce2")
#let accent = rgb("#1f4e79")
#let surface = rgb("#f4f6f9")
#let surface-warm = rgb("#fdf6e8")
#let surface-alert = rgb("#fdeceb")
#let surface-ok = rgb("#eaf5ee")

// CJK families are appended (never prepended) to the Latin stacks: Latin text
// keeps its current font, and CJK text in a callout or caption no longer falls
// back to whatever CJK font the system happens to list first.
#let cjk-sans = ("Noto Sans CJK SC", "Source Han Sans SC")
#let cjk-serif = ("Noto Serif CJK SC", "Source Han Serif SC")

#let sans = ("Noto Sans", "Libertinus Sans", "TeX Gyre Heros", "DejaVu Sans", ..cjk-sans)
#let serif = ("New Computer Modern", "Libertinus Serif", "TeX Gyre Termes", ..cjk-serif)
#let mono = ("DejaVu Sans Mono", "TeX Gyre Cursor")

// Language-dependent defaults. They live in the template, so a project only
// passes `lang` (from meta.typ) and never repeats font stacks or labels.
// "zh", "zh-Hans", "zh-CN" ... all take the Chinese branch; anything else
// keeps the English defaults above, i.e. the pre-0.2.0 look is unchanged.
#let lang-defaults(lang) = if lang.starts-with("zh") {
  (
    body-font: ("Noto Serif CJK SC", "Source Han Serif SC", "New Computer Modern", "Libertinus Serif"),
    head-font: ("Noto Sans CJK SC", "Source Han Sans SC", "Noto Sans", "DejaVu Sans"),
    toc-title: "目录",
  )
} else {
  (body-font: serif, head-font: sans, toc-title: "Contents")
}

// ---------------------------------------------------------------------------
//  Callouts
// ---------------------------------------------------------------------------
#let callout-colors = (
  info:  (bg: surface,        bar: accent,         label: "Note"),
  tip:   (bg: surface-ok,     bar: rgb("#2f7d4f"), label: "Tip"),
  warn:  (bg: surface-warm,   bar: rgb("#b8860b"), label: "Caution"),
  alert: (bg: surface-alert,  bar: rgb("#b3261e"), label: "Important"),
  key:   (bg: rgb("#eef3f9"), bar: accent,         label: "Key"),
)

#let callout(kind: "info", title: none, label: none, body) = {
  let c = callout-colors.at(kind, default: callout-colors.info)
  // `label` overrides the built-in English label (NOTE / TIP / ...) so a
  // non-English document does not have to patch the template.
  let lbl = if label == none { c.label } else { label }
  block(
    width: 100%,
    breakable: false,
    inset: (left: 0pt, right: 0pt, top: 0pt, bottom: 0pt),
  )[
    // The accent bar is a LEFT STROKE, not a placed rectangle.
    // `place(...)[rect(height: 100%)]` resolves the percentage against the
    // PAGE, not against this box, so the bar runs to the bottom of the page.
    #rect(
      width: 100%,
      fill: c.bg,
      stroke: (left: 3pt + c.bar),
      inset: (x: 0.85em, y: 0.7em),
    )[
      #set text(font: sans, size: 9.5pt)
      #set par(justify: true, leading: 0.6em)
      #block(below: 0.35em)[
        #text(weight: "bold", fill: c.bar, size: 8.5pt, upper(lbl))
        // Skip a title that merely repeats the label (see the Chinese template
        // for the same guard). Content != string in Typst, hence the repr dance.
        #if title != none and repr(title) != "[" + lbl + "]" [
          #h(0.6em) #text(weight: "bold", fill: ink)[#title]
        ]
      ]
      #body
    ]
  ]
  v(0.55em)
}

// Key Findings — the one box that should be skimmable in ten seconds.
#let key-findings(items, title: "Key Findings") = {
  block(width: 100%, breakable: false)[
    #rect(
      width: 100%,
      fill: rgb("#eef3f9"),
      stroke: (left: 3pt + accent),
      inset: (x: 0.95em, y: 0.8em),
    )[
      #set text(font: sans, size: 10pt)
      #block(below: 0.5em)[
        #text(weight: "bold", size: 10.5pt, fill: accent)[#title]
      ]
      #set enum(indent: 1.1em, tight: false)
      #set enum(numbering: n => text(fill: accent, weight: "bold")[#n.])
      #items
    ]
  ]
  v(0.7em)
}

// ---------------------------------------------------------------------------
//  Main entry point
// ---------------------------------------------------------------------------
#let report(
  title: [],
  subtitle: none,
  authors: (),
  date: none,
  organization: none,
  doc-kind: "Technical Report",
  summary: none,
  // Backward-compatible language/font switches; defaults keep the 0.1.0 look
  // when `lang` is "en", and pick the Chinese stack/labels when it is "zh".
  lang: "en",
  font: none,
  heading-font: none,
  // Section label above the table of contents. `none` = derive from `lang`
  // ("目录" for zh, "Contents" for en); an explicit value always wins.
  toc-title: none,
  toc: true,
  numbering: "1",
  bib: none,
  body,
) = {
  set document(title: title, author: authors.map(a => a.name))

  let lang-default = lang-defaults(lang)
  let body-font = if font == none { lang-default.body-font } else { font }
  let head-font = if heading-font == none { lang-default.head-font } else { heading-font }
  let toc-label = if toc-title == none { lang-default.toc-title } else { toc-title }

  set page(
    paper: "a4",
    margin: (x: 2.4cm, top: 2.9cm, bottom: 2.7cm),
    numbering: numbering,
    number-align: center,
    header: context {
      let pg = counter(page).get().first()
      if pg > 1 {
        set text(font: head-font, size: 8.5pt, fill: faint)
        grid(
          columns: (1fr, auto),
          align: (left, right),
          [#doc-kind],
          [#title],
        )
        v(-0.75em)
        line(length: 100%, stroke: 0.5pt + rule)
      }
    },
    footer: context {
      let pg = counter(page).get().first()
      if pg > 1 {
        set text(font: head-font, size: 8.5pt, fill: faint)
        line(length: 100%, stroke: 0.5pt + rule)
        v(-0.9em)
        grid(
          columns: (1fr, auto),
          align: (left, right),
          [#organization],
          [#pg],
        )
      }
    },
  )

  set text(font: body-font, size: 10.5pt, fill: ink, lang: lang)
  set par(justify: true, leading: 0.72em, spacing: 1em)

  // Number equations: a report that cross-references one needs numbers.
  set math.equation(numbering: "(1)")

  set heading(numbering: "1.1")
  show heading: it => {
    let lvl = it.level
    // Unnumbered headings (the bibliography, `numbering: none`) must not print
    // the counter: this show rule builds the number by hand, so it has to check
    // for itself — otherwise the bibliography reads "4.1. References".
    let numbered = it.numbering != none
    if lvl == 1 {
      block(above: 1.7em, below: 0.8em, sticky: true)[
        #set text(font: head-font, size: 15pt, weight: "bold", fill: ink)
        #if numbered [
          #counter(heading).display("1.")
          #h(0.55em)
        ]
        #it.body
      ]
    } else if lvl == 2 {
      block(above: 1.35em, below: 0.6em, sticky: true)[
        #set text(font: head-font, size: 12pt, weight: "bold", fill: accent)
        #if numbered [
          #counter(heading).display("1.1")
          #h(0.5em)
        ]
        #it.body
      ]
    } else {
      block(above: 1.1em, below: 0.5em, sticky: true)[
        #set text(font: head-font, size: 10.5pt, weight: "bold", fill: muted)
        #if numbered [
          #counter(heading).display("1.1.1")
          #h(0.5em)
        ]
        #it.body
      ]
    }
  }

  // ------------------------------------------------------------ code
  show raw: set text(font: mono, size: 8.5pt)
  show raw.where(block: true): it => block(
    width: 100%,
    fill: surface,
    inset: 0.8em,
    radius: 2pt,
    stroke: 0.5pt + rule,
    it,
  )

  // ---------------------------------------------------------- tables
  set table(
    stroke: none,
    inset: (x: 0.6em, y: 0.42em),
    align: horizon,
  )
  show table: it => block(above: 0.6em, below: 0.6em, it)
  show table.cell.where(y: 0): set text(font: head-font, weight: "bold", size: 9.5pt)
  show table.cell: set text(size: 9.5pt)

  // --------------------------------------------------------- figures
  set figure(gap: 0.7em)
  // Internal default: table caption above the table, figure caption below.
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: image): set figure.caption(position: bottom)
  show figure.caption: set text(font: head-font, size: 9pt, fill: muted)
  show figure.caption: it => block(width: 96%)[
    #set align(left)
    #it
  ]

  // Citations: superscript numbers in the prose, baseline entries in the
  // bibliography. Only the normal form (@key / #cite(<key>)) gets `super`;
  // narrative forms — #cite(form: "prose" / "full" / "author" / "year") — keep
  // their own semantics and baseline, because superscripting a whole phrase
  // breaks the sentence. `super` is applied once (nesting #text(size: ...)
  // inside it would shrink the label twice). Cross-references are not `cite`
  // elements, so @fig: / @tbl: / @eq: keep their normal inline rendering.
  show cite: it => if it.form == "normal" { super(it) } else { it }

  // ------------------------------------------------------------ lists
  set list(indent: 1.15em, body-indent: 0.65em)
  set enum(indent: 1.15em, body-indent: 0.65em)
  show list.item: it => { set par(justify: true, leading: 0.66em); it }

  // =========================================================== title block
  block(width: 100%)[
    #set align(left)
    #set par(justify: false)
    #text(font: head-font, size: 8.5pt, weight: "bold", fill: accent, upper(doc-kind))
    #v(0.5em)
    #block[
      #set text(font: head-font, size: 24pt, weight: "bold", fill: ink)
      #set par(leading: 1.12em)
      #title
    ]
    #if subtitle != none [
      #v(0.35em)
      #block[
        #set text(font: head-font, size: 13pt, fill: muted)
        #set par(leading: 1.2em)
        #subtitle
      ]
    ]
    #v(0.9em)
    #line(length: 100%, stroke: 1.4pt + accent)
    #v(0.55em)
    #set text(font: head-font, size: 9.5pt, fill: muted)
    #grid(
      columns: (1fr, auto),
      align: (left, right),
      {
        set par(justify: false)
        if authors.len() > 0 [
          #authors.map(a => {
            let aff = a.at("affiliation", default: none)
            if aff == none { a.name } else { [#a.name\ #text(size: 8.5pt, fill: faint)[#aff]] }
          }).join([ #h(1.2em) ])
        ]
      },
      {
        set align(right)
        [#organization #if date != none [\ #date]]
      },
    )
    #v(0.4em)
  ]

  // --------------------------------------------------------------- summary
  if summary != none {
    block(width: 100%)[
      #set text(font: body-font, size: 10pt)
      #set par(justify: true, leading: 0.68em)
      #rect(width: 100%, fill: surface, stroke: none, inset: 0.9em)[#summary]
    ]
    v(0.6em)
  }

  // ------------------------------------------------------------------ toc
  if toc {
    show outline.entry.where(level: 1): it => {
      v(0.35em, weak: true)
      strong(it)
    }
    block(above: 1.2em, below: 1em)[
      #set text(font: head-font, size: 12pt, weight: "bold")
      #block(below: 0.6em)[#toc-label]
      #show outline: set text(font: head-font, size: 9.5pt)
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
