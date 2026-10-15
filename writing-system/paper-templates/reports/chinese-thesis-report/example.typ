// ===========================================================================
//  example.typ — chinese-thesis-report 模板的最小可编译示例
//
//  单独编译：  typst compile example.typ
//
//  这是模板库自带的演示文档：封面、中英文摘要、符号表、目录、分章正文、
//  三线表、公式、交叉引用各用一次。全文均为**占位示例**，不含任何真实研究结论。
//  新建报告请用脚手架（scripts/new_typst_paper.sh -t chinese-thesis-report），
//  它会生成 main.typ + meta.typ + content/ + vendor/ 的分层工程。
// ===========================================================================

#import "chinese-thesis-report.typ": report, three-line-table, caption-above, rule

// 模板刻意不设公式编号（章节号同样手写）；需要 @eq: 交叉引用时自己开。
#set math.equation(numbering: "(1)")

#show: report.with(
  title: [（示例）中文章节式技术研究报告],
  title-en: [Example Chinese Thesis-Style Technical Report],
  date: [二〇二六年九月],
  header-title: [（示例）中文章节式技术研究报告],
  fields: (
    ([研究方向：], [（示例）占位内容]),
    ([报告类型：], [（示例）技术研究报告]),
  ),
  abstract: [
    这是模板演示用的*占位摘要*。它说明摘要段落应该出现在封面目次之间的
    前置页里，标题与字号由模板排版，正文只需要写段落。

    第二段同样是占位内容，用来展示多段摘要的行距与缩进效果。
  ],
  keywords: [示例；占位；技术报告],
  notation: [
    #caption-above[表 0.1　符号与缩略语（示例）]
    #three-line-table(
      (28mm, 1fr),
      (
        [*符号/缩写*], [*含义*],
        table.hline(stroke: 0.55pt + rule),
        [$x$], [（示例）输入变量],
        [ABC], [（示例）缩略语],
      )
    )
  ],
)

= 第一章　绪论

这是占位正文，用于演示一级标题居中、另起一页、首行缩进两字的版式。
章节号由作者手写在标题文本里，模板不做自动编号。

== 1.1　研究背景

这是占位正文。三级以内的标题层级均已在模板中排版好。

= 第二章　方法

== 2.1　公式与交叉引用

独立公式见 @eq:demo：

$ y = f(x; theta) + epsilon $ <eq:demo>

== 2.2　三线表

#caption-above[表 2.1　三线表示例（数字为占位）]

#three-line-table(
  (28mm, 1fr, 1fr),
  (
    [*方案*], [*优点*], [*局限*],
    table.hline(stroke: 0.55pt + rule),
    [（示例）方案 A], [（示例）优点], [（示例）局限],
    [（示例）方案 B], [（示例）优点], [（示例）局限],
  )
)

= 第三章　结论

这是占位正文。本文件只用于验证模板可编译、版式正确，内容没有任何研究含义。
