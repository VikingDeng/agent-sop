# SOP-run-experiment: 运行一次可信实验

- **层级**: tier1-skeleton
- **落实纪律**: P1(明确 claim) P2(可信 oracle) P3(预算与真实性边界) P4(可复现记录)
- **绑定骨架**: research
- **通用性档位**: U2
- **版本**: v7

## 触发条件

需要运行会用于科研判断、汇报或后续扩容的实验时。

## 前置条件

- 本轮 claim、支持/否定条件及不得声称的结论已写清；
- 原 claim、primary estimand、method 语义、baseline、数据/split、分析方法和正式预算已冻结，或当前 run 明确仅为不产生科学 claim 的诊断；
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

→ tier2-activity/ops-remote-compute.md（需要远程算力时）

## 步骤

1. 记录本轮唯一问题、evidence class（`diagnostic|code_readiness|exploratory|confirmatory`）、`paper_eligible`、配置身份、代码版本、数据切分、seed、预算和 kill criteria。允许复用缓存做探索，但正式上报结果必须说明缓存与复现条件；当缓存可能改变结论时运行干净重跑。
2. 先运行最便宜的 discriminating check。synthetic、mock/stub、plumbing smoke 和 code-readiness fixture 必须 `paper_eligible=false`，只验证 wiring、schema、provenance、异常路径、成本遥测、输出格式或实现 invariant；不得调参、选择数据、改变 hypothesis/estimand，也不得触发 scientific GO。
3. 科学 producer/evaluator 代码 fail fast：NaN、维度错误、缺数据、parser/oracle 失败或 method component/model/backend/device 不可用时非零退出。禁止用默认值、旧结果、proxy metric、跳样本、自动 CPU/backend/model/dataset/method fallback 继续本 run；不要保留 speculative catch-and-continue 或“不可用就换一个”的 runtime fallback code，除非该 resilience 行为本身属于冻结方法并有独立验收。
4. 失败后可自主修复同一 method 的实现或准备一个显式新配置，但必须使用新 run ID 重新执行原 acceptance；不得修改旧 raw run。若变更 claim、primary estimand、method 语义、success criterion、baseline、正式 split、分析方法或正式预算，进入 HUMAN re-contract，而不是在代码中兼容两套语义。
5. 用与 claim 匹配的 oracle 判定输出。correctness/method fidelity 不通过时，该 run 不支持科学结论，但保留原始失败状态；后续单元测试或 checker 修复不能追认它。
6. 根据随机性和 claim 选择 seed/repetition 数；不要机械要求所有诊断 run 多 seed，也不要用单点结果声称稳定优势。
7. 记录 immutable raw result、配置、代码/数据身份、环境、执行日志、失败/timeout 和实际 compute。按 [research-evidence-presentation.md](references/research-evidence-presentation.md) 从 raw runs 生成中间 run/data view；失败、invalid 和负结果不得从视图消失。
8. 只有冻结 protocol、真实任务/数据、有效 oracle、无 runtime fallback 且 eligibility 可复核的 run 才能 `paper_eligible=true`。authoritative final table 的指标与 effect estimate 只从 eligible run records 确定性生成；冻结 protocol 下 invalid/timeout 的正式尝试保留为状态/计数，不手填数值、不复制旧论文数、不纳入 smoke/code-readiness。
9. 持续检查累计资源；触及已声明预算即停止后续 run。扩大预算、进入物质性 scale、换远程资源 profile 或改用生产资源需要新的明确依据与授权。
10. 对预设 kill criterion 如实处理。负结果是科研结果；记录其证据和下一步决定，不删除、不 cherry-pick，也不以较弱 claim 或替代方法宣布原任务成功。

## 完成判定

- 实验真实运行，关键输出可由记录复核；
- oracle 能支持实际 claim，已知共享错误路径被检查或披露；
- 数据切分、baseline、调参和预算公平性与 claim 相符；
- 重复次数与随机性处理足以支持所用措辞；
- 结果、配置、身份、evidence class、`paper_eligible`、失败状态和限制已归档；
- 中间视图完整呈现 eligible 与 failed/invalid runs，final table 只消费可追溯 eligible evidence；
- 原 claim verdict 没有被更弱 claim、proxy metric 或简化方法替换；
- strict v3 仅在项目显式选择时要求 validator exit `0`。

## 门禁

- 伪造/复用旧结果冒充本轮运行；
- 未披露 holdout 泄漏、outcome-driven metric/split 漂移或 cherry-picking；
- 指标/正确性失败却仍声称通过；
- runtime fallback、mock/stub/synthetic 或 smoke/code-readiness 结果进入 scientific claim、GO 或 final table；
- 自动改变 method/model/backend/device/data/metric/analysis 继续产出结果，或用弱 claim 替换原 contract；
- 超预算、越过隐私/凭据/生产/不可逆边界；
- project-selected strict authorization 未通过却执行其保护动作。

模型、工具、某个 reviewer 或推荐 artifact 不可用时，相关 run 保持 `BLOCKED`/`NOT_ESTABLISHED`，而不是把 operational failure 写成 scientific no-go 或自动切换路径。保持原 contract 的替代实现只能通过显式新配置和 fresh run 验收。

## 失败处理

运行或 correctness 失败时保留 immutable 失败证据，修复未来路径并用新 run 重跑；不得冒用、覆盖或追认旧结果。预算或授权边界触发时停止受保护动作并报告现状。若 oracle 不足以支持原 claim，补强 oracle或将原 verdict 保持为 `NOT_ESTABLISHED`；次级弱发现可以单列，但不能替换原结论或完成标准。

## 产物

一条可复核实验记录：问题与原 claim、配置/代码/数据身份、预算、运行证据、oracle 结论、指标与不确定性、evidence class、`paper_eligible`、原 claim verdict、限制和下一步 scale 决定；以及从 raw records 生成的中间 run/data view 与适用时的 authoritative final table。
