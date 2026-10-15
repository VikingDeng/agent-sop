// ------------------------------------------------------------
//  main.typ — 只负责组装：import 模板与元信息，include 正文。
//  这里不写正文、不写排版，也不写字体/标签等版式常量；
//  版式在 vendor/template/generic.typ（模板快照），
//  文种与元信息在 meta.typ。
//
//  构建：make build      （产物 build/main.pdf）
//  摘要正文在 content/abstract.typ，由 meta.typ 载入。
//
//  默认文种是“尚未确定投稿目标”的论文草稿：
//  引言 / 相关工作 / 方法或论证 / 结果与分析 / 结论。
//  理论稿可以把“方法”换成“命题 + 证明”，把“结果与分析”换成
//  推论或讨论；相关工作也可以并入引言或移到方法之后（见各文件注释）。
//  删改章节时同步改下面的 #include。
// ------------------------------------------------------------

#import "vendor/template/generic.typ": generic-paper
#import "meta.typ": meta

// 这里只传元信息、语言（meta.lang）和文献。模板按 lang 选字体栈与
// “摘要 / 关键词”标签（见 vendor/template/generic.typ 的 lang-defaults）；
// 需要显式改字体或标签时给模板传 font / abstract-label / keywords-label。
#show: generic-paper.with(
  title: meta.title,
  authors: meta.authors,
  affiliations: meta.affiliations,
  keywords: meta.keywords,
  abstract: meta.abstract,
  lang: meta.lang,
  // 文献：由模板在正文之后输出；正文用 @key 引用，渲染成上标编号 [1]，
  // 文末条目的 [1] 保持普通基线。style 用 Typst 内置 ieee（顺序编号方括号）。
  // references.bib 起步只有一条真实文献，仅用于演示排版，请整体替换。
  bib: bibliography("/references.bib", style: "ieee"),
)

#include "content/01-introduction.typ"
#include "content/02-related-work.typ"
#include "content/03-method.typ"
#include "content/04-results.typ"
#include "content/05-conclusion.typ"
