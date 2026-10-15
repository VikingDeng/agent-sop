// ---------------------------------------------------------------------------
//  method.typ
//
//  Demonstrates: display equations, aligned equations, inline math and a
//  reference into the maths from prose.
// ---------------------------------------------------------------------------

#let method() = [
  = Method
  <sec:method>

  == Problem formulation

  Let $s$ denote the scenario descriptor (terrain, geometry, waveform
  parameters) and $theta$ the physical parameters of the propagation model.
  A measured echo is decomposed as

  $ x_"real" = F(theta + Delta theta, s) + R_"stochastic" $ <eq:decomposition>

  where $F$ is the differentiable physics prior, $Delta theta$ is a
  low-dimensional calibration correction, and $R_"stochastic"$ collects
  everything the prior cannot express. The decomposition in
  @eq:decomposition is the entire modelling assumption: we never learn $F$,
  we learn only the two correction terms.

  == Residual generator

  The residual generator $G_phi$ is conditioned on a support set
  $cal(S) = \{x_1, dots, x_K\}$ of $K$ measured frames and predicts
  $hat(R) = G_phi(s, cal(S), z)$ for a latent $z$. Conditioning is performed by
  a permutation-invariant encoder,

  $ e = 1/K sum_(k=1)^K h_psi(x_k), quad hat(R) = G_phi(s, e, z), $ <eq:encoder>

  which makes the support set order-invariant --- a property the raw
  concatenation baseline in @sec:experiments does not have.

  == Range--Doppler consistency

  Let $cal(D)$ be the range--Doppler transform applied downstream. The
  generated sample must survive that transform, so we add

  $ cal(L)_"rd" = norm(cal(D)(x_"real") - cal(D)(hat(x)))_1, $ <eq:rdloss>

  where $hat(x) = F(theta + Delta theta, s) + hat(R)$. We found the
  $cal(L)_1$ form substantially more stable than an $cal(L)_2$ variant, which
  is consistent with the heavy-tailed clutter statistics reported for the
  scenes we study.

  == Training objective

  The full objective combines the reconstruction term, the range--Doppler
  consistency term and a diffusion loss on the residual,

  $ cal(L) = underbrace(cal(L)_"rec", "reconstruction") + lambda_1 cal(L)_"rd" + lambda_2 cal(L)_"diff", $ <eq:objective>

  with $lambda_1 = 0.5$ and $lambda_2 = 1.0$ held fixed across every
  experiment reported below.
]
