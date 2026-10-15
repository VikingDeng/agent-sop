// ---------------------------------------------------------------------------
//  abstract.typ
//
//  Exports the abstract BODY only (no `= Abstract` heading): venue templates
//  each render the abstract in their own place with their own styling.
// ---------------------------------------------------------------------------

#let abstract = [
  High-fidelity radar echo simulation is the bottleneck of data-driven radar
  perception: physics-based simulators are accurate but expensive and
  scenario-specific, while purely data-driven generators require thousands of
  measured frames that are rarely available for a new scene. We present a
  few-shot framework that couples a differentiable physics prior with a
  conditional generative model, so that a new scenario can be brought up from
  a handful of measured echoes. The physics prior supplies the
  deterministic propagation structure $F$, and a residual term absorbs the
  stochastic clutter and hardware effects that the prior cannot express. We
  show that the resulting simulator transfers across scenarios with as few as
  five measured frames, improving downstream detection average precision by a
  clear margin over both a physics-only baseline and an unconditional
  generative baseline, while remaining faithful to the underlying
  range--Doppler statistics.
]
