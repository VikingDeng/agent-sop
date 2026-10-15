// Content module contract:
//   * export one function named after the file
//   * it returns the whole section, heading included
//   * use ONLY core Typst (=, #figure, #table, math, @cite) so that every
//     venue template can render it unchanged
#let introduction() = [
  = Introduction

  Opening paragraph. State the problem and why it matters.

  Second paragraph. State what is missing in prior work.

  #figure(
    // image("../figures/your-figure.svg", width: 100%),
    rect(width: 100%, height: 3cm, stroke: 0.5pt)[Placeholder],
    caption: [Replace me with a real figure.],
  ) <fig:overview>

  Contribution list:

  + First contribution.
  + Second contribution.
  + Third contribution.
]
