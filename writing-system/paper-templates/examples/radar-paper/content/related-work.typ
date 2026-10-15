// ---------------------------------------------------------------------------
//  related-work.typ
// ---------------------------------------------------------------------------

#let related-work() = [
  = Related Work
  <sec:related>

  == Radar echo simulation

  Classical radar simulation rests on electromagnetic scattering models and
  measured Doppler signatures @skolnik2001introduction @chen2019microdoppler.
  These models are accurate within their calibration envelope but do not
  extrapolate to new scenes without per-scene work, which is exactly the cost
  we aim to amortise.

  == Generative models for signals

  Denoising diffusion and score-based models have become the default
  high-fidelity generators @ho2020denoising @song2021scorebased. Applied to
  radar they are typically trained on large measured corpora and treated as
  unconditional samplers. Our residual formulation differs in that the
  generator never models the dominant deterministic structure, only the gap.

  == Physics-informed learning

  Physics-informed neural networks embed a governing equation in the loss and
  have been used widely for forward and inverse problems
  @raissi2019physics. We borrow the idea of a hard physics prior but apply it
  as an explicit simulator branch rather than as a soft penalty, so
  correctness of the deterministic part is structural rather than learned.

  == Few-shot adaptation

  Meta-learning provides fast adaptation from few examples @finn2017model.
  Our setting is close in spirit but differs in the object being adapted: we
  adapt a simulator, not a classifier, and the adaptation signal is a physical
  consistency constraint rather than a supervised label.
]
