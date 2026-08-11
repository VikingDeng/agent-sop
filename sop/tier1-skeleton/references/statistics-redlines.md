# AI 实验统计反模式红线

> **版本**: v2
> **canonical policy**: [`../statistics-oracle.md`](../statistics-oracle.md)

本 reference 只列出会让统计 claim 失真的禁止性模式，不规定万能检验、固定 seed 数、固定报告“三件套”或机械检查顺序。是否需要 inferential gate、需要哪种 uncertainty/decision quantity，以及如何处理 pairing、hierarchy、selection 和 failure，均由 canonical statistics Oracle 根据实际 claim 与数据生成过程决定。

红线不是关键词零容忍：`dropna`、bootstrap、p value、正态性诊断或某个模型名称本身不构成失败。只有它们在实际数据流中造成下列语义错误时才阻断对应 claim。

## R1 · 错认独立 replication unit / pseudo-replication 【REVIEW】【可部分 SCAN】

- **模式**：把 CSV 行数、同一 checkpoint 的重复 decoding、同一 item 的多次 judge call、同一 task 下多个 episode，或同一 seed 派生的多个指标当成独立重复。
- **为什么阻断**：有效 N 被人为放大，uncertainty 与泛化范围不再对应数据生成过程。
- **核对**：从 claim 的 target population 反推独立抽样/随机化单位；扫描报告 N 与 unique seed/task/item/checkpoint/judge/block ID 是否混用，但最终判断必须结合设计。

## R2 · 破坏 pairing、nesting 或 crossing 【REVIEW】

- **模式**：同一 task/item/seed/block 上的方法比较被当作两组独立样本；或 seed、task、model、judge 等层级/交叉相关性被扁平化后直接计算 uncertainty。
- **为什么阻断**：丢失配对会浪费或扭曲信息；忽略 cluster/crossed dependence 会低估或误估 uncertainty。
- **核对**：配对键、cluster ID、聚合权重和分析层级能否从 raw run IDs 重建；headline contrast 是否在与 estimand 相同的单位上计算。

## R3 · outcome-driven 选择仍冒充 confirmatory 【REVIEW】【可部分 SCAN】

- **模式**：看见结果后才选择 metric、baseline、subgroup、checkpoint、方向、排除规则、estimand 或分析方法，却把该结果写成预设确认性结论或补时间戳“追认”。
- **为什么阻断**：选择过程已使用同一 outcome，名义 uncertainty/error rate 不再具有原解释。
- **核对**：冻结方案、结果可见时间、代码/配置版本与选择记录；post-hoc 结果应标为 exploratory，并由未参与选择的 fresh evidence 支持后续 confirmatory claim。

## R4 · 反复窥视、可选停止或扩样未进入设计 【REVIEW】

- **模式**：每增加 seed/task/run 就查看效果，达到有利阈值便停；不利时继续，最终仍按一次固定样本分析解释。
- **为什么阻断**：停止规则与 observed data 相关，固定预算下的 nominal inference 不再有效。
- **核对**：最大预算、interim looks、kill criteria 和继续/停止依据是否预先冻结，或是否使用与该过程匹配的 sequential/anytime 设计或 fresh confirmation。资源安全停止可以执行，但其统计影响必须披露。

## R5 · 隐藏 multiplicity 或选择 family 【REVIEW】【可部分 SCAN】

- **模式**：在多 baseline、metric、dataset、subgroup、checkpoint、prompt 或 variant 中筛出有利结果，只把最终一项算作“唯一比较”；或对正式 claim family 不作任何适当控制/层级解释。
- **为什么阻断**：实际搜索空间被隐去，错误率或 posterior interpretation 与声称不匹配。
- **核对**：从生成/选择代码和完整结果表重建实际 family。不是所有展示数字都必须机械校正；但 formal claims 及 outcome-driven selection 不能被排除在 family 之外。

## R6 · 静默删除或填补 missing/failure/timeout 【SCAN】【REVIEW】

- **模式**：`dropna`、`nanmean`、`fillna(0)`、complete-case filter 或成功样本过滤改变了分析集，却不报告规则、数量、原因和对 estimand 的影响；crash、OOM、timeout、abstain 被从分母或 run view 删除。
- **为什么阻断**：结果可能只描述“方法成功时”的选择子集，却被写成方法总体表现；任意填 0 同样可能改变原 outcome 语义。
- **核对**：输入/保留/失败数量闭合，基础设施 invalid 与方法 failure 分开；若 missingness/censoring 会改变结论，使用与 claim 匹配的 sensitivity/bounds 或保持 `NOT_ESTABLISHED`。

