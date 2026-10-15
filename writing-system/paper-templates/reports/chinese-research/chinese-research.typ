// ---------------------------------------------------------------------------
//  chinese-research.typ — 中文技术研究报告模板
//
//  AUTHORSHIP: original work for this template library. Not derived from any
//  conference or publisher template.
//
//  用途：中文调研综述（本库三个默认入口之一，doc-kind=调研综述）、
//  技术研究报告、项目报告、给领导/专家评审的材料。
//
//  正文约定（starter/ 已接线，模板负责渲染）：
//    * 文献走语义 cite + bibliography：正文标注默认上标方括号 [1]，
//      文末条目标号保持普通基线；不手写数字、不做正则替换。
//    * 表题在表格上方、图题在图片下方；图表要有稳定 label 并在正文引用。
//
//  设计取向（按需求刻意避开的三件事）：
//    * 不是 Word 公文风 —— 标题用黑体、正文用宋体，层级靠字号与字重拉开，
//      不用「一、（一）1.」那套缩进式编号；
//    * 不大面积蓝色 —— 全文只有墨色与灰阶，唯一暖色仅出现在细线和标签上；
//    * 公式仍是论文级 —— 数学一律走 New Computer Modern Math，
//      中文与西文/公式混排交给 Typst 的 CJK 断行与 cjk-latin-spacing。
// ---------------------------------------------------------------------------

#let ink      = rgb("#1a1a1a")
#let muted    = rgb("#484848")
#let faint    = rgb("#767676")
#let rule     = rgb("#d2d2d2")
#let hair     = rgb("#e4e4e4")
#let surface  = rgb("#f6f6f4")
#let accent   = rgb("#8a4b2a")   // 赭石，仅用于细线与标签

#let cjk-serif = ("Noto Serif CJK SC", "Source Han Serif SC", "Noto Serif CJK TC")
#let cjk-sans  = ("Noto Sans CJK SC", "Source Han Sans SC", "Noto Sans CJK TC")
#let latin     = ("New Computer Modern", "Libertinus Serif", "TeX Gyre Termes")
#let mono      = ("DejaVu Sans Mono", "Noto Sans Mono CJK SC")

#let body-font = cjk-serif + latin
#let head-font = cjk-sans + latin

// ---------------------------------------------------------------------------
//  提示框
// ---------------------------------------------------------------------------
#let zh-callout-colors = (
  note:    (bar: rgb("#5b6270"), label: "说明"),
  tip:     (bar: rgb("#3f6b4a"), label: "建议"),
  warn:    (bar: rgb("#a8791f"), label: "注意"),
  alert:   (bar: rgb("#9c3b30"), label: "重要"),
)

#let zh-callout(kind: "note", title: none, body) = {
  let c = zh-callout-colors.at(kind, default: zh-callout-colors.note)
  block(width: 100%, breakable: false)[
    // 左侧色条用 stroke 实现，不用 place + height:100%。
    // place 里的 height:100% 是相对整页解析的，色条会一路拖到页脚。
    #rect(width: 100%, fill: surface, stroke: (left: 2.6pt + c.bar), inset: (x: 0.9em, y: 0.65em))[
      #set text(font: head-font, size: 9.5pt)
      #set par(justify: true, leading: 0.62em, first-line-indent: 0em)
      #block(below: 0.3em)[
        #text(weight: "bold", size: 9pt, fill: c.bar)[#c.label]
        // Suppress a title that just repeats the label, otherwise
        // `#zh-callout(kind: "tip", title: [建议])` prints "建议  建议".
        // (Content and string never compare equal in Typst, so compare repr.)
        #if title != none and repr(title) != "[" + c.label + "]" [
          #h(0.7em) #text(weight: "bold", fill: ink)[#title]
        ]
      ]
      #body
    ]
  ]
  v(0.6em)
}

// 要点框 —— 整篇报告里唯一值得十秒钟扫完的地方
#let zh-key-points(items, title: "核心结论") = {
  block(width: 100%, breakable: false)[
    #rect(width: 100%, fill: surface, stroke: (left: 2.6pt + accent), inset: (x: 1em, y: 0.8em))[
      #set text(font: head-font, size: 10pt)
      #block(below: 0.45em)[#text(weight: "bold", size: 10.5pt, fill: accent)[#title]]
      #set enum(indent: 1.2em, body-indent: 0.5em)
      #set enum(numbering: n => text(fill: accent, weight: "bold")[#n.])
      #items
    ]
  ]
  v(0.7em)
}

