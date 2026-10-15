// ---------------------------------------------------------------------------
//  generic.typ — a clean, single-column academic paper template
//
//  AUTHORSHIP: original work for this template library (not derived from any
//  conference template). Copyright (c) 2026 Local template library, MIT.
//  Free to modify without attribution constraints.
//
//  Purpose: the "no submission target decided yet" default. Single column,
//  generous leading, restrained headings — the layout that is easiest to
//  *write* in. This is the library's default entry for a paper draft
//  (template id generic-typst / package name generic-paper).
//
//  When a target is chosen, the PROSE can be reused, but nothing is converted
//  automatically: the look, the citation syntax and the engine all have to be
//  checked again. A Typst body is not a LaTeX body (`= heading`, `#figure`,
//  `$math$` must be rewritten by hand), and page breaks, line breaks and font
//  embedding change with any template switch. Assemble the submission against
//  the target's current-year official requirements.
//
//  This is NOT an official template for any venue and is not submission
//  material for anything. See TEMPLATE_CATALOG.md.
//
//  Two ways to use it:
//    * library demo:  examples/radar-paper/main-generic.typ (imports the
//      @local package; the body is shared with the venue entries)
//    * layered draft: typst/generic/starter/ — scripts/new_typst_paper.{sh,ps1}
//      generates main.typ + meta.typ + content/ + a frozen vendor/template/
//      snapshot + template.lock. No @local/@preview, no network.
//
//  Body conventions wired by the starter: semantic cite + bibliography
//  (superscript [1] in the prose, baseline [1] in the bibliography), table
//  captions above, figure captions below.
// ---------------------------------------------------------------------------

#let default-font = ("New Computer Modern", "Libertinus Serif")

// Language-dependent defaults, kept in the template: a Chinese draft passes
// `lang` (from meta.typ) and gets the CJK-first stack plus the Chinese labels,
// without repeating font or label constants in main.typ. English (the default)
// keeps the pre-0.2.0 stack and labels. "zh", "zh-Hans", "zh-CN" ... all take
// the Chinese branch.
#let lang-defaults(lang) = if lang.starts-with("zh") {
  (
    font: ("Noto Serif CJK SC", "Source Han Serif SC", "New Computer Modern", "Libertinus Serif"),
    abstract-label: "摘要",
    keywords-label: "关键词",
  )
} else {
  (font: default-font, abstract-label: "Abstract", keywords-label: "Keywords")
}

