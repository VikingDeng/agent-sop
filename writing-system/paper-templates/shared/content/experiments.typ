#let experiments() = [
  = Experiments

  == Setup

  Datasets, baselines, metrics.

  == Main results

  #figure(
    table(
      columns: 4,
      align: (left, center, center, center),
      stroke: none,
      table.hline(stroke: 1pt),
      table.header([*Method*], [*Metric A* $arrow.t$], [*Metric B* $arrow.t$], [*Cost* $arrow.b$]),
      table.hline(stroke: 0.5pt),
      [Baseline], [0.00], [0.00], [1x],
      [*Ours*], [*0.00*], [*0.00*], [1x],
      table.hline(stroke: 0.5pt),
      table.hline(stroke: 1pt),
    ),
    caption: [Replace with your real numbers.],
    kind: table,
  ) <tbl:results>

  @tbl:results shows the main comparison.

  == Ablation

  Remove one component at a time and report what breaks.
]