// ---------------------------------------------------------------------------
//  主入口
// ---------------------------------------------------------------------------
#let zh-report(
  title: [],
  subtitle: none,
  authors: (),
  date: none,
  organization: none,
  doc-kind: "技术研究报告",
  summary: none,
  english-title: none,
  cover: false,
  toc: true,
  numbering: "1",
  bib: none,
  body,
) = {
  set document(title: title, author: authors.map(a => a.name))

  set page(
    paper: "a4",
    margin: (x: 2.4cm, top: 2.6cm, bottom: 2.5cm),
    numbering: numbering,
    number-align: center,
    header: context {
      let pg = counter(page).get().first()
      if pg > 1 {
        set text(font: head-font, size: 8.5pt, fill: faint)
        grid(columns: (1fr, auto), align: (left, right), [#doc-kind], [#title])
        v(-0.8em)
        line(length: 100%, stroke: 0.4pt + hair)
      }
    },
    footer: context {
      let pg = counter(page).get().first()
      if pg > 1 {
        set text(font: head-font, size: 8.5pt, fill: faint)
        line(length: 100%, stroke: 0.4pt + hair)
        v(-0.95em)
        grid(columns: (1fr, auto), align: (left, right), [#organization], [#pg])
      }
    },
  )

  // 正文：中文用思源宋体，西文/数字回落到 New Computer Modern
  set text(font: body-font, size: 10.5pt, fill: ink, lang: "zh")
  // 中文段落：首行缩进两字，行距放宽，段间距收紧（与缩进配套，避免双重留白）
  set par(
    justify: true,
    leading: 0.78em,
    spacing: 0.42em,
    first-line-indent: (amount: 2em, all: false),
  )

  // 数学保持论文级：显式指定数学字体，避免回落成中文字形
  show math.equation: set text(font: "New Computer Modern Math")
  show math.equation.where(block: true): set block(above: 0.85em, below: 0.85em)

  // 标题：黑体，层级靠字号+字重，不用公文式编号
  // Number equations: a report that cross-references one needs numbers.
  set math.equation(numbering: "(1)")

  set heading(numbering: "1.1")
  show heading: it => {
    set text(font: head-font)
    let lvl = it.level
    // 未编号标题（参考文献等，numbering: none）不能显示计数器：
    // 本 show 规则是手工排编号的，必须自己判断，否则会出现「4.1 参考文献」。
    let numbered = it.numbering != none
    if lvl == 1 {
      block(above: 1.7em, below: 0.8em, sticky: true)[
        #set text(size: 15pt, weight: "bold", fill: ink)
        #if numbered [
          #text(fill: accent, size: 13pt)[#counter(heading).display("1")]
          #h(0.55em)
        ]
        #it.body
      ]
    } else if lvl == 2 {
      block(above: 1.3em, below: 0.6em, sticky: true)[
        #set text(size: 12.5pt, weight: "bold", fill: ink)
        #if numbered [
          #text(fill: muted, size: 11pt)[#counter(heading).display("1.1")]
          #h(0.5em)
        ]
        #it.body
      ]
    } else {
      block(above: 1.1em, below: 0.5em, sticky: true)[
        #set text(size: 11pt, weight: "bold", fill: muted)
        #if numbered [
          #counter(heading).display("1.1.1")
          #h(0.5em)
        ]
        #it.body
      ]
    }
  }

  // 代码
  show raw: set text(font: mono, size: 8.5pt)
  show raw.where(block: true): it => block(
    width: 100%, fill: surface, inset: 0.8em, radius: 2pt, stroke: 0.4pt + rule, it,
  )

  // 表格：三线表观感，表头加粗
  set table(stroke: none, inset: (x: 0.6em, y: 0.42em), align: horizon)
  show table: it => block(above: 0.6em, below: 0.6em, it)
  show table.cell.where(y: 0): set text(font: head-font, weight: "bold", size: 9.5pt)
  show table.cell: set text(size: 9.5pt)

  // 图表题注：内部文档默认表题在上、图题在下
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: image): set figure.caption(position: bottom)
  show figure.caption: set text(font: head-font, size: 9pt, fill: muted)
  show figure.caption: it => block(width: 95%)[
    #set align(left)
    #it
  ]

  // 文献引用：正文上标编号，文末 bibliography 条目保持基线。
  // 只对普通形式（form: "normal"，即 @key / #cite(<key>)）施加一次 super；
  // #cite(form: "prose"/"full"/"author"/"year") 是行文里的叙述式引用，整段
  // 上标会破坏句子，因此原样保留它们的语义与基线。super 只施加一次，不要再
  // 套 #text(size: ...)（那会双重缩小）。@fig: / @tbl: / @eq: 不是 cite 元素，
  // 交叉引用不受影响。
  show cite: it => if it.form == "normal" { super(it) } else { it }

  set list(indent: 1.2em, body-indent: 0.55em)
  set enum(indent: 1.2em, body-indent: 0.55em)
  // 列表项本身不首行缩进
  show list.item: set par(first-line-indent: 0em)
  show enum.item: set par(first-line-indent: 0em)

  // =============================================================== 封面
  // cover: true 时渲染整页封面（标题区独占一页 + 页脚单位/日期），
  // 目录另起一页。cover: false 时保持原来的「标题区直接接正文」行为。
  if cover {
    page(header: none, footer: none, numbering: none)[
      #set par(first-line-indent: 0em, justify: false)
      #line(length: 100%, stroke: 3pt + ink)
      #v(0.9em)
      #text(font: head-font, size: 9pt, weight: "bold", fill: accent,
            tracking: 0.28em, doc-kind)
      #v(2.2em)
      #block[
        #set text(font: head-font, size: 27pt, weight: "bold", fill: ink)
        #set par(leading: 1.3em)
        #title
      ]
      #if subtitle != none [
        #v(0.75em)
        #block[
          #set text(font: head-font, size: 14.5pt, fill: muted)
          #set par(leading: 1.32em)
          #subtitle
        ]
      ]
      #if english-title != none [
        #v(1em)
        #text(size: 10.5pt, style: "italic", fill: faint, english-title)
      ]
      #if summary != none [
        #v(6.5em)
        #rect(width: 100%, fill: surface, stroke: 0.6pt + rule, radius: 3pt,
              inset: (x: 1.3em, y: 1.1em))[#summary]
      ]
      #place(bottom + left, dy: -0.2em, block(width: 100%)[
        #set par(justify: false)
        #line(length: 100%, stroke: 0.6pt + rule)
        #v(0.55em)
        #grid(columns: (1fr, auto), align: (left, right),
          [#text(font: head-font, size: 10pt, fill: muted)[#organization]],
          [#text(font: head-font, size: 10pt, fill: muted)[#date]],
        )
      ])
    ]
    pagebreak()
  } else {
  // =============================================================== 标题区
  block(width: 100%)[
    #set align(left)
    #set par(justify: false, first-line-indent: 0em)
    #text(font: head-font, size: 8.5pt, weight: "bold", fill: accent, doc-kind)
    #v(0.6em)
    #block[
      #set text(font: head-font, size: 21pt, weight: "bold")
      #set par(leading: 1.2em)
      #title
    ]
    #if subtitle != none [
      #v(0.4em)
      #block[
        #set text(font: head-font, size: 12pt, fill: muted)
        #set par(leading: 1.25em)
        #subtitle
      ]
    ]
    #v(0.9em)
    #line(length: 100%, stroke: 1.2pt + ink)
    #v(0.55em)
    #set text(font: head-font, size: 9.5pt, fill: muted)
    #grid(
      columns: (1fr, auto),
      align: (left, right),
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

  // 摘要（封面模式下已在封面里呈现，这里跳过）
  if summary != none and not cover {
    block(width: 100%)[
      #set text(size: 10pt)
      #set par(justify: true, leading: 0.72em, first-line-indent: 0em)
      #rect(width: 100%, fill: surface, stroke: none, inset: (x: 1em, y: 0.85em))[
        #block(below: 0.35em)[#text(font: head-font, weight: "bold", size: 9.5pt)[摘要]]
        #summary
      ]
    ]
    v(0.6em)
  }

  }  // end of `if cover { ... } else {`

  // 目录
  if toc {
    show outline.entry.where(level: 1): it => { v(0.35em, weak: true); strong(it) }
    block(above: 1.2em, below: 1em)[
      #set text(font: head-font, size: 13pt, weight: "bold")
      #block(below: 0.6em)[目录]
      #show outline: set text(font: head-font, size: 9.5pt)
      #outline(title: none, depth: 2, indent: 1.1em)
    ]
    pagebreak(weak: true)
  }

  body

  if bib != none {
    show bibliography: set heading(numbering: none)
    set heading(outlined: false)
    bib
  }
}
