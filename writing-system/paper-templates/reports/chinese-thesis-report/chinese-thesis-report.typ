// ------------------------------------------------------------
//  chinese-thesis-report — 中文章节式技术研究报告模板
//  版本 0.1.0
//
//  这是**自建**模板，版式参考国内高校学位论文的通行做法
//  （A4、四边 25mm、宋体正文、黑体标题、三线表、页眉页脚、
//  封面 + 摘要 + 目录 + 符号表 + 分章正文 + 参考文献）。
//  它**不是**任何高校的官方学位论文模板，也不保证符合某校规范。
//
//  与 reports/chinese-research 的区别：那一套是短篇报告风格
//  （callout / key-points / 无封面无目录）；本模板是"论文式"
//  长文档骨架，负责分页结构、章节编号关闭、三线表与题注 helper。
// ------------------------------------------------------------

// ==================== 字体与颜色令牌 ====================
// 字体名按"可用性优先级"排列：本机装哪个就用哪个，缺失只会产生
// 良性的 unknown font family 警告（Typst 会自动往后找）。
#let cjk-serif = (
  "SimSun", "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC",
)
#let cjk-sans = (
  "SimHei", "Noto Sans CJK SC", "Source Han Sans SC", "Heiti SC",
)
#let latin-serif = ("Times New Roman", "Libertinus Serif")
#let latin-sans = ("Arial", "Libertinus Sans")

#let body-font = cjk-serif + latin-serif
#let head-font = cjk-sans + latin-sans

#let rule = rgb("#222222")
#let light = rgb("#B8B8B8")
#let header-ink = rgb("#555555")
#let header-rule = rgb("#777777")

// ==================== 排版积木 ====================
// three-line-table：三线表。columns 同 table()，body 传行内容，
// 中间用 `table.hline(stroke: 0.55pt + rule)` 自行分隔。
#let three-line-table(columns, body) = table(
  columns: columns,
  inset: (x: 4.5pt, y: 4pt),
  stroke: none,
  align: left,
  table.hline(stroke: 1pt + rule),
  ..body,
  table.hline(stroke: 1pt + rule),
)

// 表题在表上方（中文规范）。
// 注意：参数名不能叫 `text` —— 会遮住 Typst 内置的 text() 函数，
// 函数体里的 `#set text(size: 11pt)` 会报 "expected function, found content"。
#let caption-above(caption-body) = [
  #align(center)[
    #set text(size: 11pt)
    #caption-body
  ]
  #v(4pt)
]

// 图题在图下方。
#let caption-below(caption-body) = [
  #v(4pt)
  #align(center)[
    #set text(size: 11pt)
    #caption-body
  ]
]

// report-page-header：给"此后"的页面装页眉页脚。
// 必须在 pagebreak 之后调用，否则封面/前置页也会被装上。
// 放在 context 里是为了让 page 属性作用于文档剩余的页面。
#let report-page-header(title, font: latin-serif) = context {
  set page(
    header: [
      #set text(size: 9pt, fill: header-ink)
      #align(center)[#title]
      #v(2pt)
      #line(length: 100%, stroke: 0.45pt + header-rule)
    ],
    footer: [
      #set text(font: font, size: 9pt)
      #align(center)[#counter(page).display()]
    ],
  )
}

// report-outline：目录。title: none 是关键 —— outline 默认会自动
// 生成一个一级标题「目录」，而一级标题 show 规则带 pagebreak，
// 那个自动标题会多插一次分页。目录标题由模板自己排版。
#let report-outline(depth: 3, indent: 1em) = outline(
  title: none,
  depth: depth,
  indent: indent,
)

// ==================== 页面分区 ====================
#let report-cover(
  title: "",
  subtitle: none,
  title-en: none,
  kind: "技 术 研 究 报 告",
  author: none,
  institution: none,
  date: none,
  fields: (),
) = {
  set page(numbering: none)
  align(center)[
    #v(18mm)
    #text(font: head-font, size: 17pt, weight: "bold")[#kind]

    #v(30mm)

    #text(font: head-font, size: 25pt, weight: "bold")[#title]

    #if subtitle != none [
      #v(12pt)
      #text(font: latin-serif, size: 14pt)[#subtitle]
    ]

    #if title-en != none [
      #v(12pt)
      #text(font: latin-serif, size: 14pt)[#title-en]
    ]

    #v(42mm)

    #let meta-rows = {
      let rows = ()
      if author != none { rows.push(([作者：], author)) }
      if institution != none { rows.push(([单位：], institution)) }
      for f in fields { rows.push((f.at(0), f.at(1))) }
      rows
    }
    #if meta-rows.len() > 0 {
      grid(
        columns: (35mm, 72mm),
        row-gutter: 7pt,
        align: left,
        ..meta-rows.flatten(),
      )
    }

    #v(35mm)
    #if date != none { text(size: 12pt)[#date] }
  ]
  pagebreak()
}

