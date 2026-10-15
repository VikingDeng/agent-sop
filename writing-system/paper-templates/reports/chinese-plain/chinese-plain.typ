// ---------------------------------------------------------------------------
//  chinese-plain.typ — 中文报告模板（纯黑白 · 工整）
//
//  AUTHORSHIP: original work for this template library.
//
//  设计取向，一句话：**只用黑与灰，靠字号和间距拉开层级。**
//    · 没有任何彩色 —— 标题、编号、分隔线、提示框全部是黑/深灰/浅灰
//    · 封面居中、留白规整，不做色块不做图形
//    · 正文宋体、标题黑体，首行缩进两字，行距放宽
//    · 提示框用「左侧粗黑线 + 浅灰底」，黑白打印也分得清
//
//  适合：技术研究报告、调研报告、开题材料、给评审看的正式文档。
//  也适合直接激光打印 —— 没有一处依赖彩色。
//
//  数学公式走 New Computer Modern Math，保持论文级质量。
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------- 灰阶 Palette
#let ink     = rgb("#000000")   // 标题、强调
#let body-ink = rgb("#1a1a1a")   // 正文（不叫 body：会和函数的 body 参数撞名）
#let muted   = rgb("#4d4d4d")   // 次级文字
#let faint   = rgb("#767676")   // 页眉页脚
#let rule    = rgb("#b3b3b3")   // 主线
#let hair    = rgb("#d9d9d9")   // 细线
#let surface = rgb("#f2f2f2")   // 提示框底
#let surface-strong = rgb("#e6e6e6")

#let cjk-serif = ("Noto Serif CJK SC", "Source Han Serif SC", "Noto Serif CJK TC")
#let cjk-sans  = ("Noto Sans CJK SC", "Source Han Sans SC", "Noto Sans CJK TC")
#let latin     = ("New Computer Modern", "Libertinus Serif", "TeX Gyre Termes")
#let mono      = ("DejaVu Sans Mono", "Noto Sans Mono CJK SC")

#let body-font = cjk-serif + latin
#let head-font = cjk-sans + latin

// ---------------------------------------------------------------------------
//  提示框 —— 左侧粗黑线 + 浅灰底，纯灰阶
// ---------------------------------------------------------------------------
#let callout-shades = (
  note:  (bar: rgb("#4d4d4d"), label: "说明"),
  tip:   (bar: rgb("#000000"), label: "建议"),
  warn:  (bar: rgb("#000000"), label: "注意"),
  alert: (bar: rgb("#000000"), label: "重要"),
)

#let zh-note(kind: "note", title: none, body) = {
  let c = callout-shades.at(kind, default: callout-shades.note)
  block(width: 100%, breakable: false)[
    #rect(width: 100%, fill: surface, stroke: (left: 2.4pt + c.bar),
          inset: (x: 0.95em, y: 0.7em))[
      #set text(font: head-font, size: 9.5pt)
      #set par(justify: true, leading: 0.68em, first-line-indent: 0em)
      #block(below: 0.3em)[
        #text(weight: "bold", size: 9pt, fill: ink)[#c.label]
        #if title != none and repr(title) != "[" + c.label + "]" [
          #h(0.8em) #text(weight: "bold", fill: ink)[#title]
        ]
      ]
      #body
    ]
  ]
  v(0.65em)
}

// 核心结论 —— 编号列表，左侧一条黑线，无底色
#let zh-key-points(items, title: "核心结论") = {
  block(width: 100%, breakable: false)[
    #rect(width: 100%, stroke: (left: 2.4pt + ink), inset: (x: 1em, y: 0.1em))[
      #set text(font: head-font, size: 10pt)
      #block(below: 0.5em)[#text(weight: "bold", size: 10.5pt, fill: ink)[#title]]
      #set enum(indent: 1.25em, body-indent: 0.5em)
      #items
    ]
  ]
  v(0.8em)
}

