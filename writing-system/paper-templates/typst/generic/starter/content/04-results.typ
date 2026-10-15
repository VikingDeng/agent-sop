// 第 4 节｜结果与分析（占位，待替换）
//
// 本节职责：报告可核对的结果，并说明它们支持哪些结论、不支持哪些结论。
// 表用 #figure(kind: table)，表题由模板放在表格上方，label 用 tbl: 前缀。
// 表里的数：理论推导、解析量与实测各自注明来源与条件，无依据不填
// （写“无数据”，或删掉整张表）。
// 理论稿可以用例子、反例或推论代替本节。

= 结果与分析

（占位，待替换）先说清结果来自什么条件，再给结果本身。

#figure(
  table(
    columns: (auto, 1fr, 1fr),
    align: (left, left, left),
    stroke: none,
    table.hline(stroke: 1pt),
    table.header([*占位项*], [*占位条件*], [*占位结果*]),
    table.hline(stroke: 0.5pt),
    [（占位）A], [（占位）条件说明], [（占位）结果说明],
    [（占位）B], [（占位）条件说明], [（占位）结果说明],
    table.hline(stroke: 1pt),
  ),
  caption: [排版示例表：表中内容全部是占位，不是实测数据。],
  kind: table,
) <tbl:placeholder>

@tbl:placeholder 是占位表的稳定 label；换成真实结果时保留 label 并同步正文引用。