#let generic-paper(
  title: [],
  authors: (),
  affiliations: (:),
  keywords: (),
  abstract: [],
  // Language of the text. "zh" switches Typst's CJK line breaking and its
  // built-in label localisation (bibliography heading, 图/表 prefixes), and
  // selects the Chinese font stack and label defaults below.
  lang: "en",
  // Optional font list. `none` = derive from `lang` (CJK-first for zh, the
  // bundled-font default above for everything else). An explicit list wins.
  font: none,
  // Labels are derived from `lang` by default ("摘要"/"关键词" for zh,
  // "Abstract"/"Keywords" otherwise) so a non-English draft does not patch the
  // template; an explicit value always wins.
  abstract-label: none,
  keywords-label: none,
  bib: none,
  body,
) = {
  let lang-default = lang-defaults(lang)
  let body-font = if font == none { lang-default.font } else { font }
  let abs-label = if abstract-label == none { lang-default.abstract-label } else { abstract-label }
  let kw-label = if keywords-label == none { lang-default.keywords-label } else { keywords-label }

  // ---------------------------------------------------------------- page
  set page(
    paper: "a4",
    margin: (x: 2.3cm, top: 2.6cm, bottom: 2.6cm),
    numbering: "1",
    number-align: center,
  )

  // ---------------------------------------------------------------- text
  // "New Computer Modern" is bundled with Typst itself, so the default
  // compiles on a machine with no extra fonts installed. Libertinus Serif is
  // the second choice, also bundled.
  set text(
    font: body-font,
    size: 10pt,
    lang: lang,
  )
  set par(justify: true, leading: 0.72em, spacing: 0.9em)
  set block(spacing: 1.05em)

  // ------------------------------------------------------------- headings
  set heading(numbering: "1.1")
  // Number equations so cross-references like @eq:foo resolve.
  set math.equation(numbering: "(1)")
  // Unnumbered headings (the bibliography, `numbering: none`) must not print the
  // counter: these show rules build the number by hand, so they check for
  // themselves — otherwise the bibliography reads "5.1. References".
  show heading.where(level: 1): it => block(above: 1.5em, below: 0.85em)[
    #set text(size: 12pt, weight: "bold")
    #if it.numbering != none [
      #counter(heading).display("1.")
      #h(0.6em)
    ]
    #it.body
  ]
  show heading.where(level: 2): it => block(above: 1.15em, below: 0.6em)[
    #set text(size: 10.5pt, weight: "bold")
    #if it.numbering != none [
      #counter(heading).display("1.1")
      #h(0.6em)
    ]
    #it.body
  ]
  show heading.where(level: 3): it => block(above: 1em, below: 0.5em)[
    #set text(size: 10pt, weight: "bold", style: "italic")
    #if it.numbering != none [
      #counter(heading).display("1.1.1")
      #h(0.5em)
    ]
    #it.body
  ]

  // ---------------------------------------------------------------- lists
  set list(indent: 1.2em, marker: ([•], [‣], [–]))
  set enum(indent: 1.2em)
  show figure: set block(breakable: false)
  // Internal default: table caption above the table, figure caption below.
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: image): set figure.caption(position: bottom)
  show figure.caption: set text(size: 9pt)
  show figure.caption: it => block(width: 95%)[
    #set align(left)
    #it
  ]
  show table.cell.where(y: 0): set text(weight: "bold")

  // Citations: superscript numbers in the prose, baseline entries in the
  // bibliography. Only the normal form (@key / #cite(<key>)) gets `super`;
  // narrative forms — #cite(form: "prose" / "full" / "author" / "year") — keep
  // their own semantics and baseline, because superscripting a whole phrase
  // breaks the sentence. `super` is applied once (nesting #text(size: ...)
  // inside it would shrink the label twice). Cross-references are not `cite`
  // elements, so @fig: / @tbl: / @eq: keep their normal inline rendering.
  show cite: it => if it.form == "normal" { super(it) } else { it }

  // ------------------------------------------------------------- title block
  // The affiliation ordering is derived ONCE here, then reused for both the
  // author superscripts and the affiliation list. (Typst's `array.position`
  // takes a predicate, not a value — hence the lambda.)
  block(width: 100%)[
    #set align(center)
    #set par(justify: false)
    #let aff-index = {
      let acc = ()
      for a in authors {
        for k in a.at("affil-keys", default: ()) {
          if k not in acc { acc.push(k) }
        }
      }
      acc
    }
    #let mark-of(k) = str(aff-index.position(x => x == k) + 1)

    #block[
      #set text(size: 17pt, weight: "bold")
      #set par(leading: 1.15em)
      #title
    ]
    #v(0.85em)
    #text(size: 11pt,
      authors.map(a => {
        let marks = a.at("affil-keys", default: ()).map(mark-of)
        let star = if a.at("equal", default: false) { "*" } else { "" }
        [#a.name#super[#marks.join(",")#star]]
      }).join([, ])
    )
    #v(0.65em)
    #text(size: 9pt,
      aff-index.map(k => {
        let aff = affiliations.at(k)
        let parts = (
          aff.at("department", default: none),
          aff.at("institution", default: none),
          aff.at("location", default: none),
          aff.at("country", default: none),
        ).filter(p => p != none)
        [#super[#mark-of(k)]#parts.join(", ")]
      }).join([\ ])
    )
    #v(0.9em)
  ]

  // ------------------------------------------------------------- abstract
  if abstract != [] [
    #block(width: 88%, inset: (x: 0pt, y: 0.4em))[
      #set align(center)
      #text(size: 10pt, weight: "bold", smallcaps[#abs-label])
    ]
    #block(width: 88%, inset: (x: 6%, y: 0pt))[
      #set text(size: 9.5pt)
      #set par(leading: 0.62em)
      #abstract
    ]
    #v(0.6em)
  ]

  if keywords.len() > 0 [
    #block(width: 88%, inset: (x: 6%, y: 0pt))[
      #set text(size: 9pt)
      #text(weight: "bold")[#kw-label:] #keywords.join(", ")
    ]
    #v(0.5em)
  ]

  // ---------------------------------------------------------------- body
  body

  // --------------------------------------------------------- bibliography
  if bib != none {
    show bibliography: set heading(numbering: none)
    set heading(outlined: false)
    bib
  }
}
