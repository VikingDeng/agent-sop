// ------------------------------------------------------------
//  meta.typ — 元信息唯一事实来源；这里不放排版代码。
//
//  摘要正文单独放在 content/abstract.typ，由本文件载入后传给模板：
//  这样 main.typ 只做组装，长文本也不堆在元信息里。
//  下面的值全部是**占位，待替换**。
// ------------------------------------------------------------

#let abstract-body = include "content/abstract.typ"

#let meta = (
  title: [（占位，待替换）论文标题],
  authors: (
    // affil-keys 指向下面的 affiliations；equal: true 会加 * 标记共同一作。
    (name: "姓名（占位，待替换）", affil-keys: ("a",)),
  ),
  affiliations: (
    a: (institution: "单位（占位，待替换）", location: "城市（占位，待替换）"),
  ),
  keywords: ("关键词一（占位）", "关键词二（占位）"),
  abstract: abstract-body,
  // 文种（BCP-47）：模板按它选字体栈与“摘要 / 关键词”标签，"zh" → CJK SC 优先、
  // 中文标签。英文稿改成 "en"；显式覆盖字体/标签的写法见模板参数说明。
  lang: "zh",
)
