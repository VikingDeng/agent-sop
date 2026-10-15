// ---------------------------------------------------------------------------
//  conclusion.typ
// ---------------------------------------------------------------------------

#let conclusion() = [
  = Conclusion
  <sec:conclusion>

  We reframed few-shot radar scenario transfer as residual learning over a
  differentiable physics prior, so that the learned component only has to
  explain the gap between simulation and measurement rather than the whole
  echo distribution. The decomposition makes few-shot transfer practical,
  gives a range--Doppler consistency loss that keeps generated frames
  compatible with the downstream processing chain, and yields an interpretable
  diagnostic when a scene falls outside the prior's validity.

  The natural next step is to let the calibration term $Delta theta$ carry
  physical meaning rather than being a free parameter, which would turn the
  residual into a per-parameter diagnostic that an operator can act on
  directly. We also expect the formulation to transfer to other
  simulation-bottlenecked sensing modalities beyond radar.
]
