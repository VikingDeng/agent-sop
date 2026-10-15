// ---------------------------------------------------------------------------
//  paper-macros.typ — a SMALL set of helpers that are safe in any venue
//  template.
//
//  Read this warning before adding anything here.
//  ------------------------------------------------
//  The whole point of content/ is that it renders unchanged under NeurIPS,
//  ICML, ACL, IEEE and the report templates. That only holds while the content
//  uses core Typst. Every macro added to this file narrows that portability,
//  because each venue template restyles `emph`, `strong`, headings and figures
//  in its own way.
//
//  So: nothing here may pull in a head, a rule, a colour or a font size. These
//  are pure convenience wrappers whose output is plain content. If you want a
//  styled callout box, that belongs in a REPORT template where you control the
//  whole document — see reports/modern-technical/modern-technical.typ.
//
//  Import from a content module like this:
//      #import "../shared/styles/paper-macros.typ": todo, eg, ie, defs
//  (adjust the relative path — content modules live in their own directory).
// ---------------------------------------------------------------------------

// An inline editorial note that is impossible to miss in a draft and easy to
// grep for before submission:  grep -rn "TODO" content/
#let todo(body) = [#emph[TODO:] #body]

// "e.g." / "i.e." with the punctuation typeset the way venues expect.
#let eg = [e.g.,]
#let ie = [i.e.,]

// A definition list. Kept deliberately plain: a bold term, an en dash, the
// definition. No colours, no rules.
#let defs(pairs) = {
  for (term, body) in pairs {
    block(above: 0.2em, below: 0.2em)[#strong[#term] #h(0.4em) -- #h(0.4em) #body]
  }
}

// Shorthand for a range with an en dash, which is the typographically correct
// dash and is NOT the hyphen most people type.
// Spelled `#a#sym.dash.en#b`, NOT `[#a--#b]`: after a code expression the `--`
// is lexed as part of the identifier (`a--`), not as an en-dash ligature.
#let rng(a, b) = [#a#sym.dash.en#b]

// Units, set upright and with a thin space, which is what physics and IEEE
// styles both expect. `math.upright` keeps the surrounding font rather than
// forcing one, and works in markup as well as in equations.
#let unit(value, u) = [#value#h(0.167em)#math.upright(u)]