// ---------------------------------------------------------------------------
//  主入口
// ---------------------------------------------------------------------------
#let zh-report(
  title: [],
  subtitle: none,
  english-title: none,
  authors: (),
  date: none,
  organization: none,
  doc-kind: "技术研究报告",
  summary: none,
  cover: false,
  toc: true,
  numbering: "1",
  body,
) = {
  set document(title: title, author: authors.map(a => a.name))

  set page(
    paper: "a4",
    margin: (x: 2.5cm, top: 2.6cm, bottom: 2.5cm),
    numbering: numbering,
    number-align: center,
    header: context {
      if counter(page).get().first() > 1 {
        set text(font: head-font, size: 8.5pt, fill: faint)
        grid(columns: (1fr, auto), align: (left, right), [#doc-kind], [#title])
        v(-0.8em)
        line(length: 100%, stroke: 0.4pt + hair)
      }
    },
  )

  set text(font: body-font, size: 10.5pt, fill: body-ink, lang: "zh")
  set par(
    justify: true,
    leading: 0.8em,
    spacing: 0.45em,
    first-line-indent: (amount: 2em, all: false),
  )

  // 数学保持论文级字体
  show math.equation: set text(font: "New Computer Modern Math")
  show math.equation.where(block: true): set block(above: 0.9em, below: 0.9em)

  // ------------------------------------------------------------- 标题层级
  // 编号沿用你的标题文字（不自动加编号），只负责字号/字体/间距
  set heading(numbering: none)
  show heading: it => {
    set text(font: head-font)
    if it.level == 1 {
      block(above: 1.8em, below: 0.75em, sticky: true)[
        #set text(size: 14.5pt, weight: "bold", fill: ink)
        #it.body
      ]
    } else if it.level == 2 {
      block(above: 1.35em, below: 0.6em, sticky: true)[
        #set text(size: 12pt, weight: "bold", fill: ink)
        #it.body
      ]
    } else {
      block(above: 1.1em, below: 0.5em, sticky: true)[
        #set text(size: 10.5pt, weight: "bold", fill: muted)
        #it.body
      ]
    }
  }

  // ---------------------------------------------------------------- 代码
  show raw: set text(font: mono, size: 8.5pt)
  show raw.where(block: true): it => block(
    width: 100%, fill: surface, inset: 0.8em, stroke: 0.4pt + hair, it,
  )

  // ---------------------------------------------------------------- 表格
  set table(stroke: none, inset: (x: 0.6em, y: 0.45em), align: horizon)
  show table: it => block(above: 0.7em, below: 0.7em, it)
  show table.cell.where(y: 0): set text(font: head-font, weight: "bold", size: 9.5pt)
  show table.cell: set text(size: 9.5pt)

  // ---------------------------------------------------------------- 图表
  show figure.caption: set text(font: head-font, size: 9pt, fill: muted)
  show figure.caption: it => block(width: 95%)[
    #set align(left)
    #it
  ]

  set list(indent: 1.2em, body-indent: 0.55em)
  set enum(indent: 1.2em, body-indent: 0.55em)
  show list.item: set par(first-line-indent: 0em)
  show enum.item: set par(first-line-indent: 0em)

  // 引用：左侧黑细线，无底色
  show quote: it => block(
    width: 100%,
    stroke: (left: 1.6pt + rule),
    inset: (left: 1em, right: 0.5em, top: 0.35em, bottom: 0.35em),
  )[#it.body]

  // =============================================================== 封面
  if cover {
    page(header: none, footer: none, numbering: none)[
      #set par(first-line-indent: 0em, justify: false)
      #place(top + center, dy: 3.2cm, block(width: 100%)[
        #set align(center)
        #text(font: head-font, size: 9pt, fill: muted, tracking: 0.3em, doc-kind)
        #v(2.6em)
        #block[
          #set text(font: head-font, size: 26pt, weight: "bold", fill: ink)
          #set par(leading: 1.32em)
          #title
        ]
        #if subtitle != none [
          #v(0.8em)
          #block[
            #set text(font: head-font, size: 14pt, fill: muted)
            #set par(leading: 1.35em)
            #subtitle
          ]
        ]
        #if english-title != none [
          #v(1em)
          #text(size: 10.5pt, style: "italic", fill: faint, english-title)
        ]
        #if summary != none [
          #v(3.4em)
          #block(width: 88%)[
            #rect(width: 100%, stroke: 0.6pt + rule, inset: (x: 1.2em, y: 1em))[#summary]
          ]
        ]
      ])
      #place(bottom + left, dy: -0.4em, block(width: 100%)[
        #set par(justify: false)
        #set align(center)
        #line(length: 100%, stroke: 0.8pt + ink)
        #v(0.7em)
        #if authors.len() > 0 [
          #text(font: head-font, size: 10.5pt)[
            #authors.map(a => {
              let aff = a.at("affiliation", default: none)
              if aff == none { a.name } else { [#a.name（#aff）] }
            }).join([、])
          ]
          #v(0.4em)
        ]
        #text(font: head-font, size: 10pt, fill: muted)[
          #if organization != none [#organization] #if date != none [#h(1.2em) #date]
        ]
      ])
    ]
    pagebreak()
  } else {
    // ------------------------------------------------------------- 标题区
    block(width: 100%)[
      #set par(justify: false, first-line-indent: 0em)
      #text(font: head-font, size: 8.5pt, fill: muted, tracking: 0.2em, doc-kind)
      #v(0.8em)
      #block[
        #set text(font: head-font, size: 19pt, weight: "bold")
        #set par(leading: 1.22em)
        #title
      ]
      #if subtitle != none [
        #v(0.45em)
        #block[
          #set text(font: head-font, size: 11.5pt, fill: muted)
          #set par(leading: 1.3em)
          #subtitle
        ]
      ]
      #v(0.9em)
      #line(length: 100%, stroke: 1pt + ink)
      #v(0.5em)
      #set text(font: head-font, size: 9.5pt, fill: muted)
      #grid(columns: (1fr, auto), align: (left, right),
        {
          set par(justify: false)
          if authors.len() > 0 [
            #authors.map(a => {
              let aff = a.at("affiliation", default: none)
              if aff == none { a.name } else { [#a.name\ #text(size: 8.5pt, fill: faint)[#aff]] }
            }).join([ #h(1.4em) ])
          ]
        },
        {
          set align(right)
          [#organization #if date != none [\ #date]]
        },
      )
      #v(0.4em)
    ]

    // 摘要
    if summary != none {
      block(width: 100%)[
        #set text(size: 10pt)
        #set par(justify: true, leading: 0.75em, first-line-indent: 0em)
        #block(below: 0.35em)[#text(font: head-font, weight: "bold", size: 9.5pt)[摘要]]
        #block(inset: (left: 1.5em, right: 1.5em))[#summary]
      ]
      v(0.8em)
    }
  }

  // =============================================================== 目录
  if toc {
    show outline.entry.where(level: 1): it => { v(0.35em, weak: true); strong(it) }
    block(above: 1.2em, below: 1em)[
      #set text(font: head-font, size: 13pt, weight: "bold")
      #block(below: 0.7em)[目录]
      #show outline: set text(font: head-font, size: 9.5pt)
      #outline(title: none, depth: 2, indent: 1.1em)
    ]
    pagebreak(weak: true)
  }

  body
}
