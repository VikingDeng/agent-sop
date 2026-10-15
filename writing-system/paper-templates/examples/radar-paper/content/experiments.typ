// ---------------------------------------------------------------------------
//  experiments.typ
//
//  Demonstrates: a booktabs-style table, a multi-column table with
//  alignment, bold emphasis in cells, and an algorithmic-style listing.
// ---------------------------------------------------------------------------

#let experiments() = [
  = Experiments
  <sec:experiments>

  == Setup

  We evaluate on three measured scenarios held out entirely from adaptation.
  For each scenario we sample $K in {1, 5, 20}$ measured frames as the support
  set. Detection average precision is measured with a fixed downstream
  detector that is never retrained, so any change in AP is attributable to
  the simulator rather than to the detector.

  == Baselines

  We compare against three baselines: a physics-only simulator with no learned
  residual (*Physics*), an unconditional diffusion model trained on the pooled
  measured corpus (*Uncond.*), and a conditional model that concatenates the
  support frames without the permutation-invariant encoder of @eq:encoder
  (*Concat.*).

  == Main results

  #figure(
    table(
      columns: 6,
      align: (left, center, center, center, center, center),
      stroke: none,
      table.hline(stroke: 1pt),
      table.header(
        [*Method*], [*K*], [*AP* $arrow.t$], [*FID* $arrow.b$], [*RD-MMD* $arrow.b$], [*Params*],
      ),
      table.hline(stroke: 0.5pt),
      [Physics], [--], [0.412], [--], [0.318], [0.0M],
      [Uncond.], [20], [0.507], [41.2], [0.144], [12.4M],
      [Concat.], [20], [0.556], [28.7], [0.101], [13.1M],
      [Ours], [1], [0.561], [22.4], [0.083], [13.3M],
      [*Ours*], [*5*], [*0.613*], [*17.9*], [*0.061*], [*13.3M*],
      [Ours], [20], [0.628], [15.3], [0.052], [13.3M],
      table.hline(stroke: 0.5pt),
      table.hline(stroke: 1pt),
    ),
    caption: [
      Cross-scenario transfer on three held-out scenes. *AP* is downstream
      detection average precision, *FID* and *RD-MMD* measure fidelity against
      real echoes in range--Doppler space. The proposed method reaches its
      best accuracy at $K = 5$ and degrades only mildly when the support set
      shrinks to a single frame.
    ],
    kind: table,
  ) <tbl:results>

  @tbl:results shows two effects worth separating. The gain from
  *Uncond.* to *Concat.* isolates the value of conditioning at all; the gain
  from *Concat.* to *Ours* isolates the value of the permutation-invariant
  encoder plus the range--Doppler loss. The second gain is the larger of the
  two at every support size, which supports our claim that the residual
  parameterisation --- not merely the extra conditioning --- is doing the work.

  #figure(
    image("../figures/fig-placeholder.svg", width: 72%),
    caption: [
      Placeholder result panel. Replace `figures/fig-placeholder.svg` with
      your own artefact; the example deliberately ships a vector placeholder
      so the project compiles without any binary assets.
    ],
  ) <fig:results>

  == Ablation

  Removing the range--Doppler term @eq:rdloss raises RD-MMD from 0.061 to
  0.119 and leaves AP roughly flat, which is the expected signature: the
  detector forgives the artefact, but the simulated statistics stop matching
  the real ones. Removing calibration ($Delta theta = 0$) costs both, which
  confirms that the two correction terms are not redundant.
]
