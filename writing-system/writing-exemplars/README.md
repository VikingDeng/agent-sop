# writing-exemplars — 技术文档范文库

按文种和问题查的对照库。每条记录的是：**某一篇文档在某个位置上怎么组织信息、读者因此能判断什么、哪些条件使它成立、换到我们的交付里哪一部分不能照搬。** 库里不保存全文，只有短摘录、精确 URL、章节定位和实际阅读范围。

**按当前任务选 1–2 条读，不要通读全库。** 条目是参照物，不是相似度目标；也不模仿英文句法或文章本身的结论。

## 先定文种

来选例之前先按读者任务定三类写法之一：调研综述、工程技术文档、研究论文，入口是
[../skills/research-writing-pipeline/references/document-genres.md](../skills/research-writing-pipeline/references/document-genres.md)。
本库只提供**选例**，判断标准在写作技能与 [../document-quality.md](../document-quality.md)；
条目说明某篇文档在某个位置上怎么组织信息、读者因此能判断什么，不能当成本文种的规范。

| 你要写／要改 | 先读 |
|---|---|
| 综述的结构组织 | [macro](macro-structure.md) 的 A2——只作相关综述结构的局部参考，不覆盖选型调研 |
| 选型调研、设计提案、方案说明、架构决策 | [macro](macro-structure.md) 的 B1（范围与非目标）、B3（代价与被否方案）等决策类条目 |
| 官方文档、原理与机制说明 | [micro](micro-structure.md) 的 C1（可复算证据）、C2（命名与对照） |
| 故障复盘、过程叙述 | [micro](micro-structure.md) 的 D1（时间锚点与状态登记）、D3（强度用词） |
| 改稿时按问题类型查检查动作 | [principles.md](principles.md)（7 条，各绑一个正面例和一个判断问题） |

## 状态

[INDEX.tsv](INDEX.tsv) 的 `status` 列：

- `verified`：所选片段与组织做法已核对，可作**局部正例**；不是整篇质量背书。
- `boundary`：局部可学，但整条带着未解决的证据、口径或读取问题，只在明确限制下介绍其可学处。
- `candidate`：尚未定位到教学分析。

`verification` 是另一回事，只说明记录与页面是否一致（`confirmed` / `partly_confirmed`），不改变上面的分层。`layer` 指出该条出现在哪个分析文件，`unassigned` 表示尚未归入。

## 维护

范文分析是**可维护笔记，不是只读基线**：发现错误就地改，实质改动记日期与依据（如 `2026-09-21 更正：…`）。

本批研究材料（`candidates.md`、`sources.tsv`、复核 JSON）在 `/tmp/docs-exemplars-20260921/`，是临时路径，随时可能被清理。库里只留结论与链接；**每条的实际阅读范围写在该条目里**，不必回 `/tmp` 才知道看过哪里。

## 许可

摘录仅用于内部写作参考，长度受控。各来源的再分发许可与署名要求本批次未逐个核验（KEP、RFC、Python 文档、期刊论文、厂商博客、公众号条款各异），对外引用或再分发前按来源确认并署名。
