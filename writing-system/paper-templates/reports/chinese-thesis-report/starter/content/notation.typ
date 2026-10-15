// 主要符号与缩略语（占位示例，请替换）。
// 模板的 import 不跨文件继承：正文/此文件要用模板积木，必须自己 import。
#import "../vendor/template/chinese-thesis-report.typ": three-line-table, caption-above, rule

#caption-above[表 0.1　符号与缩略语（示例）]

#three-line-table(
  (28mm, 1fr),
  (
    [*符号/缩写*], [*含义*],
    table.hline(stroke: 0.55pt + rule),
    [ABC], [（示例）缩写一的含义],
    [XYZ], [（示例）缩写二的含义],
    [$x$], [（示例）变量的含义],
  )
)
