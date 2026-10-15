// ------------------------------------------------------------
//  meta.typ — document metadata (single source of truth).
//
//  Only "what this document is"; no layout code.
//  main.typ passes these values to the template; content/ holds none of them.
//  Everything below is PLACEHOLDER text — replace it.
// ------------------------------------------------------------

#let meta = (
  title: [（占位，待替换）工程技术文档标题：写明对象与结论指向],
  subtitle: [（占位，待替换）一句话说清这份文档要支撑什么决定],
  authors: (
    (name: "姓名（占位，待替换）", affiliation: "单位（占位，待替换）"),
  ),
  date: "二〇二六年九月（占位，待替换）",
  organization: "组织（占位，待替换）",
  // doc-kind 显示在页眉左侧与标题上方；本 starter 的文种是工程技术文档。
  doc-kind: "工程技术文档",
  // 文种（BCP-47）：模板按它选字体栈与标签，"zh" → Noto/SourceHan SC 优先、
  // 目录标签“目录”。英文稿改成 "en"；显式覆盖字体/标签的写法见模板参数说明。
  lang: "zh",
  summary: [
    （占位，待替换）三到四句话：这份文档回答什么问题、依据什么约束与证据、
    读者据此可以做什么决定。摘要在目录之前，写给不读全文的人。
  ],
)
