// ------------------------------------------------------------
//  main.typ — assembly only. No prose, no layout code, no layout constants.
//
//  Layout lives in vendor/template/modern-technical.typ (frozen snapshot).
//  Metadata lives in meta.typ (the document language included).
//  Prose lives in content/*.typ.
//
//  Build: make build   ->   build/main.pdf
//
//  默认文种是工程技术文档：正文按“问题与约束 / 原理与方案 /
//  实现与接口 / 验证与限制”准备。按实际篇幅删改：
//  短说明可以删掉设计与实现部分，短设计可以省略与原理重复的内容，
//  删掉某一节时同步删掉下面相应的 #include。
// ------------------------------------------------------------

#import "vendor/template/modern-technical.typ": report
#import "meta.typ": meta

// 这里只传元信息、语言（meta.lang）和文献。字体栈、目录标签这类版式默认值由
// 模板按 lang 决定（见 vendor/template/modern-technical.typ 的 lang-defaults）；
// 需要显式改字体或标签时给模板传 font / heading-font / toc-title。
// 关掉目录用 toc: false（模板默认 toc: true）。
#show: report.with(
  title: meta.title,
  subtitle: meta.subtitle,
  authors: meta.authors,
  date: meta.date,
  organization: meta.organization,
  doc-kind: meta.doc-kind,
  summary: meta.summary,
  lang: meta.lang,
  // 文献：模板负责在正文之后输出；正文用 @key 引用，渲染成上标编号 [1]，
  // 文末条目的 [1] 保持普通基线。style 用 Typst 内置 ieee（顺序编号方括号）。
  // references.bib 起步只有一条真实文献，仅用于演示排版，请整体替换。
  bib: bibliography("/references.bib", style: "ieee"),
)

#include "content/01-problem.typ"
#include "content/02-principle.typ"
#include "content/03-implementation.typ"
#include "content/04-validation.typ"
