// ---------------------------------------------------------------------------
//  introduction.typ
//
//  Content module contract:
//    * export one function named after the file
//    * the function returns the section, heading included
//    * use ONLY core Typst (`=`, `#figure`, `#table`, math, `@cite`)
//      so that every venue template can render it unchanged
// ---------------------------------------------------------------------------

#let introduction() = [
  = Introduction
  <sec:introduction>

  Radar perception models are only as good as the data they are trained on,
  and radar data is hard to obtain. A single scene must be recorded under many
  aspect angles, weather conditions and hardware configurations before a
  detector generalises, and each recording campaign is expensive. Simulation
  is the obvious substitute, but it forces a choice between two unsatisfactory
  extremes. Electromagnetic simulators model propagation faithfully and yet
  need per-scene calibration and minutes of compute per frame
  @richards2014fundamentals, while learned generators produce cheap frames
  that drift away from the physical statistics the downstream model must
  actually rely on @ho2020denoising.

  This paper asks a narrower and, we argue, more useful question: given a
  physics-based simulator that is roughly right and a handful of real echoes,
  can we learn the *residual* between them and thereby transfer the simulator
  to a new scenario? Framing the problem this way has three consequences.

  First, the physics prior does most of the work, so the learned component
  only has to model what the prior misses: stochastic clutter, calibration
  drift and multipath. This is a far smaller function class than the raw
  echo distribution, which is what makes few-shot transfer plausible.

  Second, the decomposition is interpretable by construction. When the
  sim-to-real gap is large the residual term grows, and that growth is itself
  a useful diagnostic for an operator deciding whether a scenario is
  trustworthy.

  Third, the same decomposition gives a natural regulariser: the residual is
  penalised in the range--Doppler domain rather than in raw sample space,
  which keeps generated frames consistent with the matched filter that
  downstream processing will apply.

  #figure(
    image("../figures/fig-pipeline.svg", width: 100%),
    caption: [
      The proposed pipeline. A differentiable physics prior produces a
      deterministic echo; a conditional residual generator, conditioned on a
      few measured frames, models the stochastic component. Both branches are
      combined before range--Doppler processing.
    ],
  ) <fig:pipeline>

  Our contributions are as follows.

  + We formulate few-shot radar scenario transfer as residual learning over a
    differentiable physics prior, rather than as unconstrained generative
    modelling of raw echoes.
  + We introduce a range--Doppler-domain consistency loss that ties the
    generated residual to the processing chain used downstream, and show that
    it is what prevents the drift observed in unconstrained baselines.
  + We demonstrate cross-scenario transfer from as few as five measured
    frames, and quantify the resulting gain in downstream detection average
    precision.
]
