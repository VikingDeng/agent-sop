# SOP-research-execution-grill: 自适应科研执行拷问

- **层级**: tier1-skeleton
- **落实纪律**: P1(冻结 claim 与验收) P2(证据真实性) P3(风险自适应) P4(可复现交付)
- **绑定骨架**: research
- **通用性档位**: U2
- **版本**: v5（adaptive default；signed v3 为可选 strict profile）

## 目标

在不替换已批准 idea 的前提下，找出最可能让实现、实验或结论失效的问题，并把 proposal 转化为可执行、可证伪、可复现的工作。Grill 约束科研结论质量，不规定所有研究必须走同一组 gate。

## 触发条件

- 已批准 proposal 即将实现、运行首个有科学意义的实验或物质性扩容；
- 用户要求 grill、red-team、实验就绪检查或 scale 检查。

## 前置条件

- proposal 方向已由用户提供或选择；
- 能识别本轮准备执行的 claim、实验或资源边界；
- 可访问足以开始风险分析的 proposal 与项目上下文。

## 依赖 SOP

→ tier0-core/build-oracle.md（需要独立 correctness/measurement oracle 时）

→ tier0-core/no-fallback-review.md（检查隐藏失败与证据降级时）

## 默认自由度

Agent 根据 proposal 类型、风险和现有证据选择检查与执行顺序。允许合并、跳过、重排或新增阶段；允许在实现中发现新证据后修改计划。以下名称只是常见能力，而不是固定状态机：

- code/readiness；
- data or evidence acquisition；
- oracle/measurement validation；
- pilot/Phase 0；
- scale/confirmation。

没有人工标签的研究不需要 `human_oracle`；不依赖静态数据的研究不需要 registry 或 blinded bundle；理论、系统、simulation、benchmark 和 human-study proposal 应使用各自可信的 oracle。任何缺失都只在它与当前 claim 有因果关系时阻断。

## 必须先回答的问题

形成一份简洁 execution contract：

1. proposal 的核心 claim 和本轮要验证的最小问题是什么？
2. 什么结果支持、削弱或否定它？哪些结论本轮无权声称？
3. 最危险的混淆、泄漏、实现错误、不公平 baseline 或测量错误是什么？
4. 哪个 oracle 能独立区分成功与失败？它可能与实现共享什么错误？
5. 最小有信息量的 pilot 是什么？什么条件才值得扩大？
6. 当前预算、kill criteria、随机性、数据边界和复现要求是什么？

答案可以写入现有 handoff、实验计划或 proposal companion；不强制创建特定文件名或 schema。

## 步骤

### 1. 选择与 claim 匹配的检查

- 数据型研究：检查来源、许可、切分、污染、泄漏、缺失和预处理身份；
- 人工 oracle：检查 rubric、盲法、一致性、abstain/uncertain、冲突处理和不可由 Agent 代填的身份；
- benchmark/simulation：检查实现等价性、seed、预算公平、调参边界和 hidden adaptation；
- 系统研究：检查 workload 代表性、测量扰动、资源隔离、重复运行和尾延迟；
- 理论/形式化工作：检查假设、边界条件、反例搜索、proof/checker 独立性；
- 生成式或 model-judge 研究：检查 judge 偏差、提示泄漏、循环自评和人工抽查。

只执行能改变决策或提升最终可信度的检查。不要为了满足模板制造无关 artifact。

### 2. 让 gate 对应真实边界

普通可逆的代码、静态数据获取、fixture、dry run 和不产生科学 claim 的诊断可以自主进行。只有跨越下列边界才需要明确 gate：

- 使用人类专属标签、隐私数据、凭据或外部授权；
- 从诊断进入会影响正式结论的数据收集；
- 根据已看见的 outcome 改动预注册的 metric、split、baseline 或 success criterion；
- 从小规模 pilot 进入显著算力、付费、生产资源或不可逆采集；
- 对外发布数据、模型、论文结论或影响第三方的系统。

Gate 的证据和 reviewer 数量按失败代价决定。低风险边界可由真实命令和清晰记录满足；高风险边界可要求独立 review、签名、外部 authority 或确定性 validator。

### 3. 自主探索并持续收敛

Agent 可以自由选择实现顺序、实验 plumbing、诊断方式、subagent 分工和修复轮次。初始计划不是不可修改的承诺；只要核心 claim、数据使用、success criterion 和预算没有被偷偷改变，就可以根据新证据调整战术。

Reviewer 只能用与当前 claim 相关、可复现的失败路径阻断。新增建议若不影响本轮结论，进入 backlog，不移动当前验收线。相同失败类别重复且没有新证据时，停止局部补丁并重做设计或缩小 claim，不生成无界 successor gate。

### 4. 运行最小有信息量的实验

先运行能验证 plumbing、oracle、资源估计和主要 failure mode 的最小实验。Pilot 可以产生科学信息；必须清楚标记其探索性以及哪些选择随后被冻结。只有满足预先声明或有证据更新的 scale criteria 才扩大。失败 pilot 是结果，不是流程违规。

### 5. 验收最终质量

完成时应能回答：

- 代码和实验是否真实运行，输出能否重现；
- baseline、预算和调参是否公平；
- 数据、labels、metrics 与最终 claim 是否对应；
- 主要替代解释是否被测试或诚实保留；
- 结果是否区分探索性、确认性和未验证结论；
- 下一步扩大是否由证据而非流程惯性驱动。

## 门禁

- 伪造、代填或无法追溯的关键数据、人工判断、review、签名或运行结果；
- 未披露的数据泄漏、benchmark contamination、outcome-driven cherry-picking 或 success criterion 漂移；
- oracle 已知不能区分实现错误与科学结论，却仍据此声称通过；
- 超出用户授权预算、隐私、凭据、发布、不可逆采集或生产边界；
- proposal 的核心 claim/语义必须改变但尚未获得用户决定。

工具、模型、推荐 artifact、固定 reviewer 或某个 stage 不可用，本身不是科研 no-go。选择等价证据或降级为更窄、诚实的 claim；只有无法保持验收质量时才阻断。

## 可选 strict signed-v3 profile

只有项目指令、外部审计、多人 authority 分离或高价值不可逆边界明确要求时，才启用 `research-execution-grill-v3` 签名事件账本。该 profile 使用固定 action order、external trust pin、signed review cycle、two-phase authorization 和确定性 validator；其协议见 [references/research-execution-grill-artifact.md](references/research-execution-grill-artifact.md)。

选择 strict profile 后必须完整执行，不能把其中一部分签名或 hash 当作授权。历史 v1/v2 仍是 audit-only。strict profile 的 operational failure 只阻断受保护动作，不应污染 proposal 的科学状态或禁止其他安全工作。

## 完成判定

- execution contract 足以指导下一步真实工作；
- 与 claim 相关的主要 failure modes、oracle、预算和 scale criteria 已得到证据支持或诚实标为未决；
- 不相关的 stage/gate 没有被机械加入；
- 下一步可以执行，或阻断点确实属于硬边界而不是缺少流程 artifact。

## 失败处理

发现设计或 oracle 缺陷时允许重构计划、缩小本轮 claim 或补充最小证据；不得替换已批准 idea。模型、工具或 reviewer 不可用时选择等价路径。只有无法保持证据真实性、需要未授权的人类/资源决定或核心 claim 必须改变时，才停止相关执行并明确所需决定。

## 产物

- 与 claim 匹配的简洁 execution contract；
- 实际运行证据、关键决策和变更理由；
- pilot/正式实验结果及其探索性或确认性标签；
- 与风险相称的 review/authorization；
- 剩余替代解释、限制、scale 决定和复现入口。
