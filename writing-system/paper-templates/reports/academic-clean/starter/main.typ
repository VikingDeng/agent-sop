// ------------------------------------------------------------
//  main.typ — assembly only. No prose, no layout code.
//
//  Layout lives in vendor/template/academic-clean.typ (frozen template snapshot).
//  Metadata lives in meta.typ.
//  Prose lives in content/*.typ.
//
//  Build: make build   ->   build/main.pdf
// ------------------------------------------------------------

#import "vendor/template/academic-clean.typ": report
#import "meta.typ": meta

#show: report.with(
  title: meta.title,
  subtitle: meta.subtitle,
  authors: meta.authors,
  date: meta.date,
  organization: meta.organization,
  doc-kind: meta.doc-kind,
  abstract: meta.abstract,
  toc: true,
  // Bibliography: add `bib: bibliography("/references.bib")` here and cite
  // with @key in content/ when you need references.
)

#include "content/01-introduction.typ"
#include "content/02-analysis.typ"
#include "content/03-conclusion.typ"
