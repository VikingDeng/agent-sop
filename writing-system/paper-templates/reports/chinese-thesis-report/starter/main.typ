// ------------------------------------------------------------
//  main.typ — 只负责“组装”，不含排版也不含正文。
//
//  排版在 vendor/template/chinese-thesis-report.typ（模板快照）
//  元信息在 meta.typ
//  正文在 content/*.typ
//
//  构建：make build      （产物 build/main.pdf）
// ------------------------------------------------------------

#import "vendor/template/chinese-thesis-report.typ": report
#import "meta.typ": meta

// 模板刻意不做章节号/公式号自动编号（标题里手写“第一章”）。正文若要 @eq:
// 交叉引用，需要在这里开公式编号；不需要就删掉这一行。
#set math.equation(numbering: "(1)")

#show: report.with(
  title: meta.title,
  title-en: meta.title-en,
  date: meta.date,
  header-title: meta.header-title,
  fields: meta.cover-fields,

  abstract: include "content/abstract.typ",
  keywords: meta.keywords,
  abstract-en: include "content/abstract-en.typ",
  keywords-en: meta.keywords-en,

  notation: include "content/notation.typ",
)

#include "content/ch1-introduction.typ"
#include "content/ch2-method.typ"
#include "content/ch3-conclusion.typ"

// 参考文献：需要时取消下面两行注释，并在正文里用 @key 引用
// （references.bib 是起步用的示例文献库，请替换成自己的）。
// = 参考文献
// #bibliography("/references.bib", style: "ieee")
