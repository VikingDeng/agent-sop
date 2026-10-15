// Placeholder prose — replace with your own analysis.
// Imports do not cross files in Typst: import what this chapter uses.
#import "../vendor/template/academic-clean.typ": note

= Analysis

Placeholder body text. Equations are numbered by the template:

$ cal(L)(theta) = cal(L)_"data"(theta) + lambda cal(L)_"prior"(theta) $ <eq:placeholder>

@eq:placeholder is a placeholder equation; delete it if your report has none.

#figure(
  table(
    columns: 4,
    align: (left, center, center, center),
    stroke: none,
    table.hline(stroke: 1pt),
    table.header([*Case*], [*Setting*], [*Observed*], [*Held out*]),
    table.hline(stroke: 0.5pt),
    [A], [Placeholder], [Placeholder], [Yes],
    [B], [Placeholder], [Placeholder], [No],
    table.hline(stroke: 0.5pt),
    table.hline(stroke: 1pt),
  ),
  caption: [Placeholder table — every cell above is illustrative, not measured.],
  kind: table,
) <tbl:placeholder>

@tbl:placeholder is referenced from the prose.

#note(title: "Reading the table")[
  Placeholder note. Say what the table does *not* show; a table without a stated
  limitation is usually being over-read.
]
