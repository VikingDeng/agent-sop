// ------------------------------------------------------------
//  main.typ — 只负责“组装”，不含排版也不含正文。
//
//  排版在 vendor/template/chinese-research.typ（模板快照，不要手改）
//  元信息在 meta.typ
//  正文在 content/*.typ（一节一文件）
//
//  构建：make build      （产物 build/main.pdf）
//
//  默认文种是调研综述：正文按“问题与范围 / 代表工作与机制 /
//  横向比较与证据 / 结论与开放问题”准备。材料少时按实际需要删改，
//  但删掉某一节要同步删掉下面相应的 #include。
// ------------------------------------------------------------

#import "vendor/template/chinese-research.typ": zh-report
#import "meta.typ": meta

#show: zh-report.with(
  title: meta.title,
  subtitle: meta.subtitle,
  authors: meta.authors,
  date: meta.date,
  organization: meta.organization,
  doc-kind: meta.doc-kind,
  summary: meta.summary,
  toc: true,
  // 文献：模板负责在正文之后输出；正文用 @key 引用，渲染成上标编号 [1]，
  // 文末条目的 [1] 保持普通基线。style 用 Typst 内置 ieee（顺序编号方括号）。
  // references.bib 起步只有一条真实文献，仅用于演示排版，请整体替换。
  bib: bibliography("/references.bib", style: "ieee"),
)

#include "content/01-question.typ"
#include "content/02-works.typ"
#include "content/03-comparison.typ"
#include "content/04-conclusion.typ"
