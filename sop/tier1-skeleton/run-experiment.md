# SOP-run-experiment: 运行一次可信实验

- **层级**: tier1-skeleton
- **落实纪律**: P1(明确 claim) P2(可信 oracle) P3(预算与真实性边界) P4(可复现记录)
- **绑定骨架**: research
- **通用性档位**: U2
- **版本**: v5

## 触发条件

需要运行会用于科研判断、汇报或后续扩容的实验时。

## 前置条件

- 本轮 claim、支持/否定条件及不得声称的结论已写清；
- 已按 `→ tier1-skeleton/research-execution-grill.md` 选择与 proposal 匹配的 oracle、主要 failure modes 和 scale criteria；
- 环境、代码、数据和配置身份足以重现；
- 有有限预算或明确的低成本探索范围；
- 涉及隐私、人类标签、凭据、生产资源、不可逆采集或显著扩容时，已经获得对应授权。

普通低成本 dry run、fixture、plumbing 检查和不产生科学 claim 的诊断不要求正式实验 gate。

如果项目显式选择 signed v3 strict profile，则当前动作还必须通过该 profile 的 exact authorization；否则不得把 v3 artifact 当作默认前置条件。

## 依赖 SOP

→ tier0-core/lock-env.md

→ tier0-core/build-oracle.md

→ tier0-core/reproduce-result.md

→ tier1-skeleton/statistics-oracle.md（需要统计性 claim 时）

→ tier1-skeleton/research-execution-grill.md

## 步骤

1. 记录本轮问题、配置身份、代码版本、数据切分、seed、预算和 kill criteria。允许复用缓存做探索，但正式上报结果必须说明缓存与复现条件；当缓存可能改变结论时运行干净重跑。
2. 先运行最小有信息量的检查，确认实验 plumbing、metric、资源估计和主要 failure mode。根据结果可自主修复或调整实现；若改变 claim、success criterion、正式 split 或预算边界，显式记录并在必要时进入 HUMAN gate。
3. 用与 claim 匹配的 oracle 判定输出。correctness 不通过时，该 run 不支持科学结论，但可保留为诊断证据。
4. 指标 NaN、维度错误、缺数据或 parser 失败不得用占位值掩盖。修复后重新运行受影响部分。
5. 根据随机性和 claim 选择 seed/repetition 数；不要机械要求所有诊断 run 多 seed，也不要用单点结果声称稳定优势。
6. 记录原始结果、配置、代码/数据身份、环境和执行日志。区分 exploratory、pilot 与 confirmatory result。
7. 持续检查累计资源；触及已声明预算即停止后续 run。扩大预算、进入物质性 scale 或改用生产资源需要新的明确依据与授权。
8. 对预设 kill criterion 如实处理。负结果是科研结果；记录其证据和下一步决定，不删除、不 cherry-pick，也不在未说明的情况下改目标继续跑。

## 完成判定

- 实验真实运行，关键输出可由记录复核；
- oracle 能支持实际 claim，已知共享错误路径被检查或披露；
- 数据切分、baseline、调参和预算公平性与 claim 相符；
- 重复次数与随机性处理足以支持所用措辞；
- 结果、配置、身份、探索/确认标签和限制已归档；
- strict v3 仅在项目显式选择时要求 validator exit `0`。

## 门禁

- 伪造/复用旧结果冒充本轮运行；
- 未披露 holdout 泄漏、outcome-driven metric/split 漂移或 cherry-picking；
- 指标/正确性失败却仍声称通过；
- 超预算、越过隐私/凭据/生产/不可逆边界；
- project-selected strict authorization 未通过却执行其保护动作。

模型、工具、某个 reviewer 或推荐 artifact 不可用时，优先使用等价证据或缩小 claim，而不是把 operational failure 写成 scientific no-go。

## 失败处理

运行或 correctness 失败时保留诊断证据、修复并重跑受影响部分；不得冒用旧结果。预算或授权边界触发时停止受保护动作并报告现状。若 oracle 不足以支持原 claim，补强 oracle 或诚实缩小本轮结论，而不是填充占位结果或把 operational failure 当成科学结论。

## 产物

一条可复核实验记录：问题与 claim、配置/代码/数据身份、预算、运行证据、oracle 结论、指标与不确定性、探索/确认标签、支持/证伪结论、限制和下一步 scale 决定。