#let report-front-matter(
  abstract: none,
  keywords: none,
  abstract-en: none,
  keywords-en: none,
  abstract-title: "摘　要",
  abstract-en-title: "Abstract",
  toc: true,
  notation: none,
  notation-title: "主要符号与缩略语",
  notation-caption: none,
) = {
  // 前置部分用小写罗马数字单独编号。
  set page(numbering: "I")
  counter(page).update(1)

  if abstract != none [
    #align(center)[
      #text(font: head-font, size: 16pt, weight: "bold")[#abstract-title]
    ]
    #v(10pt)

    #abstract

    #if keywords != none [
      #v(8pt)
      *关键词：* #keywords
    ]
    #pagebreak()
  ]

  if abstract-en != none [
    #align(center)[
      #text(font: latin-serif, size: 16pt, weight: "bold")[#abstract-en-title]
    ]
    #v(10pt)

    #text(font: latin-serif, size: 11pt)[#abstract-en]

    #if keywords-en != none [
      #v(8pt)
      #text(font: latin-serif, size: 11pt)[*Keywords:* #keywords-en]
    ]
    #pagebreak()
  ]

  if toc [
    #align(center)[
      #text(font: head-font, size: 16pt, weight: "bold")[目　录]
    ]
    #v(10pt)
    #report-outline()
    #pagebreak()
  ]

  if notation != none [
    #align(center)[
      #text(font: head-font, size: 16pt, weight: "bold")[#notation-title]
    ]
    #v(10pt)
    #if notation-caption != none { caption-above(notation-caption) }
    #notation
    #pagebreak()
  ]
}

// ==================== 主入口 ====================
// 用法（main.typ）：
//
//   #import "vendor/template/chinese-thesis-report.typ": report
//   #import "meta.typ": meta
//   #show: report.with(
//     title: meta.title,
//     title-en: meta.title-en,
//     date: meta.date,
//     fields: meta.cover-fields,
//     abstract: include "content/abstract.typ",
//     ...
//   )
//
// 正文里的标题**不参与自动编号**（numbering: none），章节号由
// 作者在标题里手写（如 `= 第一章　绪论`），以保留原有可见标题。
#let report(
  title: "",
  subtitle: none,
  title-en: none,
  kind: "技 术 研 究 报 告",
  author: none,
  institution: none,
  date: none,
  fields: (),
  header-title: none,
  abstract: none,
  keywords: none,
  abstract-en: none,
  keywords-en: none,
  abstract-title: "摘　要",
  abstract-en-title: "Abstract",
  toc: true,
  notation: none,
  notation-title: "主要符号与缩略语",
  notation-caption: none,
  body,
) = {
  set page(
    paper: "a4",
    margin: (left: 25mm, right: 25mm, top: 25mm, bottom: 25mm),
  )

  set text(font: body-font, size: 12pt, lang: "zh")

  // all: true —— 否则"跟在标题后面的第一段"不缩进（Typst 默认只缩进跟在段落后面的段落），
// 与中文学术排版惯例不符（章节标题后首段也应缩进两字）。
  set par(justify: true, first-line-indent: (amount: 2em, all: true), leading: 0.66em)

  // 章节号一律手写在标题文本里。
  set heading(numbering: none)

  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(8pt)
    align(center)[
      #set text(font: head-font, size: 16pt, weight: "bold")
      #it.body
    ]
    v(14pt)
  }

  show heading.where(level: 2): it => {
    v(10pt)
    block(breakable: false)[
      #set text(font: head-font, size: 14pt, weight: "bold")
      #it.body
    ]
    v(3pt)
  }

  show heading.where(level: 3): it => {
    v(7pt)
    block(breakable: false)[
      #set text(font: head-font, size: 13pt, weight: "bold")
      #it.body
    ]
    v(2pt)
  }

  report-cover(
    title: title,
    subtitle: subtitle,
    title-en: title-en,
    kind: kind,
    author: author,
    institution: institution,
    date: date,
    fields: fields,
  )

  report-front-matter(
    abstract: abstract,
    keywords: keywords,
    abstract-en: abstract-en,
    keywords-en: keywords-en,
    abstract-title: abstract-title,
    abstract-en-title: abstract-en-title,
    toc: toc,
    notation: notation,
    notation-title: notation-title,
    notation-caption: notation-caption,
  )

  // 正文：阿拉伯数字页码 + 页眉。
  set page(numbering: "1")
  counter(page).update(1)
  report-page-header(if header-title == none { title } else { header-title })

  body
}
