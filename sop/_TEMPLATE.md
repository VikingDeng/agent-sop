# SOP-<ID>: <名字>

- **层级**: tier0-core | tier1-skeleton | tier2-activity
- **落实纪律**: P1 / P2 / P3 / P4 中的一条或多条(必填,对不上则不得入库,见 ../PRINCIPLES.md)
- **绑定骨架**: research | competition | development | 无(tier0/tier2 常为"无")
- **通用性档位**: U0 普适 | U1 语言/生态相关 | U2 项目相关(必填,见 _METHODOLOGY.md §3)
- **版本**: v1 (advance on material edits)

## 触发条件

什么情况下用这条 SOP。需标注触发方式:
- `[显式]` 人主动调用本 SOP;
- `[信号自触发]` agent 在某可判定信号出现时自动进入(须写明信号,如"用户确认理解/切换话题/关键任务完成")。

标注触发方式提升 A3(步骤可执行可判定):不写清是人调还是自触发,agent 无法判断何时进入本 SOP。

## 前置条件

需要的输入 / 环境 / 状态。

## 依赖 SOP

本 SOP 调用的其他 SOP(可组合,不复制)。例:`→ tier0-core/commit-and-pr.md`。无则写"无"。

## 步骤

1. …(每步可执行、可判定)
2. …

## 门禁

挂哪些 enforcement:[AUTO] / [SCAN] / [REVIEW] / [RUNTIME] / [HUMAN]。

## 完成判定

可验证的 done 标准(客观、可自查)。

## 失败处理

遵守 P3:失败即报,不静默降级。允许显式且质量等价的 fallback，但必须记录触发原因、用未改变的验收标准重新验证；改变 public behavior、research claim、隐私/数据边界、不可逆状态或 material/unbounded cost 时写明 HUMAN gate/re-contract。

## 产物

产出什么文件 / 状态 / 记录。