## R7 · ineligible evidence 污染正式估计或修改 raw run 【SCAN】【REVIEW】

- **模式**：smoke、synthetic、mock/stub、runtime fallback 或 `paper_eligible=false` run 进入 authoritative estimate；修复分析后覆盖旧 raw result、回填旧 run 或把 eligibility 改成 true。
- **为什么阻断**：统计处理不能修复实验语义、method fidelity 或 evidence class，也不能追认历史证据。
- **核对**：final table 的每个数字可回到符合冻结 protocol 的 eligible run IDs；失败/invalid/timeout 正式尝试保留为状态、计数或适用的 sensitivity 输入，而不是从事实层消失。

## R8 · 把 statistical signal 写成 practical value，或把无信号写成等效 【REVIEW】

- **模式**：只凭很小的 p value 声称“重要提升”；把 non-significant 写成“没有差异/等效”；没有预声明 scientific margin 却声称 non-inferior/equivalent。
- **为什么阻断**：statistical 与 practical claim 回答不同问题，低 precision 也可能造成 non-significance。
- **核对**：报告 primary effect 的尺度和匹配 uncertainty；practical/equivalence/non-inferiority verdict 使用有领域含义、预先声明的 margin。p value 仅在 claim 与冻结方案需要时出现，不是所有报告的固定组成。

## R9 · 用 CI overlap 或“两种检验一致”替代正确设计 【REVIEW】

- **模式**：以两个边际 CI 是否重叠直接判定方法差异；或看到两个库/检验都给出同方向、同“显著性”，便认定 estimand、独立性、配对和选择过程正确。
- **为什么阻断**：边际区间没有直接表达目标 contrast；多个实现可能共享同一错误聚合、错误 replication unit 或错误输入表。
- **核对**：直接分析预声明 contrast 及其匹配 uncertainty/decision rule；独立 Oracle 必须独立于待验证错误，并先审查数据生成过程和 estimand。复算不一致必须调查，不能挑有利结果。

## R10 · 机械诊断后自动换检验 / method shopping 【SCAN】【REVIEW】

- **模式**：运行正态性或方差检验后自动在参数/非参数方法间切换；主分析失败或不显著后轮换 test、tail、transform、missing policy 或样本子集，直到得到有利输出。
- **为什么阻断**：这种数据依赖的分析选择本身需要进入 inferential design；“非参数”也不会自动修复 dependence、错误 estimand、低 cluster 数或 selection bias。
- **核对**：分析方法由 estimand、设计和可信 failure mode 决定；预声明且仍回答同一 estimand 的路径可执行，否则标为 exploratory 或通过 fresh protocol 重新确认。不得写自动 runtime fallback code。

## R11 · 用固定 seed 数或原始行数代替证据精度 【REVIEW】

- **模式**：规定所有研究只要达到某个 `{N_SEEDS}` 就足够，或因表中行数很大便声称 power/稳定性充足；单 seed 也无条件声称跨随机性稳定。
- **为什么阻断**：所需信息取决于 claim、独立单位、变异来源、effect scale 和目标 precision；seed 数不能替代 task/judge/generalization evidence。
- **核对**：报告各 relevant level 的有效 N 与未覆盖的变异来源。证据不足时限定 claim 或保持 `NOT_ESTABLISHED`，不补伪重复。

## R12 · headline number 无法回到 immutable evidence 【SCAN】【REVIEW】

- **模式**：最终数值来自手填表格、截图读数、不可复现 notebook 状态或已被覆盖的派生文件；报告没有 run IDs、分析版本或状态计数。
- **为什么阻断**：无法区分数据、选择、聚合或排版错误，也无法复核 claim 使用了哪些 evidence。
- **核对**：从 immutable raw records 通过版本化分析确定性生成 report/final table；分析修复生成新 derived artifact 并保留旧版本，不反向修改 raw evidence。

## 使用边界

- `diagnostic`、`code_readiness`、默认不 eligible 的 exploratory work 和有限集合描述，不因缺少 confirmatory artifact 自动失败；红线只阻断它们无权支持的正式 inferential claim。
- 扫描器只能发现候选数据流或措辞，不能仅凭关键词判定统计错误。最终 gate 必须说明具体 claim、错误路径与受影响结论。
- 本清单非穷举。新问题先判断是否真正改变 estimand、error/uncertainty interpretation、evidence eligibility 或 claim 范围；若没有，不新增门禁。
