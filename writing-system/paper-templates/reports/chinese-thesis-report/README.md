# chinese-thesis-report — 中文章节式技术研究报告模板

**版本 0.1.0** · 自建模板 · MIT · 入口 `chinese-thesis-report.typ`

> 这是**自建**模板，版式参考国内高校学位论文的通行做法（A4、四边 25mm、宋体正文、
> 黑体标题、三线表、页眉页脚、封面 + 摘要 + 目录 + 符号表 + 分章正文 + 参考文献）。
> 它**不是**任何高校的官方学位论文模板，也不保证符合某校规范；正式提交学位论文
> 请使用本校官方模板。

与 `reports/chinese-research` 的分工：那一套是短篇报告风格（callout / key-points /
无封面无目录）；本模板是**长文档论文式骨架**，负责分页结构、页眉页脚、三线表与题注。

---

## 一、它替你做了什么

| 事项 | 模板负责 | 你负责 |
|---|---|---|
| A4 / 四边 25mm 页边距 | ✅ | |
| 正文宋体 12pt、首行缩进 2em、1.66 倍行距 | ✅ | |
| 一级标题居中黑体 16pt 并自动另起一页 | ✅ | |
| 二级 / 三级标题黑体 14pt / 13pt | ✅ | |
| 封面版式（标题、副标题、信息栏、日期） | ✅ | 传参 |
| 封面不编号、前置页小写罗马数字、正文阿拉伯数字 | ✅ | |
| 正文页眉（标题 + 细线）+ 页脚页码 | ✅ | 传参 |
| 摘要 / Abstract 标题与字号、关键词排版 | ✅ | 传参或留 `none` |
| 目录（`outline` depth 3，不生成多余标题） | ✅ | |
| 主要符号与缩略语页 | ✅ | 传内容 |
| 三线表、表题在上、图题在下 | 提供 helper | 调用 |
| **章节号** | ❌ 故意不做 | 标题里手写 `= 第一章　绪论` |

章节号是刻意留给你手写的（`set heading(numbering: none)`）：报告类文稿经常要
写「第一章」「1.1」这种与正文交叉引用的自定义编号，自动编号反而会打架。
需要自动编号时自己加 `#set heading(numbering: "1.1")`。

---

## 二、三个层次

```
chinese-thesis-report.typ   模板本体（唯一需要 import 的文件）
typst.toml                  包清单（版本 / license / entrypoint）
LICENSE                     MIT
```

### 参数表（`report(...)`）

| 参数 | 类型 | 说明 |
|---|---|---|
| `title` | content | 封面主标题（也是默认页眉） |
| `subtitle` | content / none | 封面副标题（可选） |
| `title-en` | content / none | 封面英文标题 |
| `kind` | str | 封面顶部字样，默认 `"技 术 研 究 报 告"` |
| `author` / `institution` | content / none | 封面作者 / 单位（可选） |
| `date` | content / none | 封面日期 |
| `fields` | array | 封面信息栏 `((标签, 内容), ...)`，逐行渲染 |
| `header-title` | content / none | 页眉文字，`none` 则用 `title` |
| `abstract` | content / none | 中文摘要正文（标题由模板排版） |
| `keywords` | content / none | 中文关键词 |
| `abstract-en` | content / none | 英文摘要正文 |
| `keywords-en` | content / none | 英文关键词 |
| `abstract-title` / `abstract-en-title` | str | 摘要标题文字 |
| `toc` | bool | 是否输出目录，默认 `true` |
| `notation` | content / none | 主要符号与缩略语（三线表内容） |
| `notation-title` / `notation-caption` | str / content | 符号表标题 / 表题 |
| `body` | content | 正文（`report.with(...)` 时由 `#show` 自动注入） |

任何 `none` 的可选块都**整块不渲染**（含它自己的分页），所以没有英文摘要就不写
`abstract-en`，不会留空白页。

### 可复用积木

```typst
#import "chinese-thesis-report.typ": report, three-line-table, caption-above,
  caption-below, report-outline, report-page-header, rule, light, body-font, head-font
```

* `three-line-table(columns, body)` — 三线表；表体里用
  `table.hline(stroke: 0.55pt + rule)` 画中间那条线。
* `caption-above[...]` / `caption-below[...]` — 表题（上方）/ 图题（下方），11pt 居中。
* `rule`（`#222222`）、`light`（`#B8B8B8`）— 线色令牌，和 body 里保持一致。
* `body-font` / `head-font` — 字体候选列表，内容页要用同款字体时 import 这两个。

---

## 三、典型用法

```typst
#import "chinese-thesis-report.typ": report

#show: report.with(
  title: [某技术研究报告],
  title-en: [A Technical Report],
  date: [二〇二六年九月],
  fields: (([研究方向：], [xxx]),),
  abstract: include "content/abstract.typ",
  keywords: [关键词一；关键词二],
  notation: include "content/notation.typ",
)

#include "content/ch1.typ"
```

正文文件里若要用三线表 / 表题，**需要自己 import**（Typst 的 import 不跨文件继承）：

```typst
#import "../vendor/template/chinese-thesis-report.typ": three-line-table, caption-above, rule

== 2.6　评价层级

#caption-above[表 2.1　评价层级]

#three-line-table(
  (30mm, 1fr),
  (
    [*层级*], [*指标*],
    table.hline(stroke: 0.55pt + rule),
    [信号一致性], [PSD、自相关……],
  )
)
```

---

## 四、字体

模板给出的是**候选列表**，本机装哪个用哪个，缺字体只会产生
`warning: unknown font family: ...` 这类良性提示，不会编译失败：

* 正文 / 衬线：`SimSun → Noto Serif CJK SC → Source Han Serif SC → Songti SC`，
  西文 `Times New Roman → Libertinus Serif`
* 标题 / 无衬线：`SimHei → Noto Sans CJK SC → Source Han Sans SC → Heiti SC`，
  西文 `Arial → Libertinus Sans`

要固定品牌字体，在自己的入口文件里 `#set text(font: (...))` 覆盖即可，
或把 `body-font` / `head-font` 换成自己的元组。

---

## 五、许可与来源

MIT，见 `LICENSE`。本模板为本地模板库自建（`origin: own`），不含任何上游代码，
因此没有 `PATCHES.md`。改编自 `radar-data-gen` 项目 2026-09 的单文件报告排版，
抽取时**按原样保留**度量值以保证既有报告逐页一致。
