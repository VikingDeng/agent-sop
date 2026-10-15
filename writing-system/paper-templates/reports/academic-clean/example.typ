// ===========================================================================
//  example.typ — demonstration document for the academic-clean template.
//
//  Compile standalone:  typst compile example.typ
//
//  Greyscale by design: every distinction here is carried by type weight,
//  size or a rule, so it survives a mono laser printer. If it looks right in
//  black and white, it is right.
// ===========================================================================

#import "academic-clean.typ": report, note

#show: report.with(
  title: [A Survey of Physics-Informed Priors in Sensing Systems],
  subtitle: [Where hard constraints beat soft penalties],
  doc-kind: "Research Report",
  organization: "Department of Electronic Engineering",
  date: "September 2026",
  authors: (
    (name: "First Author", affiliation: "Beihang University"),
    (name: "Second Author", affiliation: "AirLab"),
  ),
  abstract: [
    Physics-informed learning has become the default answer to data scarcity in
    sensing. This report surveys the design choice that is least often made
    explicit: whether the governing physics enters as a *soft penalty* on the
    loss or as a *hard constraint* on the architecture. We find that the choice
    is usually justified by convenience rather than by the structure of the
    problem, and that hard constraints dominate whenever the physics is known
    exactly. A short decision procedure is proposed.
  ],
  toc: true,
)

= Introduction

The appeal of a soft physics penalty is obvious: it composes with any
architecture and requires no re-derivation when the model changes. Its cost is
less obvious. A soft penalty admits a trade-off between fitting the data and
satisfying the physics, and the optimiser is free to take that trade whenever
the data is noisy — which is exactly the regime in which the prior was
supposed to help.

#note(title: "Terminology")[
  *Hard constraint* means the physical law holds by construction, so no
  feasible setting of the parameters can violate it. *Soft penalty* means the
  law enters the objective and can be traded against data fit.
]

= The Two Regimes

== When the physics is exact

If the governing equation is known without free parameters, a hard constraint
is strictly better: it removes a degree of freedom the optimiser would
otherwise waste, and it makes the violation set empty rather than merely
expensive.

== When the physics is approximate

If the equation itself has uncertain coefficients, a hard constraint
propagates that uncertainty into the architecture and cannot be relaxed at
inference time. Here the soft form is the honest choice, provided the penalty
is re-weighted as the coefficient uncertainty grows.

$ cal(L)(theta) = cal(L)_"data"(theta) + lambda(t) cal(L)_"phys"(theta) $ <eq:weighted>

with $lambda$ annealed upward as the residual of the physical model shrinks.

= Evidence

#figure(
  table(
    columns: 4,
    align: (left, center, center, center),
    stroke: none,
    table.hline(stroke: 1pt),
    table.header([*Study*], [*Physics*], [*Constraint*], [*Held out*]),
    table.hline(stroke: 0.5pt),
    [A], [Exact], [Hard], [Yes],
    [B], [Exact], [Soft], [No],
    [C], [Approx.], [Soft], [Yes],
    [D], [Approx.], [Hard], [No],
    table.hline(stroke: 0.5pt),
    table.hline(stroke: 1pt),
  ),
  caption: [Reported outcomes grouped by whether the physics was exact and whether the constraint was hard.],
  kind: table,
) <tbl:survey>

Every study that used a hard constraint with exact physics reported transfer
to a held-out regime; none of the soft-penalty studies did.

#note(title: "Reading the table")[
  The comparison is confounded: studies that bother with a hard constraint are
  usually also the ones with cleaner simulators. @tbl:survey is suggestive,
  not causal.
]

= Decision Procedure

+ Is the governing equation exact? If yes, use a hard constraint.
+ If no, can the coefficient uncertainty be bounded? If yes, use a soft
  penalty with an annealed weight.
+ If neither, the physical prior is decoration. Report it as such.

= Conclusion

The soft-versus-hard choice is a modelling decision, not an implementation
detail, and it should be argued in the paper rather than defaulted.
